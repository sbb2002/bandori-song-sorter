"""
YouTube new-song detector / proposer for bandori-song-sorter.

Free, no API key, only stdlib + the project's PyYAML + the `gh` CLI (already on
GitHub's runner). Runs daily from .github/workflows/rss.yml.

Idea
----
Each band's official audio lives on its YouTube Music auto-generated
"<Band> - Topic" channel. Those channels contain *songs only* (no news,
trailers or livestreams) and are band-specific, so polling each band's Topic
RSS feed gives us both automatic band assignment *and* song-only filtering for
free.

Design (see docs/HANDOFF.md #1 for the full rationale)
-----------------------------------------------------
* Idempotent recompute — no persisted "seen" ledger. A feed entry is a *new
  candidate* unless its video id is already in src/content/songs/*.yaml (known_ids) or
  already has an `rss/<id>` PR (open/closed/merged). Merge puts it in the yaml;
  closing the PR is a permanent reject (its branch stays, so we never re-propose).
* One song = one PR, branch `rss/<video_id>`. Human merge = accept (TP),
  human close = reject (FP). GitHub PR state *is* the ledger.
* yaml is edited surgically (additive text insertion only — never re-serialized)
  so existing quoting/formatting of 560 songs is untouched.
* Every decision is logged to src/tools/collect/rss_events.jsonl (git-tracked, append-only,
  deduped per (video_id, decision)). `--report` joins it with live PR state for
  precision = TP/(TP+FP); `--audit` lists heuristic drops (where FN can hide).
* Format-change watch is parsing-layer only: fetch failure / XML error / zero
  valid entries. Multi-band → hard alarm (gh issue); single band → soft, escalates
  if it persists. Zero *staged* songs after filters is normal and never alarms.

Modes
-----
  python src/tools/collect/youtube_rss.py            preview (= --dry; safe, no writes)
  python src/tools/collect/youtube_rss.py --dry      detect & preview insertions, no writes
  python src/tools/collect/youtube_rss.py --propose  CI: open per-song PRs, log, push log (real)
  python src/tools/collect/youtube_rss.py --report    precision dashboard (events + PR state)
  python src/tools/collect/youtube_rss.py --audit     heuristic drops only (FN review)
  python src/tools/collect/youtube_rss.py --show      dump latest feed entries per band
"""

import sys
import os
import re
import json
import time
import datetime
import subprocess
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install pyyaml")
    sys.exit(1)

# Japanese titles must print on any console (Windows cp949/cp932 etc.).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


ROOT = Path(__file__).resolve().parents[3]   # src/tools/collect/<file> → repo root
DATA_DIR = ROOT / "src" / "content" / "songs"
EVENTS_LOG = ROOT / "src" / "tools" / "collect" / "rss_events.jsonl"

FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
WATCH_PAGE = "https://www.youtube.com/watch?v={}"
WATCH_SHORT = "https://youtu.be/{}"
FALLBACK_IMG = "assets/icons/_fallback.png"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# band (as used in src/content/songs/*.yaml `band:`) -> "<Band> - Topic" channel id.
# data/etc.yaml (band: various_artists) bundles multiple artists with no single
# Topic channel, so it is intentionally not auto-monitored.
BAND_CHANNELS = {
    "afterglow":         "UCs9VJt7wfDJFwyAPWSBTIRg",
    "ave_mujica":        "UCcUQTshxx-7gwzKa8fZjn6A",
    "hello_happy_world": "UCC3jTZ-SwZdILF_8P521wwQ",
    "ikka_dumb_rock":    "UCL1AOkcNmJEsSXbbjEgUi7A",
    "millsage":          "UCLAhZE3QHRPTicYKG0iD5Dw",
    "morfonica":         "UC_eLLiu3qWOWkbipDQeNCsw",
    "mugendai_mutype":   "UCeXzCxZsDcaF5xI68fK5owA",
    "mygo":              "UCnLzMFzqZHQBFXji4nZXk_w",
    "pastel_palettes":   "UCWy887F5DcK6B0AwON13rWg",
    "poppin_party":      "UC-hMXkTAR9ygeuUc415Ly0w",
    "raise_a_suilen":    "UC6HBeGmc_k9pjjpkbLBrZKA",
    "roselia":           "UCJzgTYxZKiK-e2_0Y5hPEAg",
}

# We only catalogue full original versions and the bands' cover songs.
# Anything variant_tag classifies as a length-reduced / non-studio version is
# dropped before it can reach a PR.
KEEP_VARIANTS = {"", "cover"}

# Length-based 2nd cut: a candidate whose watch page reports a duration shorter
# than this is treated as an unlabeled abridged version (TV Size ~89s, Short
# ~60-90s) and dropped. Unknown length -> never dropped (fail open, FN-safe).
# Borderline lengths still go through but the human sees the length in the PR.
MIN_LENGTH_S = 90

ISSUE_TITLE_PREFIX = "🔔 RSS 포맷 변경 의심"


# ──────────────────────────────────────────────
# Title helpers
# ──────────────────────────────────────────────

def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def video_id(url: str):
    """Extract the 11-char YouTube id from a youtu.be / watch?v= url."""
    if not url:
        return None
    m = re.search(r"(?:youtu\.be/|v=|/shorts/)([\w-]{11})", url)
    return m.group(1) if m else None


def norm_name(title: str) -> str:
    """Normalize a song title for duplicate detection within a band.

    Folds width/case, drops bracketed qualifiers like (Cover) / (TV Size) and
    all punctuation/whitespace, so 'A Sunset So Bright' and
    'A Sunset So Bright (TV Size)' compare equal.
    """
    s = unicodedata.normalize("NFKC", title or "")
    s = re.sub(r"[\(\[【（].*?[\)\]】）]", "", s)   # remove (…) […] 【…】 （…）
    s = s.casefold()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^\w]", "", s, flags=re.UNICODE)  # keep letters/digits (incl. CJK)
    return s


def variant_tag(title: str) -> str:
    """Classify a title's version. '' means a full original version.

    `live` is matched conservatively (only explicit markers) so titles like
    'Alive' are not misclassified. Anything not in KEEP_VARIANTS is dropped.
    """
    t = unicodedata.normalize("NFKC", title or "").lower()
    if "tv size" in t or "tvsize" in t or "tv-size" in t:
        return "tv_size"
    if "movie ver" in t or "movie size" in t or "anime ver" in t or "anime size" in t or "tv ver" in t:
        return "tv_size"
    if "short ver" in t or "short edit" in t or "short size" in t:
        return "short"
    if "cover" in t:
        return "cover"
    if "the first take" in t:
        return "live"
    if "instrumental" in t or "off vocal" in t or "off-vocal" in t or "カラオケ" in t:
        return "instrumental"
    if "remix" in t or "nightcore" in t or " mix)" in t:
        return "remix"
    if "medley" in t:
        return "medley"
    if "(edit" in t or " - edit" in t or "edit ver" in t:
        return "edit"
    if "(live" in t or "live ver" in t or "【live" in t or " - live" in t:
        return "live"
    return ""


# ──────────────────────────────────────────────
# Network: feed + duration
# ──────────────────────────────────────────────

def fetch_feed(channel_id: str, retries: int = 4):
    """Return (entries, ok). ok=False only after `retries` consecutive failures
    (absorbs transient 503/timeout — alarm policy keys off ok=False)."""
    last = None
    for attempt in range(retries):
        try:
            root = ET.fromstring(http_get(FEED_URL.format(channel_id)))
            entries = []
            for e in root.findall("a:entry", NS):
                vid = e.findtext("yt:videoId", namespaces=NS)
                title = e.findtext("a:title", namespaces=NS) or ""
                published = (e.findtext("a:published", namespaces=NS) or "")[:10]
                if vid:
                    entries.append({"video_id": vid, "title": title, "published": published})
            return entries, True
        except Exception as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    print(f"  [feed error] {channel_id}: {last!r}")
    return [], False


def fetch_length_seconds(vid: str):
    """Scrape the watch page for lengthSeconds. None on any failure (fail open)."""
    try:
        html = http_get(WATCH_PAGE.format(vid))
        m = re.search(r'"lengthSeconds":"(\d+)"', html)
        return int(m.group(1)) if m else None
    except Exception:
        return None


# ──────────────────────────────────────────────
# Existing data
# ──────────────────────────────────────────────

def load_existing():
    """Return (names_by_band, ids_by_band, band_file) from every src/content/songs/*.yaml."""
    names_by_band, ids_by_band, band_file = {}, {}, {}
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".yaml"):
            continue
        path = DATA_DIR / fn
        albums = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for album in albums:
            band = album.get("band", "")
            band_file.setdefault(band, path)
            names = names_by_band.setdefault(band, set())
            ids = ids_by_band.setdefault(band, set())
            for track in (album.get("tracks") or []):
                if track.get("name"):
                    names.add(norm_name(track["name"]))
                vid = video_id(track.get("url"))
                if vid:
                    ids.add(vid)
    return names_by_band, ids_by_band, band_file


# ──────────────────────────────────────────────
# gh CLI
# ──────────────────────────────────────────────

def gh_run(args):
    """Run `gh <args>`; returns CompletedProcess (returncode 127 if gh missing)."""
    try:
        return subprocess.run(["gh"] + args, capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError:
        cp = subprocess.CompletedProcess(args, 127, "", "gh not found")
        return cp


def gh_json(args):
    """Run a `gh ... --json` query. Returns parsed value, or None on any error."""
    p = gh_run(args)
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout or "null")
    except Exception:
        return None


def gh_pr_states():
    """{video_id: STATE} for every rss/<id> PR (OPEN/CLOSED/MERGED).
    Returns ({}, False) when gh is unavailable so callers can warn."""
    data = gh_json(["pr", "list", "--state", "all", "--limit", "500",
                    "--json", "number,headRefName,state"])
    if data is None:
        return {}, False
    states = {}
    for pr in data:
        ref = pr.get("headRefName", "") or ""
        if ref.startswith("rss/"):
            states[ref[4:]] = pr.get("state")
    return states, True


def _run(args, check=True):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed (rc={p.returncode}): {p.stderr.strip()}")
    return p


# ──────────────────────────────────────────────
# Surgical YAML insertion (pure text — additive only)
# ──────────────────────────────────────────────

def yaml_squote(s) -> str:
    """Single-quoted YAML scalar (matches the files' dominant style). Only ' is
    special inside single quotes (-> ''), so every title/date is safely quoted."""
    return "'" + str(s).replace("'", "''") + "'"


def _track_block(track_number, name, url):
    return "\n".join([
        f"    - track_number: {yaml_squote(track_number)}",
        f"      name: {yaml_squote(name)}",
        f"      url: {url}",
    ])


def _album_block(band, numbering, album_title, img_url, track_number, name, url):
    return "\n".join([
        f"- band: {yaml_squote(band)}",
        f"  numbering: {yaml_squote(numbering)}",
        f"  album_title: {yaml_squote(album_title)}",
        f"  img_url: {img_url}",
        f"  tracks:",
        _track_block(track_number, name, url),
    ])


def _unquote(v):
    if v is None:
        return None
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        inner = v[1:-1]
        if v[0] == "'":
            inner = inner.replace("''", "'")
        return inner
    return v


def _block_field(block_lines, key):
    # `band` is on the block's first line as "- band: ...", other keys are at
    # 2-space indent ("  numbering: ..."). Accept both forms.
    pat = re.compile(r"^(?:- |\s{2})" + re.escape(key) + r":\s*(.*)$")
    for ln in block_lines:
        m = pat.match(ln)
        if m:
            return _unquote(m.group(1))
    return None


def insert_track(yaml_text, band, numbering, album_title, img_url,
                 track_number, name, url):
    """Insert one track into <band>'s <numbering> album, additively.

    Returns (new_text, action) with action 'appended' (album existed) or
    'created' (no such album -> new block at EOF). Operates on '\\n' text only;
    the caller restores CRLF if the original used it. Existing lines are never
    rewritten, so the git diff is purely additive.
    """
    name = str(name).replace("\r", " ").replace("\n", " ").strip()
    lines = yaml_text.split("\n")

    starts = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    blocks = []
    for idx, s in enumerate(starts):
        e = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        blocks.append((s, e))

    target = None
    for (s, e) in blocks:
        bl = lines[s:e]
        if _block_field(bl, "band") == band and _block_field(bl, "numbering") == numbering:
            target = (s, e)
            break

    track_lines = _track_block(track_number, name, url).split("\n")

    if target:
        s, e = target
        ip = e                                  # insert after last non-blank line of block
        while ip - 1 >= s and lines[ip - 1].strip() == "":
            ip -= 1
        new_lines = lines[:ip] + track_lines + lines[ip:]
        return "\n".join(new_lines), "appended"

    # No matching album -> create a new block at EOF (one blank-line separator).
    end = len(lines)
    while end - 1 >= 0 and lines[end - 1].strip() == "":
        end -= 1
    block_lines = _album_block(band, numbering, album_title, img_url,
                               track_number, name, url).split("\n")
    new_lines = lines[:end] + [""] + block_lines + [""]
    return "\n".join(new_lines), "created"


def _verify_insertion(new_text, band, vid):
    """Re-parse the edited yaml and confirm the new video id is present under the
    right band. Guards against any insertion that would corrupt the file."""
    try:
        albums = yaml.safe_load(new_text)
    except Exception:
        return False
    if not isinstance(albums, list):
        return False
    for album in albums:
        if album.get("band") != band:
            continue
        for tr in (album.get("tracks") or []):
            if video_id(tr.get("url")) == vid:
                return True
    return False


# ──────────────────────────────────────────────
# Candidate detection (idempotent recompute)
# ──────────────────────────────────────────────

def _drop(band, e, reason, variant=None, length_s=None):
    return {
        "band": band, "video_id": e["video_id"], "name": e["title"],
        "published": e["published"], "decision": "dropped",
        "drop_reason": reason, "variant": variant, "length_s": length_s,
    }


def collect_candidates(existing_pr_ids, scrape_length=True):
    """Returns (candidates, drops, health, band_file).

    candidates: songs to propose. drops: per-entry drop records (for the log).
    health: per-band {ok, entries, valid} for the format watch.
    """
    names_by_band, ids_by_band, band_file = load_existing()
    candidates, drops, health = [], [], {}

    for band, channel_id in BAND_CHANNELS.items():
        entries, ok = fetch_feed(channel_id)
        valid = [e for e in entries if e["video_id"] and e["title"]]
        health[band] = {"ok": ok, "entries": len(entries), "valid": len(valid)}
        if not ok:
            continue

        known_names = names_by_band.get(band, set())
        known_ids = ids_by_band.get(band, set())

        # Collapse duplicate uploads of one song: keep the best per normalized
        # name (full version over cover, then earliest date).
        best = {}
        for e in valid:
            vid, title = e["video_id"], e["title"]
            if vid in known_ids:
                drops.append(_drop(band, e, "known_id"))
                continue
            if vid in existing_pr_ids:
                drops.append(_drop(band, e, "has_pr"))
                continue
            variant = variant_tag(title)
            if variant not in KEEP_VARIANTS:
                drops.append(_drop(band, e, "variant", variant=variant))
                continue
            key = norm_name(title)
            if key in known_names:
                drops.append(_drop(band, e, "known_name", variant=variant))
                continue
            rank = (variant != "", e["published"] or "9999-99-99")
            if key not in best or rank < best[key][0]:
                best[key] = (rank, e, variant)

        for rank, e, variant in best.values():
            length_s = fetch_length_seconds(e["video_id"]) if scrape_length else None
            if length_s is not None and length_s < MIN_LENGTH_S:
                drops.append(_drop(band, e, "length_short", variant=variant, length_s=length_s))
                continue
            candidates.append({
                "band": band, "video_id": e["video_id"], "name": e["title"],
                "published": e["published"], "variant": variant, "length_s": length_s,
                "url": WATCH_PAGE.format(e["video_id"]), "is_cover": variant == "cover",
            })

    # Order: full versions first, then covers; each group oldest -> newest.
    candidates.sort(key=lambda c: (c["is_cover"], c["published"] or "9999-99-99",
                                   c["band"], c["name"]))
    return candidates, drops, health, band_file


# ──────────────────────────────────────────────
# Event log
# ──────────────────────────────────────────────

def load_events():
    if not EVENTS_LOG.exists():
        return []
    recs = []
    for line in EVENTS_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except Exception:
            pass
    return recs


def append_events(records):
    if not records:
        return
    EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_LOG, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────
# PR proposing (CI path)
# ──────────────────────────────────────────────

def _pr_body(cand, action, track_number):
    length = f"{cand['length_s']}s" if cand.get("length_s") else "(unknown)"
    variant = cand["variant"] or "full"
    album = "Covers" if cand["is_cover"] else "New Singles"
    return (
        "자동 감지된 신곡 후보입니다. (1곡 = 1 PR)\n\n"
        "| 필드 | 값 |\n|---|---|\n"
        f"| band | `{cand['band']}` |\n"
        f"| name | {cand['name']} |\n"
        f"| 발매일(track_number) | `{track_number}` |\n"
        f"| variant | `{variant}` |\n"
        f"| 길이 | {length} |\n"
        f"| video_id | `{cand['video_id']}` |\n"
        f"| url | {cand['url']} |\n"
        f"| 삽입 | {action} → `{album}` 앨범 |\n\n"
        "**승인** = 이 PR을 **머지**하면 곡이 데이터에 반영됩니다. "
        "(라이브 반영은 `python build.py` → index.html 커밋이 별도 게이트)\n"
        "**거절** = 이 PR을 **닫으면** 끝입니다. 봇이 다시 제안하지 않습니다.\n\n"
        f"<!-- rss-bot {cand['video_id']} -->"
    )


def open_pr(cand, band_file):
    """Create a fresh rss/<id> branch off origin/main with the track inserted,
    push it and open a PR. Returns the branch name, or None on a handled failure."""
    vid, band = cand["video_id"], cand["band"]
    branch = f"rss/{vid}"
    path = band_file.get(band) or (DATA_DIR / f"{band}.yaml")
    rel = path.relative_to(ROOT).as_posix()
    numbering = "Cover" if cand["is_cover"] else "Single"
    album_title = "Covers" if cand["is_cover"] else "New Singles"
    track_number = cand["published"] or datetime.date.today().isoformat()
    url = WATCH_SHORT.format(vid)

    _run(["git", "checkout", "-B", branch, "origin/main"])
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    norm = raw.decode("utf-8").replace("\r\n", "\n")
    new_norm, action = insert_track(norm, band, numbering, album_title,
                                    FALLBACK_IMG, track_number, cand["name"], url)
    if not _verify_insertion(new_norm, band, vid):
        _run(["git", "checkout", "main"], check=False)
        print(f"  [SKIP] insertion verify failed: {vid} {cand['name']!r}")
        return None
    out = new_norm.replace("\n", "\r\n") if crlf else new_norm
    path.write_bytes(out.encode("utf-8"))

    _run(["git", "add", rel])
    _run(["git", "commit", "-m", f"data({band}): add {cand['name']} [rss]"])
    _run(["git", "push", "-f", "origin", branch])

    p = gh_run(["pr", "create", "--base", "main", "--head", branch,
                "--title", f"🎵 {band} · {cand['name']}",
                "--body", _pr_body(cand, action, track_number)])
    if p.returncode != 0 and "already exists" not in (p.stderr or ""):
        print(f"  [pr create warn] {vid}: {p.stderr.strip()}")
    _run(["git", "checkout", "main"])
    return branch


def commit_log():
    """Best-effort: persist the event log back to main (tools/ only, [skip ci])."""
    try:
        _run(["git", "checkout", "main"], check=False)
        _run(["git", "add", EVENTS_LOG.relative_to(ROOT).as_posix()], check=False)
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
            return
        _run(["git", "commit", "-m", "chore(rss): update event log [skip ci]"], check=False)
        _run(["git", "push", "origin", "HEAD:main"], check=False)
    except Exception as exc:
        print(f"  [log commit warn] {exc!r}")


# ──────────────────────────────────────────────
# Format-change watch
# ──────────────────────────────────────────────

def health_issue_open():
    data = gh_json(["issue", "list", "--state", "open", "--search", ISSUE_TITLE_PREFIX,
                    "--json", "number,title"])
    if not data:
        return False
    return any(ISSUE_TITLE_PREFIX in (i.get("title") or "") for i in data)


def open_health_issue(anomalies, health):
    if health_issue_open():
        print("  [health] 동일 이슈가 이미 열려 있음 → 재생성 안 함")
        return
    rows = []
    for b in anomalies:
        why = "fetch 실패(연속 retry>3)" if not health[b]["ok"] else f"유효 entry 0개 (수신 {health[b]['entries']})"
        rows.append(f"- `{b}`: {why}")
    body = (
        "RSS **파싱 레이어** 이상이 감지되었습니다 (파서/채널 점검 필요).\n\n"
        + "\n".join(rows)
        + "\n\n**대응 절차**: 피드 원문 ↔ 파서 비교 → 파서 수정 → Actions의 "
          "`Run workflow`(workflow_dispatch)로 수동 재실행.\n\n"
          "(스테이징 0건=정상이며 이 이슈와 무관. 이 이슈는 파싱 레이어 전용입니다.)"
    )
    p = gh_run(["issue", "create",
                "--title", f"{ISSUE_TITLE_PREFIX}: {', '.join(anomalies)}",
                "--body", body])
    print(f"  [health] 이슈 생성 rc={p.returncode}: {(p.stdout or p.stderr).strip()}")


def anomaly_persisted(prior_events, band, hours=48):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    for r in prior_events:
        if r.get("decision") == "anomaly" and r.get("band") == band:
            try:
                if datetime.datetime.fromisoformat(r["ts"]) >= cutoff:
                    return True
            except Exception:
                pass
    return False


# ──────────────────────────────────────────────
# Modes
# ──────────────────────────────────────────────

def _print_table(health, candidates):
    print(f"\n{'band':18} feed valid  new")
    print("-" * 36)
    for band in BAND_CHANNELS:
        h = health.get(band, {"ok": False, "entries": 0, "valid": 0})
        n_new = sum(1 for c in candidates if c["band"] == band)
        flag = "" if h["ok"] else "  [FETCH FAIL]"
        print(f"{band:18} {h['entries']:4} {h['valid']:5} {n_new:4}{flag}")
    print("-" * 36)
    print(f"TOTAL NEW CANDIDATES: {len(candidates)}")


def cmd_detect(propose):
    states, gh_ok = gh_pr_states()
    if not gh_ok:
        print("  [warn] gh PR 조회 실패 → 기존 PR을 제외하지 못함(로컬 미인증?).")
    existing_pr_ids = set(states.keys())

    candidates, drops, health, band_file = collect_candidates(existing_pr_ids)
    _print_table(health, candidates)

    if candidates:
        print("\nNew song candidates:")
        for c in candidates:
            tag = f" [{c['variant']}]" if c["variant"] else ""
            length = f"{c['length_s']}s" if c["length_s"] else "?s"
            print(f"  {c['band']:16} {c['published']} {length:>5} | {c['name']}{tag}")

    # Parsing-layer anomalies (NOT zero-staged; that is normal).
    anomalies = [b for b, h in health.items() if (not h["ok"]) or h["valid"] == 0]

    if not propose:
        print("\n--dry: 삽입 미리보기 (파일/PR/로그/푸시 없음)")
        for c in candidates:
            path = band_file.get(c["band"]) or (DATA_DIR / f"{c['band']}.yaml")
            text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            numbering = "Cover" if c["is_cover"] else "Single"
            album_title = "Covers" if c["is_cover"] else "New Singles"
            tn = c["published"] or datetime.date.today().isoformat()
            new_text, action = insert_track(text, c["band"], numbering, album_title,
                                            FALLBACK_IMG, tn, c["name"], WATCH_SHORT.format(c["video_id"]))
            ok = _verify_insertion(new_text, c["band"], c["video_id"])
            print(f"\n  → {path.name}  [{action}, numbering={numbering}]  verify={'OK' if ok else 'FAIL'}")
            print(f"    +     - track_number: {yaml_squote(tn)}")
            print(f"    +       name: {yaml_squote(c['name'])}")
            print(f"    +       url: {WATCH_SHORT.format(c['video_id'])}")
        if anomalies:
            print(f"\n  [dry] 파싱 이상 밴드(실제 실행 시 알람 평가): {anomalies}")
        return

    # ---- propose (real) ----
    prior = load_events()
    seen_pairs = {(r.get("video_id"), r.get("decision")) for r in prior}
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_events = []

    opened = 0
    for c in candidates:
        branch = open_pr(c, band_file)
        if branch is None:
            continue
        opened += 1
        if (c["video_id"], "staged") not in seen_pairs:
            new_events.append({
                "ts": now_iso, "band": c["band"], "video_id": c["video_id"],
                "title": c["name"], "published": c["published"], "length_s": c["length_s"],
                "variant": c["variant"], "decision": "staged", "drop_reason": None,
                "pr": branch,
            })

    for d in drops:
        if (d["video_id"], "dropped") not in seen_pairs:
            rec = {"ts": now_iso, "band": d["band"], "video_id": d["video_id"],
                   "title": d["name"], "published": d["published"], "length_s": d["length_s"],
                   "variant": d["variant"], "decision": "dropped",
                   "drop_reason": d["drop_reason"], "pr": None}
            new_events.append(rec)

    # Anomaly events are always logged (used for soft->hard escalation).
    for b in anomalies:
        new_events.append({"ts": now_iso, "band": b, "decision": "anomaly",
                           "kind": "fetch_failed" if not health[b]["ok"] else "zero_valid"})

    append_events(new_events)
    print(f"\nOpened {opened} PR(s); logged {len(new_events)} new event(s).")

    # Alarm policy: multi-band -> hard; single band -> hard only if it persisted.
    if len(anomalies) >= 2:
        print(f"  [health] 다중 밴드 파싱 이상 {anomalies} → 하드 알람")
        open_health_issue(anomalies, health)
    elif len(anomalies) == 1:
        b = anomalies[0]
        if anomaly_persisted(prior, b):
            print(f"  [health] 단일 밴드 {b} 파싱 이상 지속 → 하드 승격")
            open_health_issue(anomalies, health)
        else:
            print(f"  [health] 단일 밴드 {b} 파싱 이상(소프트 로그) — 다음 실행에서 지속 시 승격")

    commit_log()


def cmd_report():
    records = load_events()
    states, gh_ok = gh_pr_states()
    staged = [r for r in records if r.get("decision") == "staged"]
    tp = fp = pending = 0
    for r in staged:
        st = states.get(r["video_id"])
        if st == "MERGED":
            tp += 1
        elif st == "CLOSED":
            fp += 1
        else:
            pending += 1
    decided = tp + fp
    precision = (tp / decided) if decided else None

    print("=== RSS autoloader report ===")
    if not gh_ok:
        print("(gh PR 조회 실패 — TP/FP는 부정확할 수 있음)")
    print(f"staged total : {len(staged)}")
    print(f"  TP (merged): {tp}")
    print(f"  FP (closed): {fp}")
    print(f"  pending    : {pending}")
    print(f"precision    : {f'{precision:.3f} ({tp}/{decided})' if precision is not None else 'N/A (아직 결정된 PR 없음)'}")

    dropped = [r for r in records if r.get("decision") == "dropped"]
    reasons = Counter(r.get("drop_reason") for r in dropped)
    print(f"\ndropped (TN) total: {len(dropped)}")
    for reason, n in reasons.most_common():
        print(f"  {reason:14} {n}")

    anomalies = [r for r in records if r.get("decision") == "anomaly"]
    print(f"\nanomaly events: {len(anomalies)}")
    for r in anomalies[-5:]:
        print(f"  {r.get('ts','?')[:19]} {r.get('band')} {r.get('kind')}")
    print("\nFN(놓친 신곡)은 자동 검출 불가 → 'python src/tools/collect/youtube_rss.py --audit'로 휴리스틱 drop 점검.")


def cmd_audit():
    records = load_events()
    heur = [r for r in records if r.get("decision") == "dropped"
            and r.get("drop_reason") in ("variant", "length_short")]
    print("=== 휴리스틱 drop 감사 (FN이 숨을 수 있는 곳) ===")
    print("variant/length로 버린 항목 — 실제 신곡이 섞여 있으면 수동 추가 필요.\n")
    if not heur:
        print("(해당 없음)")
        return
    heur.sort(key=lambda r: (r.get("drop_reason"), r.get("band"), r.get("published") or ""))
    for r in heur:
        length = f"{r['length_s']}s" if r.get("length_s") else "?"
        tag = r.get("variant") or ""
        print(f"  [{r['drop_reason']:12}] {r['band']:16} {r.get('published','')} {length:>5} | {r['title']} ({tag})")
    print(f"\n총 {len(heur)}건. known_id/known_name drop은 안전하므로 제외됨.")


def cmd_show(limit: int = 8):
    for band, channel_id in BAND_CHANNELS.items():
        print(f"\n=== {band} ({channel_id}) ===")
        entries, ok = fetch_feed(channel_id)
        if not ok:
            print("  [feed error]")
            continue
        for e in entries[:limit]:
            print(f"  {e['published']} | {e['video_id']} | {e['title']}")


def main():
    args = sys.argv[1:]
    if "--show" in args:
        cmd_show()
    elif "--report" in args:
        cmd_report()
    elif "--audit" in args:
        cmd_audit()
    elif "--propose" in args:
        cmd_detect(propose=True)
    elif "--dry" in args:
        cmd_detect(propose=False)
    else:
        print("기본=미리보기(--dry). 실제 PR/로그/푸시는 --propose (CI 전용).")
        print("모드: --dry | --propose | --report | --audit | --show\n")
        cmd_detect(propose=False)


if __name__ == "__main__":
    main()
