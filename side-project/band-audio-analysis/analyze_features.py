"""EMOI-MAP이 쓰는 7항목(실제 컬럼 10개) 밴드별 분포 분석 — 세션 36 인계.

ave_mujica(헤비메탈 성향)가 펄스 acoustic 채널로 48% 과다분류된 이상을 발견한 뒤(세션 36),
"채널 판정이 밴드 특성과 어긋나는" 사례가 다른 밴드에도 있는지 확인하기 위한 분석.
오디오 재추출 불필요 — 이미 레포에 커밋된 두 산출물만 읽는다:
  - side-project/genre-features/song_features_with_proxies.csv (전곡 660, 원시 피처)
  - src/content/cluster/audio_map.json (energy·bpm·펄스 shape, add_energy.py/add_pulse_shape.py 산출)

환경: pandas/matplotlib/scipy만 필요(base env, librosa 불필요) — genre_features_analyze.py와 동일.

사용: python side-project/band-audio-analysis/analyze_features.py
"""
from __future__ import annotations

import csv
import json
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

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = Path(__file__).resolve().parent
FIGDIR = OUTDIR / "fig"
FEATURES_CSV = ROOT / "side-project/genre-features/song_features_with_proxies.csv"
AUDIO_MAP = ROOT / "src/content/cluster/audio_map.json"
SONGS_FULL = ROOT / "src/content/cluster/songs_full.csv"

# EMOI-MAP이 실제로 쓰는 7항목(밝기군은 4개 서브피처로 풀어 총 10개 raw 컬럼).
FEATURES = ["contrast", "mode_score", "harmonic_ratio",
            "centroid", "rolloff", "zcr", "flatness", "flux",
            "energy", "bpm"]
SHAPES = ["neutral", "acoustic", "bright", "shimmer"]

# 사용자 관찰(사전 지식, 정답 아님) — 분포가 이 기대와 어긋나는지 확인용 참고 라벨.
BAND_CHARACTER = {
    "roselia": "심포닉메탈/하드록",
    "raise_a_suilen": "하드록/일렉트로닉",
    "ave_mujica": "고딕메탈",
    "morfonica": "바이올린/현악 편성",
    "pastel_palettes": "팝",
    "poppin_party": "팝펑크",
    "afterglow": "락",
    "hello_happy_world": "팝",
    "mygo": "얼터너티브락",
    "mugendai_mutype": "팝",
    "ikka_dumb_rock": "락",
    "millsage": "미상(n=1)",
    "various_artists": "혼성(장르 대리변수 아님)",
}


def load_idx_map() -> dict:
    m = {}
    with open(SONGS_FULL, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[(row["band"], row["song"])] = int(row["idx"])
    return m


def build_dataframe() -> pd.DataFrame:
    feat_df = pd.read_csv(FEATURES_CSV)
    feat_df = feat_df.set_index(["band", "idx"])

    idx_map = load_idx_map()
    doc = json.load(open(AUDIO_MAP, encoding="utf-8"))
    rows = []
    for s in doc["songs"]:
        idx = idx_map.get((s["band"], s["song"]))
        if idx is None:
            continue
        rows.append({"band": s["band"], "idx": idx, "energy": s.get("energy"),
                     "bpm": s.get("bpm"), "shape": s.get("shape")})
    map_df = pd.DataFrame(rows).set_index(["band", "idx"])

    df = feat_df.join(map_df, how="inner")
    return df.reset_index()


def plot_violin_by_band(df: pd.DataFrame, feature: str) -> None:
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
    fig.savefig(FIGDIR / f"{feature}_violin.png", dpi=120)
    plt.close(fig)


def shape_distribution(df: pd.DataFrame) -> pd.DataFrame:
    ct = pd.crosstab(df["band"], df["shape"], normalize="index") * 100
    for s in SHAPES:
        if s not in ct.columns:
            ct[s] = 0.0
    ct = ct[SHAPES].round(1)
    ct["n"] = df.groupby("band").size()
    ct["character"] = [BAND_CHARACTER.get(b, "?") for b in ct.index]
    return ct.sort_values("acoustic", ascending=False)


def main() -> int:
    FIGDIR.mkdir(exist_ok=True)
    df = build_dataframe()
    print(f"조인 결과: {len(df)}곡 (원본 CSV 660 대비 매칭 {len(df)}건)")

    for feature in FEATURES:
        plot_violin_by_band(df, feature)
        print(f"  saved {feature}_violin.png")

    shape_ct = shape_distribution(df)
    shape_ct.to_csv(OUTDIR / "shape_distribution_by_band.csv")
    print("\n=== 밴드별 펄스 채널 분포(%) — acoustic 내림차순 ===")
    print(shape_ct.to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
