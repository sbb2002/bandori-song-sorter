"""장르(밴드) 별 오디오 피처 재정의 — 2단계: 분석·시각화. side-project(Spotify) 후속.

genre_features_extract.py(hummingbird env)가 만든 song_features.csv를 읽어:
  1. acousticness/instrumentalness/energy "재정의 프록시"를 z-score 합성으로 계산
  2. 밴드(=장르 대리) 별 바이올린 플롯 저장
  3. one-way ANOVA(eta squared)로 밴드 구분력 정량화

환경: pandas/matplotlib/scipy 필요(base env). librosa 불필요 — extract 단계와 env 분리
(hummingbird=librosa 有·pandas 無, base=pandas·matplotlib 有·librosa 無).

사용: python src/tools/cluster/genre_features_analyze.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
OUTDIR = ROOT / "docs/working/report/genre-features"
SRC = OUTDIR / "song_features.csv"

BASE_FEATURES = ["harmonic_ratio", "flatness", "contrast", "rms", "flux",
                 "voiced_frac_mix", "centroid", "rolloff", "zcr", "tempo_excerpt", "mode_score"]
PROXIES = ["acousticness_proxy", "instrumentalness_proxy", "energy_proxy"]


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / (s.std() or 1.0)


def build_proxies(df: pd.DataFrame) -> pd.DataFrame:
    df["acousticness_proxy"] = zscore(df["harmonic_ratio"]) - zscore(df["flatness"])
    df["instrumentalness_proxy"] = -zscore(df["voiced_frac_mix"])
    df["energy_proxy"] = zscore(df["rms"]) + zscore(df["contrast"]) + zscore(df["flux"])
    return df


def plot_violin_by_band(df: pd.DataFrame, feature: str) -> dict:
    grouped = df.groupby("band")[feature]
    order = grouped.median().sort_values().index.tolist()
    pairs = [(b, grouped.get_group(b).dropna().values) for b in order]
    pairs = [(b, d) for b, d in pairs if len(d) > 0]
    order = [b for b, _ in pairs]
    data = [d for _, d in pairs]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.violinplot(data, showmeans=True, showextrema=True)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(order, rotation=45, ha="right", fontsize=8)
    ax.set_title(f"{feature} distribution by band")
    ax.set_xlabel("band (sorted by median)")
    ax.set_ylabel(feature)
    ax.grid(axis="y", alpha=0.5)
    fig.tight_layout()
    fig.savefig(OUTDIR / f"{feature}_violin.png", dpi=120)
    plt.close(fig)

    f_stat, p_val = stats.f_oneway(*data)
    grand_mean = df[feature].mean()
    ss_between = sum(len(d) * (d.mean() - grand_mean) ** 2 for d in data)
    ss_total = ((df[feature] - grand_mean) ** 2).sum()
    eta_sq = ss_between / ss_total
    return {"feature": feature, "F": f_stat, "p": p_val, "eta_sq": eta_sq, "n_bands": len(order)}


def main():
    df = pd.read_csv(SRC)
    df = df.dropna(subset=BASE_FEATURES)
    df = build_proxies(df)

    results = []
    for feature in BASE_FEATURES + PROXIES:
        print(f"Plotting {feature}...")
        results.append(plot_violin_by_band(df, feature))

    summary = pd.DataFrame(results).sort_values("eta_sq", ascending=False)
    summary.to_csv(OUTDIR / "band_anova_summary.csv", index=False)
    df.to_csv(OUTDIR / "song_features_with_proxies.csv", index=False)

    print(f"\n곡 수: {len(df)} · 밴드 수: {df['band'].nunique()}")
    print("\n=== 밴드 구분력(eta squared, 정렬) ===")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
