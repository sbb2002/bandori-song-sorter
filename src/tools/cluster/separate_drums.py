"""[실험] demucs 로 드럼 스템 분리 → audio_drums/<band>__<idx>.wav.

torchaudio.load(→torchcodec 요구) 회피: 오디오를 librosa 로 로드해 텐서로 직접 apply_model.
드럼 onset 추출(build_onset_track.py --cache audio_drums)용 입력을 만든다. CPU 추론이라 곡당 수 분.

사용: python src/tools/cluster/separate_drums.py <band> <idx> [--cache audio_full]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def separate(inp: str, outp: str, name: str = "htdemucs") -> None:
    model = get_model(name)
    model.eval()
    sr = model.samplerate
    y, _ = librosa.load(inp, sr=sr, mono=False)     # torchaudio 우회
    if y.ndim == 1:
        y = np.stack([y, y])                        # mono → stereo
    wav = torch.tensor(y, dtype=torch.float32)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / (ref.std() + 1e-8)   # demucs 표준 정규화
    with torch.no_grad():
        sources = apply_model(model, wav[None], device="cpu", progress=True)[0]
    sources = sources * ref.std() + ref.mean()
    drums = sources[model.sources.index("drums")].mean(0).numpy()   # 스테레오→모노
    Path(outp).parent.mkdir(parents=True, exist_ok=True)
    sf.write(outp, drums, sr)
    print(f"[OK] drums -> {outp}  (sources={model.sources}, sr={sr})")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("band")
    ap.add_argument("idx", type=int)
    ap.add_argument("--cache", default="audio_full")
    ap.add_argument("--out-cache", default="audio_drums")
    a = ap.parse_args(argv)

    base = Path("src/content/cluster")
    inp = base / a.cache / f"{a.band}__{a.idx:03d}.wav"
    outp = base / a.out_cache / f"{a.band}__{a.idx:03d}.wav"
    if not inp.exists():
        raise SystemExit(f"입력 없음: {inp}")
    separate(str(inp), str(outp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
