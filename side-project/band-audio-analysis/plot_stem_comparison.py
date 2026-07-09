"""stem_vs_mix_comparison.csv 시각화 — mix vs other-stem 밝기군·harmonic_ratio 비교.

사용: python side-project/band-audio-analysis/plot_stem_comparison.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTDIR = Path(__file__).resolve().parent
FIGDIR = OUTDIR / "fig"
CSV = OUTDIR / "stem_vs_mix_comparison.csv"

BAND_COLOR = {"mygo": "#7fd1e8", "ave_mujica": "#e64c8c", "morfonica": "#33aaff"}


def bar_pair(df, col_mix, col_other, title, ylabel, fname):
    labels = [f"{b}\n#{i}" for b, i in zip(df["band"], df["idx"])]
    x = range(len(df))
    fig, ax = plt.subplots(figsize=(12, 5))
    w = 0.38
    colors = [BAND_COLOR.get(b, "#888") for b in df["band"]]
    ax.bar([i - w / 2 for i in x], df[col_mix], width=w, label="mix (full)", color=colors, alpha=0.55)
    ax.bar([i + w / 2 for i in x], df[col_other], width=w, label="other stem (isolated)", color=colors, alpha=1.0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGDIR / fname, dpi=120)
    plt.close(fig)


def main() -> int:
    df = pd.read_csv(CSV)
    df = df.sort_values(["band", "idx"])
    bar_pair(df, "bright_mix", "bright_other",
              "Bright score (mean of centroid/rolloff/zcr/flatness, mixed scale) - mix vs other stem",
              "bright score (raw, compare within-song only)", "bright_mix_vs_other.png")
    bar_pair(df, "harmonic_ratio_mix", "harmonic_ratio_other",
              "harmonic_ratio - mix vs other stem", "harmonic_ratio", "harmonic_ratio_mix_vs_other.png")
    bar_pair(df, "centroid_mix", "centroid_other",
              "spectral centroid - mix vs other stem", "centroid (Hz)", "centroid_mix_vs_other.png")

    print("저장:", FIGDIR / "bright_mix_vs_other.png")
    print("저장:", FIGDIR / "harmonic_ratio_mix_vs_other.png")
    print("저장:", FIGDIR / "centroid_mix_vs_other.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
