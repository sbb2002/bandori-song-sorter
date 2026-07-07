"""Phase B0 — 스크리닝 요약 그림. 작업 5.

후보별 |pearson r|(energy·tempo) 막대(0.5 임계선) + 최강 후보 산점도 2개 → b0_screening.png.
onset 파생 feature 가 energy/tempo 지각축을 못 잡음을 한 장으로 보인다.
사용: python src/tools/cluster/b0_plot.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "Malgun Gothic"   # 한글 글리프(Windows)
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUTDIR = ROOT / "docs/working/report/cluster-energy-axis"
WS = ROOT / "src/content/cluster/legacy/axis_labels_worksheet.csv"
SF = ROOT / "src/content/cluster/songs_full.csv"
FEAT = OUTDIR / "onset_features.csv"


def vid(u: str) -> str:
    u = (u or "").strip()
    for p in ("https://youtu.be/", "https://www.youtube.com/watch?v=", "http://youtu.be/"):
        if u.startswith(p):
            u = u[len(p):]
    return u.split("&")[0].split("?")[0]


def fval(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def main():
    res = json.load(open(OUTDIR / "b0_correlation.json", encoding="utf-8"))
    ws = list(csv.DictReader(open(WS, encoding="utf-8")))
    sf = list(csv.DictReader(open(SF, encoding="utf-8")))
    feat = list(csv.DictReader(open(FEAT, encoding="utf-8")))
    vid2bi = {vid(r["url"]): (r["band"], r["idx"]) for r in sf}
    feat_by_bi = {(r["band"], r["idx"]): r for r in feat}

    cands = list(res["labels"]["energy_calm1_intense5"].keys())
    e_r = [abs(res["labels"]["energy_calm1_intense5"][c]["pearson"]) for c in cands]
    t_r = [abs(res["labels"]["tempo_slow1_fast5"][c]["pearson"]) for c in cands]

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    fig.suptitle("Phase B0 — onset 파생 후보 × energy/tempo 손라벨(n=30) 스크리닝 : 전멸",
                 fontsize=13, fontweight="bold")

    # (A) |r| 막대 + 0.5 임계선
    x = np.arange(len(cands))
    ax[0].bar(x - 0.2, e_r, 0.4, label="|r| vs energy", color="#e64c8c")
    ax[0].bar(x + 0.2, t_r, 0.4, label="|r| vs tempo", color="#66a0e0")
    ax[0].axhline(0.5, color="#ffb020", ls="--", lw=1.5, label="채택 임계 |r|=0.5")
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(cands, rotation=55, ha="right", fontsize=8)
    ax[0].set_ylabel("|pearson r|")
    ax[0].set_ylim(0, 0.6)
    ax[0].set_title("(A) 후보별 상관 강도 — 전부 임계 미만")
    ax[0].legend(fontsize=8)

    # 라벨 곡 데이터로 산점도
    def scatter(ax_, cand, lab, title):
        xs, ys = [], []
        for r in ws:
            bi = vid2bi.get(vid(r["url"]))
            if not bi or bi not in feat_by_bi:
                continue
            cv, lv = fval(feat_by_bi[bi].get(cand)), fval(r.get(lab))
            if not (np.isnan(cv) or np.isnan(lv)):
                xs.append(cv); ys.append(lv)
        ax_.scatter(xs, ys, c="#8a5cf6", s=42, alpha=0.75, edgecolors="w", linewidths=0.5)
        if len(xs) >= 2 and np.std(xs) > 0:
            m, b = np.polyfit(xs, ys, 1)
            xr = np.array([min(xs), max(xs)])
            ax_.plot(xr, m * xr + b, color="#ffb020", lw=1.5)
        ax_.set_xlabel(cand)
        ax_.set_ylabel(lab)
        ax_.set_title(title)

    scatter(ax[1], "dyn_std", "energy_calm1_intense5", "(B) 최강 energy 후보 dyn_std (r=-0.40)")
    scatter(ax[2], "pulse_bpm", "tempo_slow1_fast5", "(C) ACF 템포 pulse_bpm × tempo (r=+0.12)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out = OUTDIR / "b0_screening.png"
    plt.savefig(out, dpi=110)
    print(f"저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
