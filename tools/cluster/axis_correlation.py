"""음원맵 축 재정의(v3) — 후보 feature ↔ 사용자 손 라벨 상관분석 (spec §5).

입력:
  cluster/axis_labels_worksheet.csv  — 손 라벨(pitch/valence/rough, 1~5, 빈칸 허용)
  cluster/axis_pilot_features.csv     — perceptual_features.py 산출 후보 feature

출력(stdout): 라벨 축(pitch/valence/rough)별로 각 후보 feature 와의
  피어슨 r · 스피어만 ρ · p값 · n 을 |상관| 내림차순 정렬.
  → "귀와 맞는 feature만 축으로 채택"(spec §5-3)의 근거표.

사용:
    python tools/cluster/axis_correlation.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WORKSHEET = Path("cluster/axis_labels_worksheet.csv")
FEATURES = Path("cluster/axis_pilot_features.csv")

# 손 라벨 축 → (컬럼, 기대 부호 설명). spec §2·§3 + v3-2차 x축 재정의.
LABEL_AXES = {
    # y축(확정): 거침↔매끄러움 = spectral contrast.
    "rough (매1↔거5)":   ("rough_smooth1_rough5",  "y축(확정): contrast(-)·flatness(+)"),
    # x축 재후보(1차 pitch/f0 실패 → 개념 재정의). 상관 최고를 x축으로.
    "energy (잔1↔강5)":  ("energy_calm1_intense5", "x후보A: rms/flux/onset_rate 와 +상관 기대"),
    "tempo (느1↔빠5)":   ("tempo_slow1_fast5",     "x후보B: tempo 와 +상관 기대"),
    "acoustic (어쿠1↔일렉5)": ("acoustic1_electro5", "x후보C: harmonic_ratio(-)/flatness/perc_ratio"),
    # 참고(1차): valence·pitch. pitch 는 실패로 확인됨.
    "valence (어1↔밝5)": ("valence_dark1_bright5", "1차 참고: mode_score(+0.51)"),
    "pitch (저1↔고5)":   ("pitch_lo1_hi5",         "1차 실패: f0 무변별(r≈0)"),
}

# 각 라벨축에서 주목할 지정 후보(표에 ★ 표시).
SPEC_HINT = {
    "rough_smooth1_rough5": {"contrast", "flatness", "flux", "zcr"},
    "energy_calm1_intense5": {"rms", "flux", "onset_rate"},
    "tempo_slow1_fast5": {"tempo"},
    "acoustic1_electro5": {"harmonic_ratio", "perc_ratio", "flatness"},
    "valence_dark1_bright5": {"mode_score", "contrast"},
    "pitch_lo1_hi5": {"f0_p95_semi", "centroid", "rolloff"},
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[중단] 없음: {path}")
    return list(csv.DictReader(open(path, encoding="utf-8")))


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def main():
    labels = {int(r["idx"]): r for r in read_csv(WORKSHEET)}
    feats = read_csv(FEATURES)
    # 수치형 후보 컬럼 자동 감지(idx/band/song/key/f0_src 제외).
    skip = {"idx", "band", "song", "key", "f0_src"}
    feat_cols = [c for c in feats[0].keys() if c not in skip]

    from scipy.stats import pearsonr, spearmanr

    for title, (lab_col, note) in LABEL_AXES.items():
        # 라벨·feature 짝짓기(idx 기준, 양쪽 값 있는 것만).
        rows = []
        for fr in feats:
            i = int(fr["idx"])
            lv = to_float(labels.get(i, {}).get(lab_col, ""))
            if np.isnan(lv):
                continue
            rows.append((i, lv, fr))
        n_lab = len(rows)
        print(f"\n{'='*68}\n[{title}]  라벨 채워진 곡 {n_lab}개 · {note}\n{'='*68}")
        if n_lab < 5:
            print(f"  (라벨 {n_lab}개 — 최소 5개 필요, 상관 생략)")
            continue

        results = []
        for col in feat_cols:
            xs, ys = [], []
            for _i, lv, fr in rows:
                fv = to_float(fr.get(col, ""))
                if not np.isnan(fv):
                    xs.append(fv); ys.append(lv)
            if len(xs) < 5 or np.std(xs) == 0:
                continue
            r, rp = pearsonr(xs, ys)
            rho, sp = spearmanr(xs, ys)
            results.append((col, r, rp, rho, sp, len(xs)))

        results.sort(key=lambda t: -abs(t[1]))
        hint = SPEC_HINT.get(lab_col, set())
        print(f"  {'feature':20} {'pearson r':>10} {'p':>7} {'spearman':>9} {'p':>7} {'n':>4}")
        for col, r, rp, rho, sp, n in results:
            star = "★" if col in hint else " "
            print(f"{star} {col:20} {r:>+10.3f} {rp:>7.3f} {rho:>+9.3f} {sp:>7.3f} {n:>4}")

    print(f"\n{'-'*68}")
    print("해석: |r|≥0.5 & p<0.05 면 그 feature가 사용자 귀와 유의하게 정렬(채택 후보).")
    print("      ★ = spec 지정 후보. 부호가 기대와 반대면 방향만 뒤집어 사용.")


if __name__ == "__main__":
    main()
