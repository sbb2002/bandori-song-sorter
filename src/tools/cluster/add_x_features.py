"""x축 재정의(v3-2차) 보조 feature 를 axis_pilot_features.csv 에 병합.

1차 x축(보컬 f0)이 검증 실패(docs/working/report/cluster-correlation) → 새 x 후보 축
(에너지/밀도·템포·어쿠스틱↔일렉트로닉) 상관 재검정용. 기존 feature(rms·flux·tempo)는
이미 있으므로, 부족한 것만 추가한다:
  - onset_rate     : 초당 onset 수(리듬 밀도, energy/density 후보)
  - harmonic_ratio : HPSS 하모닉/(하모닉+퍼커시브) 에너지비(어쿠스틱↔일렉트로닉 후보)
  - perc_ratio     : 1 − harmonic_ratio

Demucs 불필요(믹스에서 계산) → 캐시된 cluster/audio_full 로 빠르게. 멱등(재실행 안전).

사용: python src/tools/cluster/add_x_features.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FEATURES = Path("src/content/cluster/legacy/axis_pilot_features.csv")
FULL = Path("src/content/cluster/audio_full")
SR = 22050
NEW = ["onset_rate", "harmonic_ratio", "perc_ratio"]


def extra(path: str) -> dict:
    import librosa
    y, sr = librosa.load(path, sr=SR, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    onset_rate = len(onsets) / (len(y) / sr)
    y_h, y_p = librosa.effects.hpss(y)
    h, p = float(np.mean(y_h ** 2)), float(np.mean(y_p ** 2))
    hr = h / (h + p + 1e-12)
    return {"onset_rate": round(onset_rate, 4),
            "harmonic_ratio": round(hr, 4), "perc_ratio": round(1 - hr, 4)}


def main():
    rows = list(csv.DictReader(open(FEATURES, encoding="utf-8")))
    fields = list(rows[0].keys()) + [c for c in NEW if c not in rows[0]]
    for i, r in enumerate(rows, 1):
        p = FULL / f"{r['band']}__{int(r['idx']):03d}.wav"
        if not p.exists():
            print(f"[{i}] {r['band']}__{r['idx']} 캐시 없음 → skip", flush=True)
            continue
        print(f"[{i}/{len(rows)}] {r['band']}__{r['idx']}", flush=True)
        r.update(extra(str(p)))
    with open(FEATURES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"[OK] {FEATURES} — +{NEW}", flush=True)


if __name__ == "__main__":
    main()
