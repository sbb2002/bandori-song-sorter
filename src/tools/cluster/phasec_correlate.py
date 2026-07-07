"""Phase C — 정식 feature × 손라벨(4정서축) 상관 검정 + 합성 valence. 작업 5.

b0_correlate.py 를 일반화: vid 조인으로 phasec_features.csv 를 손라벨(rough/valence/energy/tempo,
n=30)과 상관. 각 후보의 Pearson/Spearman, 기존 축(x=contrast·y=mode) 독립성, 그리고 md 지침의
합성 valence(mode+centroid+harmonic) 회귀가 mode 단독을 넘는지 검정.

판정:
  Timbre  = rough 라벨과 |r|≥0.5 (contrast 재확인)
  Valence = valence 라벨과 |r|≥0.5 (mode 단독 vs 합성 비교)
  Arousal = energy/tempo 라벨과 |r|≥0.5 AND 기존 축과 독립(|r|≲0.4)

출력: phasec_correlation.txt · phasec_correlation.json
사용: python src/tools/cluster/phasec_correlate.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
WS = ROOT / "src/content/cluster/legacy/axis_labels_worksheet.csv"
FEAT = ROOT / "docs/working/report/emotion-axes/phasec_features.csv"
AMAP = ROOT / "src/content/cluster/audio_map.json"
OUTDIR = ROOT / "docs/working/report/emotion-axes"

AROUSAL = ["lufs", "lra", "rms_std", "crest", "tempo_acf", "pulse_clarity", "vbl", "onset_rate"]
VALENCE = ["mode_score", "harmonic_ratio", "centroid", "rolloff"]
TIMBRE = ["contrast", "flatness", "flux", "zcr", "rms"]
CANDIDATES = AROUSAL + VALENCE + TIMBRE + ["tempo_librosa"]

# 라벨축(축 소속 표기). 부호 기대는 |r| 기준이라 무관.
LABELS = {
    "rough_smooth1_rough5": "rough(매1↔거5) · Timbre",
    "valence_dark1_bright5": "valence(어1↔밝5) · Valence",
    "energy_calm1_intense5": "energy(잔1↔강5) · Arousal",
    "tempo_slow1_fast5": "tempo(느1↔빠5) · Arousal",
}


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


def corr(pairs):
    xs = [a for a, b in pairs]
    ys = [b for a, b in pairs]
    if len(xs) < 5 or np.std(xs) == 0 or np.std(ys) == 0:
        return None
    r, rp = pearsonr(xs, ys)
    rho, sp = spearmanr(xs, ys)
    return (r, rp, rho, sp, len(xs))


def main():
    ws = list(csv.DictReader(open(WS, encoding="utf-8")))
    feat = list(csv.DictReader(open(FEAT, encoding="utf-8")))
    amap = json.load(open(AMAP, encoding="utf-8"))
    ws_by_vid = {vid(r["url"]): r for r in ws}
    xy_by_vid = {vid(s["url"]): (s.get("x"), s.get("y")) for s in amap.get("songs", [])}

    # feature 행 → {후보..., 라벨..., x, y}  (vid 조인)
    joined = {}
    for r in feat:
        v = vid(r["url"])
        lab = ws_by_vid.get(v)
        if not lab:
            continue
        row = dict(r)
        for lc in LABELS:
            row[lc] = lab.get(lc, "")
        row["_x"], row["_y"] = xy_by_vid.get(v, (None, None))
        joined[v] = row

    results = {"labels": {}, "independence": {}, "composite_valence": {}, "verdict": {}}
    out = []

    def emit(s=""):
        out.append(s)
        print(s)

    emit("# Phase C — 정식 feature × 손라벨(4정서축) 상관")
    emit(f"조인 곡수: {len(joined)}")
    emit("")

    # 1) 라벨축별 상관(전 후보 랭킹)
    for lab, ltitle in LABELS.items():
        emit(f"## [{ltitle}]")
        emit(f"  {'후보':16} {'pearson r':>10} {'p':>7} {'spearman':>9} {'n':>4}")
        results["labels"][lab] = {}
        rows_lab = []
        for cand in CANDIDATES:
            pairs = [(fval(row.get(cand)), fval(row.get(lab))) for row in joined.values()]
            pairs = [(a, b) for a, b in pairs if not (np.isnan(a) or np.isnan(b))]
            res = corr(pairs)
            if res is None:
                continue
            r, rp, rho, sp, n = res
            rows_lab.append((cand, r, rp, rho, n))
            results["labels"][lab][cand] = {"pearson": round(r, 3), "p": round(rp, 4),
                                            "spearman": round(rho, 3), "n": n}
        rows_lab.sort(key=lambda t: -abs(t[1]))
        for cand, r, rp, rho, n in rows_lab:
            flag = "◀PASS" if (abs(r) >= 0.5 and rp < 0.05) else ""
            emit(f"  {cand:16} {r:>+10.3f} {rp:>7.3f} {rho:>+9.3f} {n:>4} {flag}")
        emit("")

    # 2) 독립성 — 후보 ↔ 기존 축(x=contrast, y=mode), 라벨 30곡 기준
    emit("## 독립성 — 후보 ↔ 기존 축 x(거칢)·y(밝음)  (arousal 후보는 |r|≲0.4 여야 새 축 자격)")
    emit(f"  {'후보':16} {'r(x)':>8} {'r(y)':>8}")
    for cand in AROUSAL + VALENCE:
        px = [(fval(row.get(cand)), fval(row.get("_x"))) for row in joined.values() if row.get("_x") is not None]
        py = [(fval(row.get(cand)), fval(row.get("_y"))) for row in joined.values() if row.get("_y") is not None]
        px = [(a, b) for a, b in px if not (np.isnan(a) or np.isnan(b))]
        py = [(a, b) for a, b in py if not (np.isnan(a) or np.isnan(b))]
        rx, ry = corr(px), corr(py)
        rxv = rx[0] if rx else float("nan")
        ryv = ry[0] if ry else float("nan")
        results["independence"][cand] = {"r_x": round(rxv, 3) if rxv == rxv else None,
                                         "r_y": round(ryv, 3) if ryv == ryv else None}
        emit(f"  {cand:16} {rxv:>+8.3f} {ryv:>+8.3f}")
    emit("")

    # 3) 합성 valence(mode+centroid+harmonic) 회귀 vs mode 단독
    emit("## 합성 Valence 검정 (md: mode+centroid+harmonicity) — valence 라벨과 R")
    comp_feats = ["mode_score", "centroid", "harmonic_ratio"]
    rowsv = [row for row in joined.values()
             if not np.isnan(fval(row.get("valence_dark1_bright5")))
             and all(not np.isnan(fval(row.get(c))) for c in comp_feats)]
    if len(rowsv) >= 8:
        y = np.array([fval(r["valence_dark1_bright5"]) for r in rowsv])
        X = np.array([[fval(r[c]) for c in comp_feats] for r in rowsv])
        Xz = (X - X.mean(0)) / (X.std(0) + 1e-9)
        A = np.column_stack([Xz, np.ones(len(y))])
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ coef
        R_comp = float(np.corrcoef(pred, y)[0, 1])
        r_mode = float(pearsonr([fval(r["mode_score"]) for r in rowsv], y)[0])
        results["composite_valence"] = {"R_composite": round(R_comp, 3), "r_mode_only": round(r_mode, 3),
                                        "coef_z": {c: round(float(w), 3) for c, w in zip(comp_feats, coef[:-1])},
                                        "n": len(rowsv)}
        emit(f"  mode 단독 r = {r_mode:+.3f}  →  합성(z) R = {R_comp:+.3f}  (n={len(rowsv)})")
        emit(f"  가중치(z): " + " · ".join(f"{c}={w:+.2f}" for c, w in zip(comp_feats, coef[:-1])))
        emit(f"  판정: 합성이 {'개선' if abs(R_comp) > abs(r_mode) + 0.05 else '미개선'}")
    emit("")

    # 4) 축별 판정
    emit("## 축별 판정")
    axis_map = {"Timbre": ("rough_smooth1_rough5", TIMBRE + ["contrast"]),
                "Valence": ("valence_dark1_bright5", VALENCE),
                "Arousal-energy": ("energy_calm1_intense5", AROUSAL),
                "Arousal-tempo": ("tempo_slow1_fast5", AROUSAL)}
    for axis, (lab, cands) in axis_map.items():
        best, br, bp = None, 0.0, 1.0
        for c in cands:
            e = results["labels"].get(lab, {}).get(c)
            if e and abs(e["pearson"]) > abs(br):
                best, br, bp = c, e["pearson"], e["p"]
        strong = abs(br) >= 0.5 and bp < 0.05
        ind = results["independence"].get(best, {})
        indep = True
        if axis.startswith("Arousal") and ind:
            rx, ry = ind.get("r_x"), ind.get("r_y")
            indep = (rx is None or abs(rx) <= 0.4) and (ry is None or abs(ry) <= 0.4)
        verdict = "PASS" if (strong and indep) else ("약함" if strong else "탈락")
        results["verdict"][axis] = {"best": best, "r": round(br, 3), "p": round(bp, 4),
                                    "independent": indep, "verdict": verdict}
        emit(f"  {axis:16} 최고 {str(best):14} r={br:+.3f}(p={bp:.3f}) "
             f"{'독립=' + ('O' if indep else 'X') if axis.startswith('Arousal') else ''} → {verdict}")
    emit("")
    emit("해석: Arousal PASS 있으면 새 축 성립(전곡 확대 근거). 없으면 valence 강화·timbre 확정만 취함.")

    def _native(o):
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        raise TypeError

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "phasec_correlation.txt").write_text("\n".join(out), encoding="utf-8")
    (OUTDIR / "phasec_correlation.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=_native), encoding="utf-8")
    print(f"\n저장: {(OUTDIR / 'phasec_correlation.txt').relative_to(ROOT)} · phasec_correlation.json")


if __name__ == "__main__":
    main()
