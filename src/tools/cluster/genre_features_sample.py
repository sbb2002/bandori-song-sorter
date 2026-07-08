"""장르(밴드) 오디오 피처 재정의 — 0단계: 밴드별 N곡 랜덤 샘플링. 작업 6 후속.

전곡 660을 한 번에 확보하는 대신, **밴드별로 N곡씩 랜덤 샘플링**해 먼저 프록시가
유효한지 검증하고, 유효하면 그때 전곡으로 확장한다(사용자 결정). songs_full.csv의
13개 밴드 전체를 대상으로 하므로 이 로컬(부분 캐시 10밴드)에 없는 roselia·
poppin_party·raise_a_suilen(하드록/메탈·대형 유닛)도 포함돼, "메탈 vs 어쿠스틱"
대비를 이번에는 볼 수 있다.

이 스크립트는 (1) 샘플 목록을 정하고 `sample_manifest.csv`에 기록, (2) `--download`
시 `perceptual_features.ensure_full()`(기존 yt-dlp 다운로드 로직) 재사용해 audio_full/에
확보한다. 다운로드 없이 목록만 볼 때는 `--dry-run`.

사용:
  python src/tools/cluster/genre_features_sample.py --n 15 --dry-run   # 목록만 확인
  python src/tools/cluster/genre_features_sample.py --n 15 --download  # 실제 다운로드(yt-dlp 필요)
그 다음: <hummingbird-python> src/tools/cluster/genre_features_extract.py (audio_full에 있는 파일만 처리)
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))

SONGS_FULL = ROOT / "src/content/cluster/songs_full.csv"
OUTDIR = ROOT / "docs/working/report/genre-features"
MANIFEST = OUTDIR / "sample_manifest.csv"


def sample_rows(n: int, seed: int) -> list[dict]:
    rows = list(csv.DictReader(open(SONGS_FULL, encoding="utf-8")))
    by_band: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_band[r["band"]].append(r)

    rng = random.Random(seed)
    selected = []
    for band, band_rows in sorted(by_band.items()):
        k = min(n, len(band_rows))
        selected.extend(rng.sample(band_rows, k))
    return selected


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15, help="밴드당 샘플 곡 수(기본 15, 부족하면 전량)")
    ap.add_argument("--seed", type=int, default=42, help="재현용 랜덤 시드")
    ap.add_argument("--dry-run", action="store_true", help="목록만 출력·기록, 다운로드 안 함")
    ap.add_argument("--download", action="store_true", help="누락 파일 yt-dlp로 다운로드")
    args = ap.parse_args(argv)

    selected = sample_rows(args.n, args.seed)

    by_band: dict[str, int] = defaultdict(int)
    for r in selected:
        by_band[r["band"]] += 1
    print(f"[sample] 밴드 {len(by_band)}개 · 총 {len(selected)}곡 (seed={args.seed})")
    for band, cnt in sorted(by_band.items()):
        print(f"  {band:20s} {cnt}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["band", "idx", "song", "url"])
        w.writeheader()
        for r in selected:
            w.writerow({"band": r["band"], "idx": r["idx"], "song": r["song"], "url": r["url"]})
    print(f"[manifest] {MANIFEST.relative_to(ROOT)}")

    if args.download:
        from perceptual_features import ensure_full
        missing = ensure_full(selected, download=True)
        if missing:
            print(f"[다운로드 실패] {len(missing)}곡: {missing}")
        else:
            print("[다운로드] 전량 확보 완료")
    elif not args.dry_run:
        from perceptual_features import ensure_full
        missing = ensure_full(selected, download=False)
        if missing:
            print(f"[캐시 없음] {len(missing)}곡 — --download로 받으세요.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
