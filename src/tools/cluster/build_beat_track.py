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


def perceptual_pulse(onset_env, sr, hop, base_tempo, tau=0.96, pmin=90.0, pmax=200.0):
    """지각 pulse rate 추정 — README 방안 A(ACF 옥타브 비율 규칙).

    onset-envelope 자기상관(ACF)은 느린 옥타브로 편향(자기상관 배음)돼 단독으론 항상
    절반 tempo 를 고른다. base(beat_track)와 그 ×2 의 ACF 를 비교해, 빠른 쪽이 느린 쪽의
    tau 배 이상이면 빠른 pulse 를 채택 — 이 **비율 자체가 '빠른 pulse 가 얼마나 두드러지나'
    = 지각 pulse 지표**다. tempo 가 같아도(afterglow·morfonica 둘 다 실제 185) 지각 pulse
    (afterglow 185 / morfonica 92)가 달라, 정확 tempo 로는 불가능한 구분을 해낸다.
    """
    acf = librosa.autocorrelate(onset_env)
    acf = acf / (acf[0] or 1.0)                       # lag0=1 정규화(표기 일관)

    def acf_at(bpm):
        lag = int(round((60.0 / bpm) * sr / hop))     # BPM → onset-frame lag
        return float(acf[lag]) if 1 <= lag < len(acf) else 0.0

    slow, fast = float(base_tempo), float(base_tempo) * 2
    a_slow, a_fast = acf_at(slow), acf_at(fast)
    ratio = (a_fast / a_slow) if a_slow > 0 else 0.0
    take_fast = ratio >= tau and pmin <= fast <= pmax
    pulse = fast if take_fast else slow
    return {"pulse_bpm": round(pulse, 1), "pulse_div": (2 if take_fast else 1),
            "slow": round(slow, 1), "fast": round(fast, 1),
            "acf_slow": round(a_slow, 3), "acf_fast": round(a_fast, 3),
            "ratio": round(ratio, 3), "tau": tau}


def build(path: str) -> dict:
    y, sr = librosa.load(path, sr=SR, mono=True)
    dur = len(y) / sr
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP, units="time")
    tempo = float(np.atleast_1d(tempo)[0])

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP)
    pulse = perceptual_pulse(onset_env, sr, HOP, tempo)     # 지각 pulse(방안 A)

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

    return {"sr": SR, "dur": round(dur, 1), "tempo": round(tempo, 1),
            "pulse": pulse, "levels": levels}


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
    pl = doc["pulse"]
    print(f"[OK] {p} / {doc['dur']}s tempo≈{doc['tempo']}")
    print(f"    지각 pulse ≈ {pl['pulse_bpm']} (div {pl['pulse_div']}={'박' if pl['pulse_div']==1 else '8분'}) "
          f"| ACF slow({pl['slow']})={pl['acf_slow']} fast({pl['fast']})={pl['acf_fast']} "
          f"ratio={pl['ratio']} (τ={pl['tau']})")
    for lv in doc["levels"]:
        print(f"    {lv['name']:4} (x{lv['div']}) → {lv['n']:4}개 (초당 {lv['n'] / max(doc['dur'], 1):.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
