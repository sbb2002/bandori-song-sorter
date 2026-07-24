"""
미추가 곡 백필 (HANDOFF 1) — Topic 채널 업로드 전체를 YouTube Data API로 받아
기존 src/content/songs/*.yaml(known video_id/name)과 비교 → 누락 후보 도출.

RSS는 채널당 최근 ~15개만 반환하므로 과거 영상은 youtube_rss로 영원히 안 들어온다.
이 스크립트는 Data API(playlistItems 페이징)로 업로드 전체를 받아 그 한계를 넘는다.
채널=밴드라 배정 자동, Topic이라 음원만(노이즈 적음).

**반자동**: 후보를 출력만 한다(데이터 미변경). 사람이 확인한 뒤 추가.
필터는 youtube_rss와 동일:
  · variant_tag ∉ {'', 'cover'} → 변형(TV size/short/live/inst/remix…) 제외
  · norm_name 이 known_name 에 있으면 '곡명 기존재'(같은 곡 다른 영상/버전)로 분리 표시

**메인 채널 커버곡 스캔(2026-07-25)**: `BAND_MAIN_CHANNELS`에 등록된 밴드는 Topic 채널과
별개로 메인(공식) 채널도 추가로 훑는다. 메인 채널은 노래 외 콘텐츠가 섞여 variant_tag
블랙리스트가 안전하지 않으므로, 제목에 '歌ってみた'가 있는 경우만(화이트리스트)
후보로 본다(강제 variant='cover', 출력에 [MAIN] 태그). 상세 설계:
docs/working/spec/main-channel-cover-backfill.md

  python src/tools/collect/backfill.py            # 전체 밴드
  python src/tools/collect/backfill.py roselia    # 특정 밴드만(공백 구분 다수 가능)
"""
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_rss import (video_id, norm_name, variant_tag, KEEP_VARIANTS,
                         BAND_CHANNELS, WATCH_SHORT, load_existing,
                         fetch_length_seconds, MIN_LENGTH_S)
from youtube_api import load_env_key, fetch_uploads, APIError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ──────────────────────────────────────────────
# 메인 채널 설정 (歌ってみた 화이트리스트)
# ──────────────────────────────────────────────

# 밴드의 메인(공식) 채널 — Topic 채널과 별개. 현재 mugendai_mutype만 확인됨(2026-07-25,
# 사용자 요청으로 조사). 나머지 11개 정식 밴드의 메인 채널 id는 미조사 상태 — 여기 추가하기
# 전에 반드시 YouTube Data API channels.list 등으로 실제 채널이 맞는지 확인할 것(추측 금지,
# 잘못된 채널을 넣으면 엉뚱한 콘텐츠가 그 밴드 데이터로 잘못 들어갈 위험).
BAND_MAIN_CHANNELS = {
    "mugendai_mutype": "UCxL_Vlnhfo46sN6vPHR_4hA",
}

# 메인 채널 스캔 전용 화이트리스트 마커. Topic 채널(BAND_CHANNELS)이 아니라 메인 채널은
# 노래 외 콘텐츠(생방송·잡담쇼츠·미니애니·CM 등)가 다수라 variant_tag()의 블랙리스트 방식이
# 안전하지 않다(미인식 제목은 전부 "오리지널 곡"으로 폴스루됨). 이 마커가 제목에 있는
# 경우만 커버곡 후보로 본다(실측 mutype 250개 업로드 전수조사에서 정밀도 100% 확인).
_COVER_SERIES_MARKERS = ("歌ってみた",)


def is_cover_series_title(title: str) -> bool:
    """제목에 '歌ってみた' 마커가 있으면 True (NFKC 정규화 후 부분일치)."""
    t = unicodedata.normalize("NFKC", title or "")
    return any(m in t for m in _COVER_SERIES_MARKERS)


def main():
    only = {a for a in sys.argv[1:] if not a.startswith("-")}

    key = load_env_key()
    if not key:
        print("‼️ .env 에 YOUTUBE_API_KEY 가 없습니다."); sys.exit(1)

    names_by_band, ids_by_band, _ = load_existing()
    bands = [b for b in BAND_CHANNELS if not only or b in only]
    print(f"백필 대상 밴드 {len(bands)}개 — Topic 업로드 전체 조회(Data API)\n")

    total_new = total_namedup = 0
    total_main_new = 0
    summary = []
    for band in bands:
        try:
            uploads = fetch_uploads(BAND_CHANNELS[band], key)
        except APIError as e:
            print(f"[{band}] ‼️ API 오류: {e}")
            summary.append((band, 0, 0, 0, 0, 0))
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

        # ── 메인 채널 추가 스캔(歌ってみた 화이트리스트만) ──
        main_new = []
        main_ch = BAND_MAIN_CHANNELS.get(band)
        if main_ch:
            try:
                main_uploads = fetch_uploads(main_ch, key)
            except APIError as e:
                print(f"[{band}] ‼️ 메인 채널 API 오류: {e}")
                main_uploads = []
            for u in main_uploads:
                if u["video_id"] in known_ids:
                    continue
                if not is_cover_series_title(u["title"]):
                    continue                   # 화이트리스트 미통과 → 스캔 대상 아님
                kn = norm_name(u["title"])
                if kn in known_names:
                    namedup.append((u, "cover")); continue
                if kn in seen:
                    continue
                length_s = fetch_length_seconds(u["video_id"])
                if length_s is not None and length_s < MIN_LENGTH_S:
                    variant_drop.append((u, "cover")); continue
                seen.add(kn)
                main_new.append((u, "cover"))  # variant는 강제 'cover'

        total_main_new += len(main_new)
        summary.append((band, len(uploads), len(new), len(namedup), len(variant_drop), len(main_new)))

        combined_new = [(u, var, False) for u, var in new] + [(u, var, True) for u, var in main_new]
        if combined_new:
            print(f"=== {band} — 누락 후보 {len(new) + len(main_new)} (업로드 {len(uploads)}) ===")
            for u, var, is_main in sorted(combined_new, key=lambda x: x[0]["published"]):
                var_tag = f" [{var}]" if var else ""
                main_tag = " [MAIN]" if is_main else ""
                print(f"   {u['published']}  {WATCH_SHORT.format(u['video_id'])}  {u['title']}{var_tag}{main_tag}")
            print()
        if namedup:
            print(f"   ⚠️ [{band}] 곡명 기존재(다른 영상/버전) {len(namedup)} — 추가 전 대조 필요:")
            for u, var in sorted(namedup, key=lambda x: x[0]["published"]):
                tag = f" [{var}]" if var else ""
                print(f"      {u['published']}  {WATCH_SHORT.format(u['video_id'])}  {u['title']}{tag}")
            print()

    print("=" * 70)
    print(f"{'band':18} {'upl':>4} {'new':>4} {'main':>4} {'namedup':>8} {'var제외':>7}")
    print("-" * 70)
    for band, nu, nn, nd, nv, nm in summary:
        print(f"{band:18} {nu:4} {nn:4} {nm:4} {nd:8} {nv:7}")
    print("-" * 70)
    print(f"신규 후보 합계: {total_new + total_main_new} "
          f"(Topic {total_new} + 메인 채널 {total_main_new}) · 곡명중복(검토) {total_namedup}")
    print("\n※ 출력만 — 데이터 미변경. 추가는 후보 확인 후 별도 단계.")


if __name__ == "__main__":
    main()
