"""
밴드별 조회수 TOP10 산출 (HANDOFF 1) — 워드클라우드 가사 수집 대상 선정.

data/*.yaml 의 재생가능 트랙 video_id 를 YouTube Data API(videos.list, part=statistics)
로 조회수 조회 → 밴드별 내림차순 TOP10. 콘솔 표 + assets/lyrics/<band>.md(가사
붙여넣기 템플릿) 생성. assets/lyrics/ 는 .gitignore 처리됨(원문 비커밋).

대상: 곡 10개 이상인 10개 밴드. various_artists/ikka_dumb_rock/millsage 제외.
  python tools/band_top10.py             # 조회수 조회 + TOP10 출력 + 템플릿 생성
  python tools/band_top10.py --no-write  # 템플릿 미생성(콘솔만)
"""
import sys
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml"); sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_rss import video_id, BAND_CHANNELS
from youtube_api import load_env_key, fetch_view_counts, APIError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LYRICS_DIR = ROOT / "assets" / "lyrics"
TOP_N = 10
EXCLUDE = {"various_artists", "ikka_dumb_rock", "millsage"}


def load_tracks():
    """[{band, name, url, vid}] — url 있는(재생가능) 트랙만."""
    out = []
    for fn in sorted(DATA.glob("*.yaml")):
        for al in (yaml.safe_load(fn.read_text(encoding="utf-8")) or []):
            band = al.get("band", "")
            is_cover = (al.get("numbering") == "Cover") or (al.get("album_title") == "Covers")
            for tr in (al.get("tracks") or []):
                url = tr.get("url")
                us = str(url).strip() if url is not None else ""
                vid = video_id(us) if us else None
                if vid:
                    out.append({"band": band, "name": tr.get("name", ""),
                                "url": us, "vid": vid, "is_cover": is_cover})
    return out


def main():
    write = "--no-write" not in sys.argv[1:]
    key = load_env_key()
    if not key:
        print("‼️ .env 에 YOUTUBE_API_KEY 가 없습니다."); sys.exit(1)

    no_cover = "--no-cover" in sys.argv[1:]
    tracks = load_tracks()
    target = [t for t in tracks if t["band"] in BAND_CHANNELS and t["band"] not in EXCLUDE]
    if no_cover:
        target = [t for t in target if not t["is_cover"]]
    # 같은 video_id 중복 트랙은 1개로 묶음(데이터 중복 방어 — 예: roselia LOUDER)
    seen, uniq = set(), []
    for t in target:
        if t["vid"] in seen:
            continue
        seen.add(t["vid"]); uniq.append(t)
    target = uniq
    vids = sorted({t["vid"] for t in target})
    bands = sorted(set(t["band"] for t in target))
    if no_cover:
        print("(--no-cover: 커버곡 제외)")
    print(f"대상 밴드 {len(bands)}개 · 트랙 {len(target)} · 고유 video_id {len(vids)}")
    print("조회수 조회 중 (YouTube Data API)...")

    try:
        views = fetch_view_counts(vids, key)
    except APIError as e:
        print(f"‼️ API 오류: {e}"); sys.exit(1)

    missing = [v for v in vids if v not in views]
    print(f"조회수 수신 {len(views)}/{len(vids)}"
          + (f" · 누락(비공개/삭제 추정) {len(missing)}" if missing else ""))

    by_band = defaultdict(list)
    for t in target:
        vc = views.get(t["vid"])
        if vc is not None:
            by_band[t["band"]].append((vc, t))

    if write:
        LYRICS_DIR.mkdir(parents=True, exist_ok=True)

    for band in sorted(by_band):
        ranked = sorted(by_band[band], key=lambda x: -x[0])[:TOP_N]
        print(f"\n=== {band} — TOP{len(ranked)} ===")
        for i, (vc, t) in enumerate(ranked, 1):
            tag = " [cover]" if t["is_cover"] else ""
            print(f"  {i:2}. {vc:>12,}  {t['name']}{tag}  ({t['url']})")
        if write:
            md = [f"# {band} — 조회수 TOP{len(ranked)} 가사 수집", "",
                  "<!-- 각 곡 아래 코드블록에 가사를 붙여넣으세요. "
                  "이 폴더(assets/lyrics/)는 .gitignore 처리됨(원문 비커밋). -->", ""]
            for i, (vc, t) in enumerate(ranked, 1):
                md += [f"## {i}. {t['name']}",
                       f"- url: {t['url']}",
                       f"- views: {vc:,}", "",
                       "```", "(여기에 가사)", "```", ""]
            (LYRICS_DIR / f"{band}.md").write_text("\n".join(md), encoding="utf-8")

    if write:
        print(f"\n가사 템플릿 생성: assets/lyrics/<band>.md ({len(by_band)}개 밴드)")
    else:
        print("\n(--no-write: 템플릿 미생성)")


if __name__ == "__main__":
    main()
