"""Phase C — 요약 그림. 작업 5.

(A) 4 라벨축 × feature군(전용arousal·spectral·mode) 최고 |r| — arousal 전용군만 항상 낮음.
(B) energy 라벨: 전용arousal vs spectral 후보 |r| 막대(0.5 임계).
(C) 산점 2개: tempo_acf×tempo(측정템포 무용) · contrast×energy(스펙트럴 유효).
사용: python src/tools/cluster/phasec_plot.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "Malgun Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUTDIR = ROOT / "docs/working/report/emotion-axes"
WS = ROOT / "src/content/cluster/legacy/axis_labels_worksheet.csv"


def vid(u):
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


ARO = ["lufs", "lra", "rms_std", "crest", "tempo_acf", "pulse_clarity", "vbl", "onset_rate"]
SPEC = ["contrast", "centroid", "rolloff", "flatness"]
LABELS = {"rough_smooth1_rough5": "rough\n(Timbre)", "valence_dark1_bright5": "valence\n(Valence)",
          "energy_calm1_intense5": "energy\n(Arousal)", "tempo_slow1_fast5": "tempo\n(Arousal)"}


def main():
    res = json.load(open(OUTDIR / "phasec_correlation.json", encoding="utf-8"))
    feat = {r["url"]: r for r in csv.DictReader(open(OUTDIR / "phasec_features.csv", encoding="utf-8"))}
    ws = list(csv.DictReader(open(WS, encoding="utf-8")))

    def bestr(lab, group):
        return max((abs(res["labels"][lab][c]["pearson"]) for c in group if c in res["labels"][lab]), default=0)

    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.7))
    fig.suptitle("Phase C — 정식 오디오 feature × 손라벨(n=30) : Timbre·Valence 확정 / Arousal 독립축 불가",
                 fontsize=12.5, fontweight="bold")

    # (A) 라벨축 × feature군 최고 |r|
    labs = list(LABELS)
    x = np.arange(len(labs))
    aro = [bestr(l, ARO) for l in labs]
    spec = [bestr(l, SPEC) for l in labs]
    mode = [abs(res["labels"][l].get("mode_score", {}).get("pearson", 0)) for l in labs]
    ax[0].bar(x - 0.25, aro, 0.25, label="전용 arousal군", color="#e0663c")
    ax[0].bar(x, spec, 0.25, label="spectral군", color="#3ca0e0")
    ax[0].bar(x + 0.25, mode, 0.25, label="mode", color="#8a5cf6")
    ax[0].axhline(0.5, color="#ffb020", ls="--", lw=1.4, label="|r|=0.5")
    ax[0].set_xticks(x); ax[0].set_xticklabels([LABELS[l] for l in labs], fontsize=8.5)
    ax[0].set_ylabel("최고 |pearson r|"); ax[0].set_ylim(0, 0.9)
    ax[0].set_title("(A) 라벨축별 feature군 최고 |r|\n전용 arousal군은 어디서도 임계 미달")
    ax[0].legend(fontsize=7.5)

    # (B) energy 라벨: 전용 arousal vs spectral 후보 |r|
    lab = "energy_calm1_intense5"
    cands = ARO + SPEC
    rs = [abs(res["labels"][lab].get(c, {}).get("pearson", 0)) for c in cands]
    cols = ["#e0663c"] * len(ARO) + ["#3ca0e0"] * len(SPEC)
    xb = np.arange(len(cands))
    ax[1].bar(xb, rs, color=cols)
    ax[1].axhline(0.5, color="#ffb020", ls="--", lw=1.4)
    ax[1].set_xticks(xb); ax[1].set_xticklabels(cands, rotation=60, ha="right", fontsize=7.5)
    ax[1].set_ylabel("|r| vs energy 라벨"); ax[1].set_ylim(0, 0.8)
    ax[1].set_title("(B) energy = 스펙트럴(파랑)이 잡고\n전용 arousal(주황)은 못 잡음")

    # (C) 산점: tempo_acf×tempo(무용) / contrast×energy(유효)
    def scat(ax_, cand, lab_, title, color):
        xs, ys = [], []
        for r in ws:
            fr = feat.get(r["url"])
            if not fr:
                continue
            cv, lv = fval(fr.get(cand)), fval(r.get(lab_))
            if not (np.isnan(cv) or np.isnan(lv)):
                xs.append(cv); ys.append(lv)
        ax_.scatter(xs, ys, c=color, s=40, alpha=0.75, edgecolors="w", linewidths=0.5)
        if len(xs) > 2 and np.std(xs) > 0:
            m, b = np.polyfit(xs, ys, 1)
            xr = np.array([min(xs), max(xs)])
            ax_.plot(xr, m * xr + b, color="#ffb020", lw=1.5)
        rr = np.corrcoef(xs, ys)[0, 1]
        ax_.set_xlabel(cand); ax_.set_ylabel(lab_); ax_.set_title(f"{title} (r={rr:+.2f})", fontsize=9.5)

    # 두 산점을 한 축에 겹치지 않게 → ax[2]에 tempo, 별도 텍스트로 대비
    scat(ax[2], "tempo_acf", "tempo_slow1_fast5", "(C) 측정 템포 tempo_acf × 지각 tempo\n= 무관(측정≠지각)", "#e0663c")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = OUTDIR / "phasec_screening.png"
    plt.savefig(out, dpi=110)
    print(f"저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
