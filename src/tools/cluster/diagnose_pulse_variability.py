# -*- coding: utf-8 -*-
"""
진단 게이트: 곡별 '구간간 pulse 변동성' 스캔 → section-local(방안 B) 대상 flag.

파이프라인(millsage 타당성 프로브 정식화):
  full-mix onset envelope → tempogram(국소 자기상관) → 프레임별 지배 tempo
  → 옥타브 접기([90,180)) → 6구간 중앙값의 std(= seg_spread).
  seg_spread 가 크면 곡 내에서 체감 pulse 가 구간마다 바뀐다는 뜻(변박/폴리메트릭)
  → 전역 단일 pulse(방안 A)로 불충분 → 방안 B 대상.
부가 지표: mean-tempogram 상위 2피크 비율(≈1.5 헤미올라 / ≈2.0 옥타브subdivision).

demucs 불필요(librosa 만), 원본 audio_full 은 읽기 전용(librosa.load).
검증 기준(프로브): millsage#179 spread=24.9(헤미올라1.5) vs poppin#375 spread=2.6(옥타브2.0).

사용:
  python diagnose_pulse_variability.py --out diag_all.csv
  python diagnose_pulse_variability.py --start 0 --count 165 --out diag/shard0.csv   # 샤딩
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

import sys, csv, argparse, time
from pathlib import Path
import numpy as np
import librosa

CLUSTER = Path(__file__).resolve().parents[2] / "content" / "cluster"   # src/content/cluster
SR, HOP, WIN = 22050, 512, 384
FOLD_LO, FOLD_HI = 90.0, 180.0
NSEG = 6
THRESH = 8.0   # spread_oct(octave%, circular) > THRESH → flag(방안 B 대상). 앵커로 재보정 예정.


def fold(b):
    """BPM 배열을 한 옥타브 [90,180) 로 접어 옥타브/배음 모호성 제거."""
    b = np.asarray(b, dtype=float)
    for _ in range(6):
        b = np.where(b < FOLD_LO, b * 2, b)
        b = np.where(b >= FOLD_HI, b / 2, b)
    return b


def analyze(path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)   # READ-ONLY
    dur = len(y) / sr
    oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    tg = librosa.feature.tempogram(onset_envelope=oenv, sr=sr,
                                   hop_length=HOP, win_length=WIN)
    freqs = librosa.tempo_frequencies(tg.shape[0], hop_length=HOP, sr=sr)
    band = (freqs >= 60) & (freqs <= 240)
    idx = np.where(band)[0]
    tgb, fb = tg[idx], freqs[idx]
    dom = fb[np.argmax(tgb, axis=0)]              # 프레임별 지배 tempo(raw)
    # 구간간 pulse 변동을 옥타브 '원(circular)' 위에서 측정(선형 std는 90 fold경계에서
    # 89↔92 를 92↔178 로 쪼개는 위양성 발생 → 옥타브는 순환량이므로 circular std 사용).
    ang = 2.0 * np.pi * (np.log2(dom) - np.floor(np.log2(dom)))   # 옥타브 내 각도
    seg_ang = []
    for s in np.array_split(ang, NSEG):
        seg_ang.append(np.arctan2(np.mean(np.sin(s)), np.mean(np.cos(s))))  # 구간 원평균 방향
    seg_ang = np.array(seg_ang)
    R = np.hypot(np.mean(np.cos(seg_ang)), np.mean(np.sin(seg_ang)))
    circ_std = float(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-9)))))        # radians
    seg_spread = circ_std / (2.0 * np.pi) * 100.0                          # octave% (0..~50)
    domf = fold(dom)                                                        # 표시용(접은 BPM)
    med = np.array([np.median(s) for s in np.array_split(domf, NSEG)])
    # 헤미올라 지표: 시간평균 tempogram 상위 2피크 비율
    prof = tg.mean(axis=1)
    order = np.argsort(prof)[::-1]
    picked = []
    for i in order:
        f = freqs[i]
        if f < 50 or f > 280:
            continue
        if all(abs(f - p) > 6 for p in picked):
            picked.append(f)
        if len(picked) >= 2:
            break
    ratio = float(max(picked) / min(picked)) if len(picked) >= 2 else float("nan")
    return dict(spread=seg_spread, ratio=ratio, fold_med=float(np.median(domf)),
                dur=dur, seg=[int(round(m)) for m in med])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(CLUSTER / "songs_full.csv"))
    ap.add_argument("--cache", default=str(CLUSTER / "audio_full"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--count", type=int, default=10**9)
    ap.add_argument("--thresh", type=float, default=THRESH)
    a = ap.parse_args()

    cache = Path(a.cache)
    with open(a.manifest, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    sub = rows[a.start:a.start + a.count]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    n_ok = n_skip = 0
    with open(a.out, "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["idx", "band", "song", "id", "spread_oct", "peak_ratio",
                    "fold_med", "dur", "flagged", "segs"])
        for row in sub:
            oid = f"{row['band']}__{int(row['idx']):03d}"
            wav = cache / (oid + ".wav")
            if not wav.is_file():
                n_skip += 1
                continue
            try:
                r = analyze(wav)
            except Exception as e:
                print(f"[ERR] {oid}: {e}", flush=True)
                n_skip += 1
                continue
            flagged = int(r["spread"] > a.thresh)
            w.writerow([row["idx"], row["band"], row["song"], oid,
                        f"{r['spread']:.2f}", f"{r['ratio']:.3f}",
                        f"{r['fold_med']:.1f}", f"{r['dur']:.1f}", flagged,
                        "|".join(map(str, r["seg"]))])
            n_ok += 1
            if n_ok % 20 == 0:
                el = time.time() - t0
                print(f"  {n_ok} done ({el/n_ok:.1f}s/곡)", flush=True)
    print(f"[OK] {a.out}: {n_ok}곡 분석, {n_skip} skip, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
