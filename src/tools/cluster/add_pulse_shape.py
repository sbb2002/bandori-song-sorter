"""곡별 재생 펄스 모양(shape)을 emoi-map(audio_map.json) songs[] 에 추가 — 음색 시그니처 시각화용.

EMOI-MAP 재생 펄스(박마다 별에서 퍼지는 파동)는 지금까지 전부 매끈한 원이었다. 세션 34에서
검증한 Idea A(펄스 "모양"=곡의 음색 시그니처, 데이터 지지 71%·PCA 지도 대안은 기각)를 실제
반영한다. 색(밴드 정체성)은 그대로 두고 모양만 4채널로 갈린다. 산식·데모는
side-project/genre-features/pulse-shapes-demo.html 및 memory pulse_signature_shapes 참고.

채널 산식(코퍼스 전체 z-score 기준, song_features_with_proxies.csv 전곡 660):
  acoustic = z(harmonic_ratio)
  bright   = mean(z(centroid), z(rolloff), z(zcr), z(flatness))
  shimmer  = z(flux)
  위 3채널 중 최댓값 채택. 최댓값 - 2등 < 0.4 면 neutral(뚜렷한 성분 없음, 매끈한 원 유지).

audio_map.json 의 songs[] 는 (band, song) 만 갖고 있으나 song 제목이 밴드 내에서 중복되는 곡이
2쌍 있어(raise_a_suilen/R・I・O・T, roselia/Neo-Aspect) song 제목만으로는 조인이 애매하다.
songs_full.csv 의 (band,song)->idx 매핑(add_energy.py 와 동일 패턴)을 거쳐 (band,idx) 로 CSV와
안전하게 조인한다.

사용:
  python src/tools/cluster/add_pulse_shape.py            # audio_map.json 에 shape 기록
  python src/tools/cluster/add_pulse_shape.py --dry-run  # 채널 분포 통계만 출력, 파일 미변경
이후 `python src/build.py` 로 index.html(window.CLUSTER_DATA) 재생성.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]          # src/tools/cluster/<file> → repo root
CLUSTER = ROOT / "src" / "content" / "cluster"
DEFAULT_MAP = CLUSTER / "audio_map.json"
DEFAULT_MANIFEST = CLUSTER / "songs_full.csv"
DEFAULT_FEATURES = ROOT / "side-project" / "genre-features" / "song_features_with_proxies.csv"

BRIGHT_COLS = ("centroid", "rolloff", "zcr", "flatness")
NEUTRAL_GAP = 0.4          # 최댓값-2등 이 이보다 작으면 neutral


def _load_idx_map(manifest: Path) -> dict:
    """(band, song) → idx (add_energy.py 와 동일 매핑, onset 파일명에도 재사용됨)."""
    m = {}
    with open(manifest, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[(row["band"], row["song"])] = int(row["idx"])
    return m


def _zscore(values: list) -> list:
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    sd = var ** 0.5
    if sd == 0:
        return [0.0] * n
    return [(v - mean) / sd for v in values]


def _load_channels(features: Path) -> dict:
    """(band, idx) → shape, features.csv 전체를 z-score 표준화해 채널 계산."""
    rows = list(csv.DictReader(open(features, encoding="utf-8")))
    if not rows:
        return {}

    z = {}
    for col in ("harmonic_ratio", "flux", *BRIGHT_COLS):
        z[col] = _zscore([float(r[col]) for r in rows])

    out = {}
    for i, r in enumerate(rows):
        acoustic = z["harmonic_ratio"][i]
        bright = sum(z[c][i] for c in BRIGHT_COLS) / len(BRIGHT_COLS)
        shimmer = z["flux"][i]
        ranked = sorted([("acoustic", acoustic), ("bright", bright), ("shimmer", shimmer)],
                         key=lambda kv: kv[1], reverse=True)
        top_name, top_val = ranked[0]
        _, second_val = ranked[1]
        shape = top_name if (top_val - second_val) >= NEUTRAL_GAP else "neutral"
        out[(r["band"], int(r["idx"]))] = shape
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="곡별 재생 펄스 shape(neutral/acoustic/bright/shimmer)을 audio_map.json songs 에 추가")
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    ap.add_argument("--dry-run", action="store_true", help="통계만 출력, 파일 미변경")
    args = ap.parse_args()

    with open(args.map, encoding="utf-8") as f:
        doc = json.load(f)
    songs = doc.get("songs") or []

    idx_map = _load_idx_map(args.manifest)
    channels = _load_channels(args.features)

    counts = Counter()
    miss = 0
    for s in songs:
        idx = idx_map.get((s["band"], s["song"]))
        shape = channels.get((s["band"], idx)) if idx is not None else None
        if shape is None:
            shape = "neutral"
            miss += 1
        s["shape"] = shape
        counts[shape] += 1

    total = len(songs)
    print(f"곡 {total} · 채널 매칭 {total - miss} · 폴백(neutral) {miss}")
    for name in ("neutral", "acoustic", "bright", "shimmer"):
        n = counts.get(name, 0)
        print(f"  {name:8s} {n:4d}  ({n / total * 100:.1f}%)")

    if args.dry_run:
        print("[dry-run] 파일 미변경.")
        return 0

    with open(args.map, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"저장: {args.map}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
