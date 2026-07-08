import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats

from distribution import cleanse_dataset

dataset = pd.read_csv(r"side-project\spotify-tracks-dataset\data\dataset.csv")
dataset = cleanse_dataset(dataset)

OUT_DIR = Path(r"side-project\spotify-tracks-dataset\fig\violin-genre_vs_audiofeats")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1: low-level, 2: high-level(composite), 3: model-predicted
FEATURES = {
    "duration_ms": "1_low-level",
    "key": "1_low-level",
    "mode": "1_low-level",
    "loudness": "1_low-level",
    "tempo": "1_low-level",
    "time_signature": "1_low-level",
    "danceability": "2_composite",
    "energy": "2_composite",
    "speechiness": "2_composite",
    "acousticness": "2_composite",
    "instrumentalness": "2_composite",
    "liveness": "2_composite",
    "valence": "2_composite",
    "popularity": "3_model-predicted",
}


def plot_violin_by_genre(df: pd.DataFrame, feature: str, group: str) -> dict:
    """
    Plots feature distribution across all track_genre values as a violin plot,
    genres ordered by median feature value. Returns one-way ANOVA effect-size stats.
    """
    grouped = df.groupby("track_genre")[feature]
    order = grouped.median().sort_values().index.tolist()
    data = [grouped.get_group(g).values for g in order]

    fig, ax = plt.subplots(figsize=(30, 8))
    parts = ax.violinplot(data, showmeans=True, showextrema=True)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels(order, rotation=90, fontsize=6)
    ax.set_title(f"{feature} distribution by track_genre ({group})")
    ax.set_xlabel("track_genre (sorted by median)")
    ax.set_ylabel(feature)
    ax.grid(axis="y", alpha=0.5)
    fig.tight_layout()

    filepath = OUT_DIR / f"{group}_{feature}_violin.png"
    fig.savefig(filepath, dpi=120)
    plt.close(fig)

    # Effect size: how much of the variance in `feature` is explained by genre
    f_stat, p_val = stats.f_oneway(*data)
    grand_mean = df[feature].mean()
    ss_between = sum(len(d) * (d.mean() - grand_mean) ** 2 for d in data)
    ss_total = ((df[feature] - grand_mean) ** 2).sum()
    eta_sq = ss_between / ss_total

    return {"feature": feature, "group": group, "F": f_stat, "p": p_val, "eta_sq": eta_sq}


results = []
for feature, group in FEATURES.items():
    print(f"Plotting {feature} ({group})...")
    results.append(plot_violin_by_genre(dataset, feature, group))

summary = pd.DataFrame(results).sort_values("eta_sq", ascending=False)
print("\n=== Genre separation strength (eta squared, sorted) ===")
print(summary.to_string(index=False))
summary.to_csv(OUT_DIR / "_genre_anova_summary.csv", index=False)
