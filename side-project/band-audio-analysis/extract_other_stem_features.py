"""실험: Demucs "other" 스템(보컬/드럼/베이스 제외 = 기타·신스 등 화성악기)에서
피처를 재측정해, 믹스 전체 기반 측정과 비교한다.

세션 37 발견(mygo·ave_mujica가 acoustic 채널로 과다분류)의 원인 가설 —
"밝기군(centroid/rolloff/zcr/flatness)이 낮은 건 어두운 믹스(베이스·드럼 등) 때문이지 실제
화성악기 음색과 무관할 수 있다" — 를 검증한다. other 스템만 남기면 밝기군이 올라가서 acoustic
쏠림이 완화되는지 확인이 목적.

표본: 시간 비용(곡당 CPU 분리 ~3.5분) 때문에 전곡이 아니라 일부만 — mygo·ave_mujica(과다분류
발견 밴드) + morfonica(양성 대조군, 대조군도 other 스템에서 망가지지 않는지 확인).
분리한 WAV는 저장하지 않음(용량 문제, 재현 필요하면 재실행) — 피처만 CSV로 남긴다.

환경: hummingbird conda env(librosa/soundfile/torch/demucs).
사용: python side-project/band-audio-analysis/extract_other_stem_features.py
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import librosa
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/tools/cluster"))
from genre_features_extract import compute  # noqa: E402  (믹스 측정과 동일 함수 재사용)

AUDIO = ROOT / "src/content/cluster/audio_full"
SONGS_FULL = ROOT / "src/content/cluster/songs_full.csv"
MIX_CSV = ROOT / "side-project/genre-features/song_features_with_proxies.csv"
OUT = Path(__file__).resolve().parent / "other_stem_features.csv"

# (band, idx) 표본 — mygo·ave_mujica(과다분류 발견) + morfonica(양성 대조군)
SAMPLE = [
    ("mygo", 260), ("mygo", 261), ("mygo", 262), ("mygo", 263),
    ("ave_mujica", 72), ("ave_mujica", 73), ("ave_mujica", 74), ("ave_mujica", 75),
    ("morfonica", 180), ("morfonica", 181), ("morfonica", 182),
]

FEATURES = ["harmonic_ratio", "centroid", "rolloff", "flatness", "zcr", "flux", "contrast", "mode_score"]


def load_songs() -> dict:
    rows = list(csv.DictReader(open(SONGS_FULL, encoding="utf-8")))
    return {(r["band"], int(r["idx"])): r["song"] for r in rows}


def separate_other(model, sr: int, path: Path) -> np.ndarray:
    y, _ = librosa.load(str(path), sr=sr, mono=False)
    if y.ndim == 1:
        y = np.stack([y, y])
    wav = torch.tensor(y, dtype=torch.float32)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / (ref.std() + 1e-8)
    with torch.no_grad():
        sources = apply_model(model, wav[None], device="cpu", progress=False)[0]
    sources = sources * ref.std() + ref.mean()
    other = sources[model.sources.index("other")].mean(0).numpy()  # 스테레오→모노
    return other


def main() -> int:
    songs = load_songs()
    model = get_model("htdemucs")
    model.eval()
    sr = model.samplerate

    rows = []
    t_start = time.time()
    for i, (band, idx) in enumerate(SAMPLE, 1):
        inp = AUDIO / f"{band}__{idx:03d}.wav"
        if not inp.exists():
            print(f"[skip] {band}__{idx:03d} 없음")
            continue
        t0 = time.time()
        other = separate_other(model, sr, inp)
        feats = compute(other, sr)
        elapsed = time.time() - t0
        row = {"band": band, "idx": idx, "song": songs.get((band, idx), "?"), **feats}
        rows.append(row)
        print(f"[{i}/{len(SAMPLE)}] {band}__{idx:03d} ({elapsed:.0f}s) "
              f"harmonic_ratio={feats['harmonic_ratio']} centroid={feats['centroid']} "
              f"rolloff={feats['rolloff']}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["band", "idx", "song"] + FEATURES + ["tempo_excerpt", "voiced_frac_mix", "rms", "key"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"\n총 {len(rows)}곡, {time.time() - t_start:.0f}s 소요. 저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
