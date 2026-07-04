# -*- coding: utf-8 -*-
"""
에너지 기반 동적 subdivision용 intensity 곡선을 onset JSON에 추가.

full-mix 의 절대 음량(RMS dB)을 글로벌 앵커(DB_LO~DB_HI)로 정규화·평활 → 2Hz 다운샘플한
intensity 곡선을 onsets/<id>.json 의 "dyn" 필드로 저장한다. **곡별(per-song) 정규화가 아니라
글로벌**이라 곡 간 절대 energy 차이를 보존한다(Symbol I=시종 dense, 軌跡 1절=박).
렌더(_clOnsetTick)가 이 곡선을 임계로 잘라 순간 subdivision(박/8분/16분)을 고른다:
조용(intro/outro/브레이크다운)=박, 고조=8분/16분. 임계는 JS 상수라 재추출 없이 튜닝 가능.

demucs 불필요(librosa 만), 원본 audio_full 은 읽기 전용. onset JSON 만 갱신(dyn 추가).
사용: python build_dynamics.py --start 0 --count 165
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

import sys, csv, json, argparse, time
from pathlib import Path
import numpy as np
import librosa
from scipy.ndimage import uniform_filter1d

CLUSTER = Path(__file__).resolve().parents[2] / "content" / "cluster"
SR, HOP = 22050, 512
SMOOTH = 2.5      # 초, 구간 다이나믹스만(비트 단위 깜빡임 제거)
DYN_HZ = 2        # 저장 곡선 샘플레이트
DB_LO, DB_HI = -22.0, -7.0   # 글로벌 음량 앵커(카탈로그 분포 기준: 조용≲-15dB, 최대~-7dB)


def intensity_curve(path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)   # READ-ONLY
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0]
    db = librosa.amplitude_to_db(rms + 1e-9)             # 절대 음량(dB)
    w = max(1, int(SMOOTH * sr / HOP))
    db = uniform_filter1d(db, w)                         # 구간 평활
    inten = np.clip((db - DB_LO) / (DB_HI - DB_LO), 0.0, 1.0)   # 글로벌 절대음량 정규화(곡별 아님)
    # 2Hz 다운샘플(0.5s 블록 평균)
    step = max(1, int(round((sr / HOP) / DYN_HZ)))
    v = [round(float(inten[i:i + step].mean()), 3) for i in range(0, len(inten), step)]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(CLUSTER / "songs_full.csv"))
    ap.add_argument("--cache", default=str(CLUSTER / "audio_full"))
    ap.add_argument("--onsets", default=str(CLUSTER / "onsets"))
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=10**9)
    a = ap.parse_args()

    cache, onsets = Path(a.cache), Path(a.onsets)
    with open(a.manifest, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sub = rows[a.start:a.start + a.count]

    t0 = time.time()
    n_ok = n_skip = 0
    for row in sub:
        oid = f"{row['band']}__{int(row['idx']):03d}"
        wav, oj = cache / (oid + ".wav"), onsets / (oid + ".json")
        if not wav.is_file() or not oj.is_file():
            n_skip += 1
            continue
        try:
            v = intensity_curve(wav)
            d = json.loads(oj.read_text(encoding="utf-8"))
            d["dyn"] = {"hz": DYN_HZ, "v": v}
            oj.write_text(json.dumps(d, separators=(",", ":"), ensure_ascii=False),
                          encoding="utf-8")
        except Exception as e:
            print(f"[ERR] {oid}: {e}", flush=True)
            n_skip += 1
            continue
        n_ok += 1
        if n_ok % 20 == 0:
            print(f"  {n_ok} done ({(time.time()-t0)/n_ok:.1f}s/곡)", flush=True)
    print(f"[OK] dyn 추가 {n_ok}곡, {n_skip} skip, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
