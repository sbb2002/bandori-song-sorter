"""Phase B0 — onset 파생 후보 ↔ n=28 손라벨(energy/tempo) 상관 검정. 작업 5.

axis_correlation.py 방법론 재사용. 조인은 vid(youtube id) 공간:
  worksheet(라벨) · onset_features.csv(후보) · audio_map.json(현행 축 x/y) 을 url→vid 로 묶는다.

판정(260708-final_comment.md §2):
  후보가 유망 = |r| ≥ 0.5 (p<0.05) with energy 또는 tempo 라벨
             AND 기존 축과 독립 (|r| ≲ 0.4 with x=contrast·y=mode).
  유망하면 Phase C 라벨 확대 확정검정 / 전멸이면 Phase C(오디오 필요 후보)로 직행.

출력: stdout 표 + b0_correlation.json(기계판) + b0_correlation.txt(표 캡처).
사용: python src/tools/cluster/b0_correlate.py
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
SF = ROOT / "src/content/cluster/songs_full.csv"
FEAT = ROOT / "side-project/emoi-map-emotion-axes/phase-b0/onset_features.csv"
AMAP = ROOT / "src/content/cluster/audio_map.json"
OUTDIR = ROOT / "side-project/emoi-map-emotion-axes/phase-b0"

CANDIDATES = ["e1_mean_dyn", "e2_lra_dyn", "e3_onset_rate", "onset_rate_fine",
              "dyn_std", "dyn_p90", "dyn_p10", "pulse_bpm", "tempo_json"]
CAND_DESC = {
    "e1_mean_dyn": "E1 평균 강도(mean dyn.v)",
    "e2_lra_dyn": "E2 강도레인지 p90-p10(LRA 근사)",
    "e3_onset_rate": "E3 온셋밀도(박레벨/s)",
    "onset_rate_fine": "온셋밀도(최密/s)",
    "dyn_std": "강도 표준편차",
    "dyn_p90": "강도 p90",
    "dyn_p10": "강도 p10",
    "pulse_bpm": "ACF 템포(pulse_bpm)",
    "tempo_json": "librosa 템포(참고)",
}
LABELS = {"energy_calm1_intense5": "energy(잔1↔강5)", "tempo_slow1_fast5": "tempo(느1↔빠5)"}
# 참고용(기존 축 정합 확인): rough=x(contrast), valence=y(mode)
REF_LABELS = {"rough_smooth1_rough5": "rough(매1↔거5)", "valence_dark1_bright5": "valence(어1↔밝5)"}


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
    ws = list(csv.DictReader(open(WS, encoding="utf-8")))
    sf = list(csv.DictReader(open(SF, encoding="utf-8")))
    feat = list(csv.DictReader(open(FEAT, encoding="utf-8")))
    amap = json.load(open(AMAP, encoding="utf-8"))

    vid2bi = {vid(r["url"]): (r["band"], r["idx"]) for r in sf}      # vid → (band,idx)
    feat_by_bi = {(r["band"], r["idx"]): r for r in feat}           # (band,idx) → 후보
    xy_by_vid = {vid(s["url"]): (s.get("x"), s.get("y")) for s in amap.get("songs", [])}

    # vid → {후보..., x, y, 라벨...}
    joined = {}
    for r in ws:
        v = vid(r["url"])
        bi = vid2bi.get(v)
        if not bi or bi not in feat_by_bi:
            continue
        row = dict(feat_by_bi[bi])
        row["_x"], row["_y"] = xy_by_vid.get(v, (None, None))
        for lab in {**LABELS, **REF_LABELS}:
            row[lab] = r.get(lab, "")
        joined[v] = row

    # 전곡(660) 후보↔x/y 독립성용 — (band,idx)→vid 역참조
    bi2vid = {(r["band"], r["idx"]): vid(r["url"]) for r in sf}
    all_rows = []
    for r in feat:
        v = bi2vid.get((r["band"], r["idx"]))
        x, y = xy_by_vid.get(v, (None, None))
        all_rows.append({**r, "_x": x, "_y": y})

    def corr(pairs):
        xs = [a for a, b in pairs]
        ys = [b for a, b in pairs]
        if len(xs) < 5 or np.std(xs) == 0 or np.std(ys) == 0:
            return None
        r, rp = pearsonr(xs, ys)
        rho, sp = spearmanr(xs, ys)
        return (r, rp, rho, sp, len(xs))

    results = {"labels": {}, "independence": {}, "verdict": {}}
    out = []

    def emit(s=""):
        out.append(s)
        print(s)

    emit("# Phase B0 — onset 파생 후보 × 손라벨(energy/tempo) 상관")
    emit(f"조인 곡수: 라벨 {len(joined)} · 전곡 feature {len(all_rows)}")
    emit("")

    # 1) 라벨 상관(energy/tempo + 참고 rough/valence)
    for lab, ltitle in {**LABELS, **REF_LABELS}.items():
        emit(f"## [{ltitle}]  라벨축")
        emit(f"  {'후보':22} {'pearson r':>10} {'p':>7} {'spearman':>9} {'p':>7} {'n':>4}")
        results["labels"][lab] = {}
        rows_lab = []
        for cand in CANDIDATES:
            pairs = []
            for v, row in joined.items():
                cv, lv = fval(row.get(cand)), fval(row.get(lab))
                if not (np.isnan(cv) or np.isnan(lv)):
                    pairs.append((cv, lv))
            res = corr(pairs)
            if res is None:
                continue
            r, rp, rho, sp, n = res
            rows_lab.append((cand, r, rp, rho, sp, n))
            results["labels"][lab][cand] = {"pearson": round(r, 3), "p": round(rp, 4),
                                            "spearman": round(rho, 3), "sp": round(sp, 4), "n": n}
        rows_lab.sort(key=lambda t: -abs(t[1]))
        for cand, r, rp, rho, sp, n in rows_lab:
            flag = "◀유망" if (abs(r) >= 0.5 and rp < 0.05) else ""
            emit(f"  {cand:22} {r:>+10.3f} {rp:>7.3f} {rho:>+9.3f} {sp:>7.3f} {n:>4} {flag}")
        emit("")

    # 2) 독립성(전곡 660: 후보 ↔ x=contrast, y=mode)
    emit("## 독립성 — 후보 ↔ 기존 축(전곡 660)")
    emit(f"  {'후보':22} {'r(x=거칢)':>10} {'r(y=밝음)':>10}   (|r|≲0.4 면 독립)")
    for cand in CANDIDATES:
        px = [(fval(r[cand]), fval(r["_x"])) for r in all_rows if r["_x"] is not None]
        py = [(fval(r[cand]), fval(r["_y"])) for r in all_rows if r["_y"] is not None]
        px = [(a, b) for a, b in px if not (np.isnan(a) or np.isnan(b))]
        py = [(a, b) for a, b in py if not (np.isnan(a) or np.isnan(b))]
        rx = corr(px)
        ry = corr(py)
        rxv = rx[0] if rx else float("nan")
        ryv = ry[0] if ry else float("nan")
        results["independence"][cand] = {"r_x": round(rxv, 3) if rxv == rxv else None,
                                         "r_y": round(ryv, 3) if ryv == ryv else None}
        emit(f"  {cand:22} {rxv:>+10.3f} {ryv:>+10.3f}")
    emit("")

    # 3) 판정
    emit("## 판정 (energy/tempo |r|≥0.5,p<0.05 & 기존축 독립 |r|≲0.4)")
    for cand in CANDIDATES:
        best_lab, best_r, best_p = None, 0.0, 1.0
        for lab in LABELS:
            e = results["labels"].get(lab, {}).get(cand)
            if e and abs(e["pearson"]) > abs(best_r):
                best_lab, best_r, best_p = lab, e["pearson"], e["p"]
        ind = results["independence"].get(cand, {})
        rx, ry = ind.get("r_x"), ind.get("r_y")
        indep = (rx is not None and abs(rx) <= 0.4) and (ry is not None and abs(ry) <= 0.4)
        strong = abs(best_r) >= 0.5 and best_p < 0.05
        verdict = "PASS" if (strong and indep) else ("약함" if strong else "탈락")
        results["verdict"][cand] = {"best_label": best_lab, "best_r": round(best_r, 3),
                                    "best_p": round(best_p, 4), "independent": indep, "verdict": verdict}
        lname = LABELS.get(best_lab, "-") if best_lab else "-"
        emit(f"  {cand:22} 최고 {lname:14} r={best_r:+.3f}(p={best_p:.3f}) "
             f"독립={'O' if indep else 'X'} → {verdict}")
    emit("")
    emit("해석: PASS 없으면 onset 파생만으로는 energy/tempo 축 부족 → Phase C(정식 LRA·tempogram, 오디오) 직행.")

    def _native(o):
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        raise TypeError(f"not serializable: {type(o)}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "b0_correlation.txt").write_text("\n".join(out), encoding="utf-8")
    (OUTDIR / "b0_correlation.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=_native), encoding="utf-8")
    print(f"\n저장: {(OUTDIR/'b0_correlation.txt').relative_to(ROOT)} · b0_correlation.json")


if __name__ == "__main__":
    main()
