"""
미추가 곡 백필 (HANDOFF 1) — Topic 채널 업로드 전체를 YouTube Data API로 받아
기존 data/*.yaml(known video_id/name)과 비교 → 누락 후보 도출.

RSS는 채널당 최근 ~15개만 반환하므로 과거 영상은 youtube_rss로 영원히 안 들어온다.
이 스크립트는 Data API(playlistItems 페이징)로 업로드 전체를 받아 그 한계를 넘는다.
채널=밴드라 배정 자동, Topic이라 음원만(노이즈 적음).

**반자동**: 후보를 출력만 한다(데이터 미변경). 사람이 확인한 뒤 추가.
필터는 youtube_rss와 동일:
  · variant_tag ∉ {'', 'cover'} → 변형(TV size/short/live/inst/remix…) 제외
  · norm_name 이 known_name 에 있으면 '곡명 기존재'(같은 곡 다른 영상/버전)로 분리 표시

  python tools/backfill.py            # 전체 밴드
  python tools/backfill.py roselia    # 특정 밴드만(공백 구분 다수 가능)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_rss import (video_id, norm_name, variant_tag, KEEP_VARIANTS,
                         BAND_CHANNELS, WATCH_SHORT, load_existing)
from youtube_api import load_env_key, fetch_uploads, APIError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    only = {a for a in sys.argv[1:] if not a.startswith("-")}

    key = load_env_key()
    if not key:
        print("‼️ .env 에 YOUTUBE_API_KEY 가 없습니다."); sys.exit(1)

    names_by_band, ids_by_band, _ = load_existing()
    bands = [b for b in BAND_CHANNELS if not only or b in only]
    print(f"백필 대상 밴드 {len(bands)}개 — Topic 업로드 전체 조회(Data API)\n")

    total_new = total_namedup = 0
    summary = []
    for band in bands:
        try:
            uploads = fetch_uploads(BAND_CHANNELS[band], key)
        except APIError as e:
            print(f"[{band}] ‼️ API 오류: {e}")
            summary.append((band, 0, 0, 0, 0))
            continue
        known_ids = ids_by_band.get(band, set())
        known_names = names_by_band.get(band, set())

        new, namedup, variant_drop, seen = [], [], [], set()
        for u in uploads:
            if u["video_id"] in known_ids:
                continue
            var = variant_tag(u["title"])
            if var not in KEEP_VARIANTS:
                variant_drop.append((u, var)); continue
            kn = norm_name(u["title"])
            if kn in known_names:
                namedup.append((u, var)); continue
            if kn in seen:
                continue                       # 같은 곡 중복 업로드
            seen.add(kn)
            new.append((u, var))

        total_new += len(new); total_namedup += len(namedup)
        summary.append((band, len(uploads), len(new), len(namedup), len(variant_drop)))

        if new:
            print(f"=== {band} — 누락 후보 {len(new)} (업로드 {len(uploads)}) ===")
            for u, var in sorted(new, key=lambda x: x[0]["published"]):
                tag = f" [{var}]" if var else ""
                print(f"   {u['published']}  {WATCH_SHORT.format(u['video_id'])}  {u['title']}{tag}")
            print()
        if namedup:
            print(f"   ⚠️ [{band}] 곡명 기존재(다른 영상/버전) {len(namedup)} — 추가 전 대조 필요:")
            for u, var in sorted(namedup, key=lambda x: x[0]["published"]):
                tag = f" [{var}]" if var else ""
                print(f"      {u['published']}  {WATCH_SHORT.format(u['video_id'])}  {u['title']}{tag}")
            print()

    print("=" * 60)
    print(f"{'band':18} {'upl':>4} {'new':>4} {'namedup':>8} {'var제외':>7}")
    print("-" * 60)
    for band, nu, nn, nd, nv in summary:
        print(f"{band:18} {nu:4} {nn:4} {nd:8} {nv:7}")
    print("-" * 60)
    print(f"신규 후보 합계: {total_new} · 곡명중복(검토) {total_namedup}")
    print("\n※ 출력만 — 데이터 미변경. 추가는 후보 확인 후 별도 단계.")


if __name__ == "__main__":
    main()
