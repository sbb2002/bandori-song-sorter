"""[실험] 드럼 스템 → beat 그리드 펄스 트랙(cluster/onsets/<band>__<idx>.json).

방법론 전환(onset 검출 → beat 그리드):
  1) librosa.beat.beat_track 으로 매 박 타임스탬프(실제 곡 pulse 위상에 정렬)
  2) 각 박(및 subdivision)의 볼륨(드럼 RMS)으로 펄스 프리셋(강/중/약) 결정
onset 검출의 plateau·놓침·과다 문제를 피하고, 규칙적 박자감을 준다.

subdivision 레벨(박/8분/16분)을 함께 산출 → 프론트 탭으로 청취하며 체감 박에 맞는 배속 선택.
각 이벤트: t 시각(초), v 볼륨(드럼 RMS 0~1 정규화). 드럼 분리는 separate_drums.py.

사용: python src/tools/cluster/build_beat_track.py <band> <idx> [--cache audio_drums]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import librosa

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SR = 22050
HOP = 256
SUBDIV = [("박", 1), ("8분", 2), ("16분", 4)]   # 그리드 세분화 레벨(탭)


def _subdivide(beats: np.ndarray, div: int) -> list[float]:
    if div <= 1:
        return [float(t) for t in beats]
    out = []
    for i in range(len(beats) - 1):
        a, b = beats[i], beats[i + 1]
        for j in range(div):
            out.append(float(a + (b - a) * j / div))
    out.append(float(beats[-1]))
    return out


def build(path: str) -> dict:
    y, sr = librosa.load(path, sr=SR, mono=True)
    dur = len(y) / sr
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP, units="time")
    tempo = float(np.atleast_1d(tempo)[0])

    rms = librosa.feature.rms(y=y, hop_length=HOP)[0]
    tgrid = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
    vmax = float(rms.max()) or 1.0

    def vol(t):
        return round(float(rms[min(int(np.searchsorted(tgrid, t)), len(rms) - 1)] / vmax), 3)

    levels = []
    for name, div in SUBDIV:
        grid = _subdivide(np.asarray(beats), div)
        events = [{"t": round(t, 2), "v": vol(t)} for t in grid]
        levels.append({"name": name, "div": div, "n": len(events), "events": events})

    return {"sr": SR, "dur": round(dur, 1), "tempo": round(tempo, 1), "levels": levels}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("band")
    ap.add_argument("idx", type=int)
    ap.add_argument("--cache", default="audio_drums")
    a = ap.parse_args(argv)

    wav = Path("src/content/cluster") / a.cache / f"{a.band}__{a.idx:03d}.wav"
    if not wav.exists():
        raise SystemExit(f"wav 없음: {wav} (separate_drums.py 로 드럼 분리 먼저)")
    doc = build(str(wav))

    out = Path("src/content/cluster/onsets")
    out.mkdir(exist_ok=True)
    p = out / f"{a.band}__{a.idx:03d}.json"
    json.dump(doc, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"[OK] {p} / {doc['dur']}s tempo≈{doc['tempo']}")
    for lv in doc["levels"]:
        print(f"    {lv['name']:4} (x{lv['div']}) → {lv['n']:4}개 (초당 {lv['n'] / max(doc['dur'], 1):.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
