"""곡별 에너지(energy)를 emoi-map(audio_map.json) songs[] 에 추가 — 별 시각화용.

EMOI-MAP 딥스페이스 시각화(작업 4)에서 각 곡 점을 "별"로 그릴 때, 별의 밝기·크기를
곡 에너지로 변조한다(에너지 큰 곡 = 밝은 별). 에너지 원천은 이미 존재하는 onset 트랙의
`dyn.v`(build_dynamics.py 산출, 2Hz 글로벌 절대음량 정규화 RMS intensity 0~1)다.
재분석·재다운로드 없이 onset JSON 만 읽어 집계 → 순수 파생값이라 오디오 스택 불필요.

집계·정규화:
  energy_raw = mean(dyn.v)                     # 곡 전체 평균 음량(intensity)
  energy     = 전곡 percentile rank → [0,1]     # 별 밝기 시각 분포 균등화(0=가장 조용, 1=가장 큼)
onset 없거나 dyn 결측 곡 = 0.5(중앙) 폴백.

곡↔onset 매핑은 build.py 와 동일: songs_full.csv 의 (band,song)→idx →
onsets/<band>__<idx:03d>.json.

사용:
  python src/tools/cluster/add_energy.py            # audio_map.json 에 energy 기록
  python src/tools/cluster/add_energy.py --dry-run  # 통계만 출력, 파일 미변경
이후 `python src/build.py` 로 index.html(window.CLUSTER_DATA) 재생성.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]          # src/tools/cluster/<file> → repo root
CLUSTER = ROOT / "src" / "content" / "cluster"
DEFAULT_MAP = CLUSTER / "audio_map.json"
DEFAULT_MANIFEST = CLUSTER / "songs_full.csv"
ONSET_DIR = CLUSTER / "onsets"


def _load_idx_map(manifest: Path) -> dict:
    """(band, song) → idx (onset 파일명 <band>__<idx:03d> 에 baked)."""
    m = {}
    with open(manifest, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[(row["band"], row["song"])] = int(row["idx"])
    return m


def _song_energy_raw(band: str, idx: int) -> float | None:
    """onsets/<band>__<idx>.json 의 dyn.v 평균. 파일/필드 없으면 None."""
    p = ONSET_DIR / f"{band}__{idx:03d}.json"
    if not p.is_file():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception:
        return None
    v = ((doc or {}).get("dyn") or {}).get("v") or []
    if not v:
        return None
    return sum(v) / len(v)


def _percentile_ranks(raws: list) -> list:
    """present raw 값을 [0,1] 균등 랭크로. None 은 0.5(중앙) 폴백. 3자리 반올림."""
    idxs = [i for i, r in enumerate(raws) if r is not None]
    out = [0.5] * len(raws)
    if len(idxs) <= 1:
        for i in idxs:
            out[i] = round(0.5, 3) if len(idxs) == 1 else out[i]
        return out
    order = sorted(idxs, key=lambda i: raws[i])            # 조용→큼
    denom = len(order) - 1
    for rank, i in enumerate(order):
        out[i] = round(rank / denom, 3)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="곡별 energy(0~1)를 audio_map.json songs 에 추가")
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--dry-run", action="store_true", help="통계만 출력, 파일 미변경")
    args = ap.parse_args()

    with open(args.map, encoding="utf-8") as f:
        doc = json.load(f)
    songs = doc.get("songs") or []
    idx_map = _load_idx_map(args.manifest)

    raws, miss = [], 0
    for s in songs:
        idx = idx_map.get((s["band"], s["song"]))
        r = _song_energy_raw(s["band"], idx) if idx is not None else None
        if r is None:
            miss += 1
        raws.append(r)

    energies = _percentile_ranks(raws)
    for s, e in zip(songs, energies):
        s["energy"] = e

    present = [r for r in raws if r is not None]
    print(f"곡 {len(songs)} · onset 반영 {len(present)} · 폴백(0.5) {miss}")
    if present:
        present.sort()
        print(f"  raw mean(dyn.v)  min {present[0]:.3f} / "
              f"median {present[len(present)//2]:.3f} / max {present[-1]:.3f}")
    es = sorted(energies)
    print(f"  energy(0~1)      min {es[0]:.3f} / median {es[len(es)//2]:.3f} / max {es[-1]:.3f}")

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
