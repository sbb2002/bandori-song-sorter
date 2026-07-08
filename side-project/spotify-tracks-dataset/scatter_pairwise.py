import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from itertools import product

from distribution import cleanse_dataset

dataset = pd.read_csv(r"side-project\spotify-tracks-dataset\data\dataset.csv")
dataset = cleanse_dataset(dataset)

OUT_DIR = Path(r"side-project\spotify-tracks-dataset\fig\scatter-pairwise")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 1: low-level, 2: composite, 3: model-predicted (metadata.md 변수 분류와 동일)
GROUP1 = ["duration_ms", "key", "mode", "loudness", "tempo", "time_signature"]
GROUP2 = ["danceability", "energy", "speechiness", "acousticness", "instrumentalness", "liveness", "valence"]
GROUP3 = ["popularity"]

PAIR_SETS = {
    "1x2": list(product(GROUP1, GROUP2)),
    "1x3": list(product(GROUP1, GROUP3)),
    "2x3": list(product(GROUP2, GROUP3)),
}


def overall_scatter(df: pd.DataFrame, x: str, y: str, tag: str) -> dict:
    """전체 데이터 하나의 산점도(hexbin, log count) + Pearson r."""
    r, p = stats.pearsonr(df[x], df[y])

    fig, ax = plt.subplots(figsize=(7, 6))
    hb = ax.hexbin(df[x], df[y], gridsize=50, cmap="viridis", bins="log", mincnt=1)
    fig.colorbar(hb, ax=ax, label="log10(count)")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"{x} vs {y}  (r={r:.3f}, p={p:.1e}, n={len(df)})")
    fig.tight_layout()

    filepath = OUT_DIR / f"{tag}_{x}_vs_{y}_overall.png"
    fig.savefig(filepath, dpi=120)
    plt.close(fig)

    return {"pair_group": tag, "x": x, "y": y, "r": r, "p": p, "n": len(df)}


def genre_correlation_bar(df: pd.DataFrame, x: str, y: str, tag: str, overall_r: float) -> pd.DataFrame:
    """장르별 Pearson r을 막대그래프로(장르는 r 기준 정렬) + 전체 r을 기준선으로 표시."""
    rows = []
    for genre, g in df.groupby("track_genre"):
        if len(g) < 5 or g[x].std() == 0 or g[y].std() == 0:
            continue
        r, p = stats.pearsonr(g[x], g[y])
        rows.append({"track_genre": genre, "r": r, "p": p, "n": len(g)})
    gdf = pd.DataFrame(rows).sort_values("r")

    fig, ax = plt.subplots(figsize=(30, 6))
    colors = ["crimson" if v < 0 else "steelblue" for v in gdf["r"]]
    ax.bar(range(len(gdf)), gdf["r"], color=colors, alpha=0.8)
    ax.axhline(overall_r, color="black", linestyle="--", linewidth=1, label=f"overall r={overall_r:.3f}")
    ax.set_xticks(range(len(gdf)))
    ax.set_xticklabels(gdf["track_genre"], rotation=90, fontsize=6)
    ax.set_ylabel("Pearson r")
    ax.set_title(f"{x} vs {y}: per-genre correlation (sorted)")
    ax.legend()
    ax.grid(axis="y", alpha=0.5)
    fig.tight_layout()

    filepath = OUT_DIR / f"{tag}_{x}_vs_{y}_by_genre.png"
    fig.savefig(filepath, dpi=120)
    plt.close(fig)

    return gdf


all_pairs = [(tag, x, y) for tag, pairs in PAIR_SETS.items() for x, y in pairs]

overall_results = []
genre_summary_rows = []

for tag, x, y in all_pairs:
    print(f"[{tag}] {x} vs {y}")
    res = overall_scatter(dataset, x, y, tag)
    overall_results.append(res)

    gdf = genre_correlation_bar(dataset, x, y, tag, res["r"])
    genre_summary_rows.append({
        "pair_group": tag, "x": x, "y": y,
        "overall_r": res["r"], "overall_p": res["p"],
        "genre_r_mean": gdf["r"].mean(),
        "genre_r_std": gdf["r"].std(),
        "genre_r_min": gdf["r"].min(),
        "genre_r_min_genre": gdf.loc[gdf["r"].idxmin(), "track_genre"],
        "genre_r_max": gdf["r"].max(),
        "genre_r_max_genre": gdf.loc[gdf["r"].idxmax(), "track_genre"],
        "n_sign_flip": int(((gdf["r"] > 0) != (res["r"] > 0)).sum()),
        "n_genres": len(gdf),
    })

overall_df = pd.DataFrame(overall_results)
overall_df["abs_r"] = overall_df["r"].abs()
overall_df = overall_df.sort_values("abs_r", ascending=False).drop(columns="abs_r")
overall_df.to_csv(OUT_DIR / "_overall_correlation_summary.csv", index=False)

genre_summary_df = pd.DataFrame(genre_summary_rows).sort_values("genre_r_std", ascending=False)
genre_summary_df.to_csv(OUT_DIR / "_genre_correlation_variability_summary.csv", index=False)

print("\n=== 전체 상관계수 |r| 정렬 (상위 15) ===")
print(overall_df.head(15).to_string(index=False))

print("\n=== 장르 간 상관계수 변동성(std) 정렬 (상위 15) ===")
print(genre_summary_df.head(15).to_string(index=False))
