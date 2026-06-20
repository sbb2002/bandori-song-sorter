"""
YouTube new-song detector for bandori-song-sorter.

Free, no API key, no extra dependencies (urllib + xml.etree + the project's PyYAML).

Idea
----
Each band's official audio lives on its YouTube Music auto-generated
"<Band> - Topic" channel. Those channels contain *songs only* (no news,
trailers or livestreams) and are band-specific, so polling each band's Topic
RSS feed gives us both automatic band assignment *and* song-only filtering for
free. We compare feed entries against the songs already in data/*.yaml and
stage genuinely new ones in an inbox CSV for review before they are added.

We never modify data/*.yaml and never push anything. Output is limited to
  tools/rss_inbox.csv   - review queue of new song candidates
  tools/rss_seen.json   - ledger of video ids already processed

Usage
-----
  python tools/youtube_rss.py            detect new songs, update inbox + seen
  python tools/youtube_rss.py --dry      detect & print only (no file writes)
  python tools/youtube_rss.py --show     dump latest feed entries per band
"""

import sys
import os
import re
import json
import csv
import datetime
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

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


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INBOX_CSV = ROOT / "tools" / "rss_inbox.csv"
SEEN_JSON = ROOT / "tools" / "rss_seen.json"

FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
WATCH_URL = "https://youtu.be/{}"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# band (as used in data/*.yaml `band:`) -> "<Band> - Topic" channel id.
# Derived from the existing data; verified all 13 bands resolve to a Topic channel.
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

INBOX_FIELDS = ["detected_at", "band", "name", "release_date", "video_id", "variant", "url"]

# We only catalogue full original versions and the bands' cover songs.
# Length-reduced / non-studio versions (TV Size, Short, live, instrumental)
# are dropped and never reach the inbox.
KEEP_VARIANTS = {"", "cover"}


# ──────────────────────────────────────────────
# Helpers
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
    'Alive' are not misclassified.
    """
    t = unicodedata.normalize("NFKC", title or "").lower()
    if "tv size" in t or "tvsize" in t or "tv-size" in t:
        return "tv_size"
    if "short ver" in t or "short edit" in t or "short size" in t:
        return "short"
    if "cover" in t:
        return "cover"
    if "the first take" in t:
        return "live"
    if "instrumental" in t or "off vocal" in t or "off-vocal" in t or "カラオケ" in t:
        return "instrumental"
    if "(live" in t or "live ver" in t or "【live" in t or " - live" in t:
        return "live"
    return ""


# ──────────────────────────────────────────────
# Data / feed access
# ──────────────────────────────────────────────

def load_existing():
    """Return (names_by_band, ids_by_band) from every data/*.yaml file."""
    names_by_band = {}
    ids_by_band = {}
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".yaml"):
            continue
        albums = yaml.safe_load((DATA_DIR / fn).read_text(encoding="utf-8")) or []
        for album in albums:
            band = album.get("band", "")
            names = names_by_band.setdefault(band, set())
            ids = ids_by_band.setdefault(band, set())
            for track in (album.get("tracks") or []):
                if track.get("name"):
                    names.add(norm_name(track["name"]))
                vid = video_id(track.get("url"))
                if vid:
                    ids.add(vid)
    return names_by_band, ids_by_band


def fetch_feed(channel_id: str):
    """Return the channel's recent uploads as a list of entry dicts."""
    root = ET.fromstring(http_get(FEED_URL.format(channel_id)))
    entries = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        title = e.findtext("a:title", namespaces=NS) or ""
        published = (e.findtext("a:published", namespaces=NS) or "")[:10]
        if vid:
            entries.append({"video_id": vid, "title": title, "published": published})
    return entries


def load_seen() -> dict:
    if SEEN_JSON.exists():
        try:
            return json.loads(SEEN_JSON.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_seen(seen: dict) -> None:
    SEEN_JSON.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def append_inbox(rows: list) -> None:
    new_file = not INBOX_CSV.exists()
    with open(INBOX_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INBOX_FIELDS)
        if new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


# ──────────────────────────────────────────────
# Modes
# ──────────────────────────────────────────────

def cmd_show(limit: int = 8) -> None:
    for band, channel_id in BAND_CHANNELS.items():
        print(f"\n=== {band} ({channel_id}) ===")
        try:
            for e in fetch_feed(channel_id)[:limit]:
                print(f"  {e['published']} | {e['video_id']} | {e['title']}")
        except Exception as exc:
            print(f"  [feed error] {exc!r}")


def cmd_detect(dry: bool = False) -> None:
    names_by_band, ids_by_band = load_existing()
    seen = load_seen()
    now = datetime.date.today().isoformat()

    inbox_rows = []
    total_new = 0
    print(f"{'band':18} feed  known  NEW")
    print("-" * 38)

    for band, channel_id in BAND_CHANNELS.items():
        try:
            entries = fetch_feed(channel_id)
        except Exception as exc:
            print(f"{band:18} [feed error] {exc!r}")
            continue

        known_names = names_by_band.get(band, set())
        known_ids = ids_by_band.get(band, set())

        # Collapse duplicate uploads of the same song: keep one per normalized
        # name, preferring a full version over a cover, then the earliest date.
        best = {}
        for e in entries:
            vid, title = e["video_id"], e["title"]
            if vid in known_ids or vid in seen:
                continue
            variant = variant_tag(title)
            if variant not in KEEP_VARIANTS:
                continue  # drop TV Size / Short / live / instrumental
            key = norm_name(title)
            if key in known_names:
                continue  # same song already in data under a different upload
            rank = (variant != "", e["published"] or "9999-99-99")
            if key not in best or rank < best[key][0]:
                best[key] = (rank, e)

        new_here = [v[1] for v in best.values()]

        for e in new_here:
            inbox_rows.append({
                "detected_at": now,
                "band": band,
                "name": e["title"],
                "release_date": e["published"],
                "video_id": e["video_id"],
                "variant": variant_tag(e["title"]),
                "url": WATCH_URL.format(e["video_id"]),
            })

        total_new += len(new_here)
        print(f"{band:18} {len(entries):4}  {len(known_names):5}  {len(new_here):3}")

    # Order the whole queue: full original versions first, then covers;
    # each group oldest -> newest (ties broken by band, then name).
    inbox_rows.sort(key=lambda r: (
        r["variant"] != "",
        r["release_date"] or "9999-99-99",
        r["band"],
        r["name"],
    ))

    print("-" * 38)
    print(f"TOTAL NEW CANDIDATES: {total_new}")

    if inbox_rows:
        print("\nNew song candidates:")
        for r in inbox_rows:
            tag = f" [{r['variant']}]" if r["variant"] else ""
            print(f"  {r['band']:16} {r['release_date']} | {r['name']}{tag}")

    if dry:
        print("\n(--dry: no files written)")
        return

    if inbox_rows:
        append_inbox(inbox_rows)
        for r in inbox_rows:
            seen[r["video_id"]] = {"band": r["band"], "name": r["name"], "detected_at": now}
        save_seen(seen)
        print(f"\nWrote {len(inbox_rows)} row(s) -> {INBOX_CSV}")
        print(f"Updated ledger     -> {SEEN_JSON}")
    else:
        print("\nNothing new to stage.")


def main() -> None:
    args = sys.argv[1:]
    if "--show" in args:
        cmd_show()
    elif "--dry" in args:
        cmd_detect(dry=True)
    else:
        cmd_detect(dry=False)


if __name__ == "__main__":
    main()
