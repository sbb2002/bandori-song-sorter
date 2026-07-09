"""other_stem_features.csv(스템 분리) vs song_features_with_proxies.csv(믹스 전체) 비교.

세션 37 가설 검증: other 스템(보컬/드럼/베이스 제외)에서 측정하면 mygo·ave_mujica의 밝기군이
mix 대비 올라가서 acoustic 쏠림이 완화되는지 확인. 표본이 작아(밴드당 3~4곡) 통계적 검정이
아니라 방향성(라벨=상승/하락) 확인 수준.

환경: base env(pandas만).
사용: python side-project/band-audio-analysis/compare_stem_vs_mix.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = Path(__file__).resolve().parent
MIX_CSV = ROOT / "side-project/genre-features/song_features_with_proxies.csv"
OTHER_CSV = OUTDIR / "other_stem_features.csv"

BRIGHT_COLS = ["centroid", "rolloff", "zcr", "flatness"]


def main() -> int:
    mix = pd.read_csv(MIX_CSV)
    other = pd.read_csv(OTHER_CSV)

    merged = other.merge(mix, on=["band", "idx"], suffixes=("_other", "_mix"))
    if merged.empty:
        print("병합 결과 0행 — other_stem_features.csv가 아직 없거나 idx가 안 맞습니다.")
        return 1

    cols = ["harmonic_ratio"] + BRIGHT_COLS
    print(f"{'band':14}{'idx':>5}  {'song':30}", end="")
    for c in cols:
        print(f"{c+'(mix)':>16}{c+'(other)':>16}{'Δ':>10}", end="")
    print()

    rows = []
    for _, r in merged.iterrows():
        song = str(r["song_mix"])[:28]
        print(f"{r['band']:14}{int(r['idx']):>5}  {song:30}", end="")
        rec = {"band": r["band"], "idx": r["idx"], "song": song}
        for c in cols:
            vm, vo = r[f"{c}_mix"], r[f"{c}_other"]
            delta = vo - vm
            print(f"{vm:>16.4f}{vo:>16.4f}{delta:>+10.4f}", end="")
            rec[f"{c}_mix"], rec[f"{c}_other"], rec[f"{c}_delta"] = vm, vo, delta
        print()
        rows.append(rec)

    df = pd.DataFrame(rows)
    print("\n=== 밝기군 4개 평균 델타(other - mix), 밴드별 ===")
    df["bright_mix"] = df[[f"{c}_mix" for c in BRIGHT_COLS]].mean(axis=1)
    df["bright_other"] = df[[f"{c}_other" for c in BRIGHT_COLS]].mean(axis=1)
    df["bright_delta"] = df["bright_other"] - df["bright_mix"]
    print(df.groupby("band")[["bright_mix", "bright_other", "bright_delta"]].mean().round(3).to_string())

    print("\n=== harmonic_ratio 밴드별 평균 델타 ===")
    df["hr_delta"] = df["harmonic_ratio_other"] - df["harmonic_ratio_mix"]
    print(df.groupby("band")[["harmonic_ratio_mix", "harmonic_ratio_other", "hr_delta"]].mean().round(3).to_string())

    df.to_csv(OUTDIR / "stem_vs_mix_comparison.csv", index=False)
    print(f"\n저장: {OUTDIR / 'stem_vs_mix_comparison.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
