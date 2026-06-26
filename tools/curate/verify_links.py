"""
Data-quality triage for bandori-song-sorter (HANDOFF #1).

검수 *보조* 도구입니다. 의심 항목만 골라 표로 뽑아줄 뿐, 데이터(data/*.yaml)는
절대 수정하지 않습니다. 모든 편집은 사람이 직접 합니다(데이터 변경이 회귀 리스크의
본체이므로 — docs/HANDOFF.md 원칙).

youtube_rss.py의 video_id / norm_name / fetch_length_seconds / http_get 를 재사용해
파싱 규칙을 한 곳에서만 관리합니다.

검수 항목(561곡 전수 대신, 플래그된 수십 건만 사람이 확인)
  A. 빈 url            — ♪만 뜨고 재생 불가. 행 삭제/보강 결정 필요.
  B. url 오류 의심     — 같은 video_id를 서로 다른 곡명이 가리킴(어쿠스틱 등 변형곡이
                         원곡 url을 잘못 물고 있는 케이스). 둘 다 살리되 url 교정. 최우선.
  C. undefined 더미앨범 — C1 redundant(이미 정규앨범에 있는 곡=삭제해도 곡 안 사라짐)
                         / C2 unique(유일본→정규앨범으로 이동 필요) / C3 빈 url.
  D. 앨범 중복(정상)   — 같은 video_id·같은 곡명이 여러 정규앨범에 수록. 데이터 유지,
                         앱이 1회만 표시(먼저 검색된 것 재생). 참고용.
  E. 동명-다른영상     — 밴드 내 같은 곡명인데 video_id가 다름(재녹음/오타 가능). 참고용.

레이어(네트워크 사용량 순)
  Layer 0 (기본)  : 오프라인. A~E 전부. 네트워크 0, 결정적.
  Layer 1 --oembed: oEmbed(API키 없음, 곡당 1요청)로 죽은 링크(404/비공개) + 실제 제목 대조.
  Layer 2 --length: watch 페이지 길이 스크랩으로 풀버전/TV Size 판별.
  --all 은 0+1+2.

⚠️ 로컬(가정 IP)에서 실행하세요. Layer 2 길이 스크랩은 데이터센터 IP(GitHub Actions)에선
   consent wall로 막힙니다(youtube_rss와 정반대 — 그래서 이 검수는 CI가 아닌 로컬 전용).

캐시: tools/curate/verify_cache.json (oembed/length 결과). 재실행 시 네트워크를 다시 치지 않음.

사용법
  python tools/curate/verify_links.py                 # Layer 0 (오프라인)
  python tools/curate/verify_links.py --oembed        # + 죽은 링크/제목 대조
  python tools/curate/verify_links.py --length        # + 풀버전 판별
  python tools/curate/verify_links.py --all           # 전부
  python tools/curate/verify_links.py --all --json tools/curate/verify_report.json
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("PyYAML이 필요합니다: pip install pyyaml")
    sys.exit(1)

# 파싱 규칙은 youtube_rss와 공유(중복 정의 금지). youtube_rss 는 tools/collect/ 에 있음.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
from youtube_rss import video_id, norm_name, fetch_length_seconds, UA, MIN_LENGTH_S

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]   # tools/curate/<file> → repo root
DATA_DIR = ROOT / "data"
CACHE_PATH = ROOT / "tools" / "curate" / "verify_cache.json"

UNDEF = "undefined"


# ──────────────────────────────────────────────
# Load tracks (flat record list)
# ──────────────────────────────────────────────

def load_tracks():
    """Return a flat list of track dicts across every data/*.yaml."""
    tracks = []
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.endswith(".yaml"):
            continue
        albums = yaml.safe_load((DATA_DIR / fn).read_text(encoding="utf-8")) or []
        for album in albums:
            band = album.get("band", "")
            numbering = album.get("numbering", "")
            album_title = album.get("album_title", "")
            for tr in (album.get("tracks") or []):
                name = tr.get("name", "")
                url = tr.get("url")
                url_s = str(url).strip() if url is not None else ""
                tracks.append({
                    "file": fn,
                    "band": band,
                    "numbering": numbering,
                    "album": album_title,
                    "name": name,
                    "url": url_s,
                    "vid": video_id(url_s) if url_s else None,
                    "norm": norm_name(name),
                    "undef": numbering == UNDEF or album_title == UNDEF,
                })
    return tracks


# ──────────────────────────────────────────────
# Layer 0 analysis (offline)
# ──────────────────────────────────────────────

def analyze(tracks):
    """Compute A~E from the flat track list. Pure, no network."""
    empty = [t for t in tracks if not t["url"]]

    by_vid = defaultdict(list)
    for t in tracks:
        if t["vid"]:
            by_vid[t["vid"]].append(t)

    suspect_url = []     # B: same vid, different real names
    album_dup = []       # D: same vid, same name, multiple real albums
    for vid, group in by_vid.items():
        real = [t for t in group if not t["undef"]]
        norms = {t["norm"] for t in real}
        if len(real) >= 2 and len(norms) >= 2:
            suspect_url.append((vid, real))
        elif len(real) >= 2 and len(norms) == 1:
            albums = {(t["band"], t["album"]) for t in real}
            if len(albums) >= 2:
                album_dup.append((vid, real))

    # C: undefined classification.
    real_ids_by_band = defaultdict(set)
    for t in tracks:
        if not t["undef"] and t["vid"]:
            real_ids_by_band[t["band"]].add(t["vid"])
    undef_redundant, undef_unique, undef_empty = [], [], []
    for t in tracks:
        if not t["undef"]:
            continue
        if not t["url"]:
            undef_empty.append(t)
        elif t["vid"] and t["vid"] in real_ids_by_band[t["band"]]:
            undef_redundant.append(t)
        else:
            undef_unique.append(t)

    # E: same norm name within band, different video ids (real albums only).
    by_band_norm = defaultdict(list)
    for t in tracks:
        if not t["undef"] and t["norm"] and t["vid"]:
            by_band_norm[(t["band"], t["norm"])].append(t)
    name_diff_vid = []
    for (band, norm), group in by_band_norm.items():
        vids = {t["vid"] for t in group}
        if len(vids) >= 2:
            name_diff_vid.append((band, norm, group))

    return {
        "empty": empty,
        "suspect_url": suspect_url,
        "album_dup": album_dup,
        "undef_redundant": undef_redundant,
        "undef_unique": undef_unique,
        "undef_empty": undef_empty,
        "name_diff_vid": name_diff_vid,
        "by_vid": by_vid,
    }


# ──────────────────────────────────────────────
# Layers 1 & 2 (network, cached)
# ──────────────────────────────────────────────

def load_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=0),
                          encoding="utf-8")


def fetch_oembed(vid):
    """(status, title, author). status: ok | unavailable | notfound | error."""
    url = ("https://www.youtube.com/oembed?url="
           f"https://www.youtube.com/watch?v={vid}&format=json")
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        return ("ok", data.get("title"), data.get("author_name"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ("notfound", None, None)
        if e.code in (401, 403):
            return ("unavailable", None, None)
        return ("error", None, None)
    except Exception:
        return ("error", None, None)


def run_network(tracks, do_oembed, do_length):
    """Fill cache with oembed/length for every distinct video id. Returns cache."""
    cache = load_cache()
    vids = sorted({t["vid"] for t in tracks if t["vid"]})
    total = len(vids)
    for i, vid in enumerate(vids, 1):
        entry = cache.setdefault(vid, {})
        need_o = do_oembed and "oembed" not in entry
        need_l = do_length and "length" not in entry
        if not (need_o or need_l):
            continue
        if need_o:
            status, title, author = fetch_oembed(vid)
            entry["oembed"] = {"status": status, "title": title, "author": author}
        if need_l:
            entry["length"] = fetch_length_seconds(vid)
        time.sleep(0.2)   # 예의상 지연(레이트리밋 회피). 캐시 덕에 1회성 비용.
        if i % 25 == 0 or i == total:
            print(f"  ...network {i}/{total}", file=sys.stderr)
            save_cache(cache)
    save_cache(cache)
    return cache


# ──────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────

def loc(t):
    return f"{t['band']}/{t['album']}/{t['name']}"


def report(tracks, A, cache=None, do_oembed=False, do_length=False):
    print("=" * 64)
    print("bandori-song-sorter 데이터 품질 triage  (읽기 전용 · 데이터 무변경)")
    print("=" * 64)
    print(f"총 트랙 {len(tracks)} · video_id 보유 {sum(1 for t in tracks if t['vid'])}")
    print()

    # A
    print(f"[A] 빈 url — {len(A['empty'])}건  (♪만 뜨고 재생 불가 → 삭제/보강 결정)")
    for t in A["empty"]:
        print(f"    {t['file']:24} {t['band']}/{t['album']} | {t['name']!r}")
    print()

    # B
    print(f"[B] url 오류 의심 — {len(A['suspect_url'])}그룹  ★최우선")
    print("    같은 video_id를 서로 다른 곡명이 가리킴(변형곡이 원곡 url을 잘못 물음).")
    print("    → 두 곡 모두 유지하되, 잘못된 쪽 url을 올바른 영상으로 교정.")
    for vid, group in sorted(A["suspect_url"], key=lambda g: g[1][0]["band"]):
        print(f"    {vid}:")
        for t in group:
            print(f"        - {loc(t)}   ({t['url']})")
    print()

    # C
    print(f"[C] undefined 더미앨범 — redundant {len(A['undef_redundant'])} / "
          f"unique {len(A['undef_unique'])} / 빈url {len(A['undef_empty'])}")
    print("    C2 unique(유일본 → 정규앨범으로 이동 필요):")
    for t in sorted(A["undef_unique"], key=lambda t: t["band"]):
        print(f"        {t['band']:18} {t['name']!r}  ({t['url']})")
    print("    C1 redundant(이미 정규앨범에 존재 → 삭제해도 곡 안 사라짐):")
    for t in sorted(A["undef_redundant"], key=lambda t: t["band"]):
        print(f"        {t['band']:18} {t['name']!r}")
    print()

    # D
    print(f"[D] 앨범 중복(정상) — {len(A['album_dup'])}그룹  참고용(데이터 유지·앱 1회 표시)")
    for vid, group in sorted(A["album_dup"], key=lambda g: g[1][0]["band"]):
        albums = ", ".join(sorted({t["album"] for t in group}))
        print(f"    {vid}  {group[0]['band']}/{group[0]['name']}  ←  [{albums}]")
    print()

    # E
    print(f"[E] 동명-다른영상 — {len(A['name_diff_vid'])}그룹  참고용(재녹음/오타 가능)")
    for band, norm, group in sorted(A["name_diff_vid"], key=lambda g: g[0]):
        names = " | ".join(f"{t['album']}:{t['name']}({t['vid']})" for t in group)
        print(f"    {band}: {names}")
    print()

    # Layer 1/2
    if cache is not None and (do_oembed or do_length):
        print("-" * 64)
        if do_oembed:
            dead, mism = [], []
            for t in tracks:
                if not t["vid"]:
                    continue
                o = cache.get(t["vid"], {}).get("oembed")
                if not o:
                    continue
                if o["status"] in ("notfound", "unavailable"):
                    dead.append((t, o["status"]))
                elif o["status"] == "ok" and o.get("title"):
                    if norm_name(t["name"]) not in norm_name(o["title"]):
                        mism.append((t, o["title"]))
            print(f"[L1] 죽은 링크 — {len(dead)}건  ★최우선(404/비공개)")
            for t, st in dead:
                print(f"    [{st:11}] {loc(t)}  {t['url']}")
            print(f"[L1] 제목 불일치 — {len(mism)}건  (oEmbed 실제 제목에 곡명이 없음)")
            for t, title in mism:
                print(f"    {loc(t)}\n        실제: {title}")
            print()
        if do_length:
            short = []
            for t in tracks:
                if not t["vid"]:
                    continue
                ln = cache.get(t["vid"], {}).get("length")
                if isinstance(ln, int) and ln < MIN_LENGTH_S:
                    short.append((t, ln))
            print(f"[L2] 짧은 영상 — {len(short)}건  (<{MIN_LENGTH_S}s, TV Size/Short 의심)")
            for t, ln in sorted(short, key=lambda x: x[1]):
                print(f"    {ln:>4}s  {loc(t)}")
            print()

    print("=" * 64)
    print("처리 권장 순서:  B/L1(틀린·죽은 링크) → C2(유일본 이동) → A(빈 url) → "
          "L2(풀버전) → C1(중복 정리)")
    print("데이터 변경 후 곡수 변동 시 JS 카운트 테스트 갱신(이 장치 node 없음 → 다른 장치 npm test).")


def build_json(tracks, A, cache):
    def slim(t):
        return {"band": t["band"], "album": t["album"], "name": t["name"],
                "url": t["url"], "vid": t["vid"]}
    out = {
        "total": len(tracks),
        "A_empty_url": [slim(t) for t in A["empty"]],
        "B_suspect_url": [{"vid": v, "tracks": [slim(t) for t in g]}
                          for v, g in A["suspect_url"]],
        "C_undef_unique": [slim(t) for t in A["undef_unique"]],
        "C_undef_redundant": [slim(t) for t in A["undef_redundant"]],
        "C_undef_empty": [slim(t) for t in A["undef_empty"]],
        "D_album_dup": [{"vid": v, "tracks": [slim(t) for t in g]}
                        for v, g in A["album_dup"]],
    }
    if cache is not None:
        out["cache_size"] = len(cache)
    return out


def main():
    args = sys.argv[1:]
    do_oembed = "--oembed" in args or "--all" in args
    do_length = "--length" in args or "--all" in args
    json_path = None
    if "--json" in args:
        i = args.index("--json")
        if i + 1 < len(args):
            json_path = args[i + 1]

    tracks = load_tracks()
    A = analyze(tracks)

    cache = None
    if do_oembed or do_length:
        print("네트워크 조회 중(캐시 사용)...", file=sys.stderr)
        cache = run_network(tracks, do_oembed, do_length)

    report(tracks, A, cache, do_oembed, do_length)

    if json_path:
        Path(json_path).write_text(
            json.dumps(build_json(tracks, A, cache), ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\nJSON 리포트 저장: {json_path}")


if __name__ == "__main__":
    main()
