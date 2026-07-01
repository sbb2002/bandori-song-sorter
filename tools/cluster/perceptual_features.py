"""음원맵 축 재정의(v3) — 후보 지각 feature 추출·검증 파일럿.

설계 출처: docs/spec/audio-map-axes.md
- §2 x축: 보컬 음역(f0 95p) 70% + centroid 20% + rolloff 10%.
- §3 y축: 후보3(오디오 정서/mode) 우선 · 후보2(음색 거칢) 백업.
- §5 검증: 곡별 후보 feature 계산 → 사용자 손 라벨과 피어슨/스피어만 상관 →
           귀와 맞는 feature만 축으로 채택.
- §2.1 구간: 60초 클립은 마지막 후렴 정점을 놓침 → **전곡**에서 f0 상위 95p로 통계 포착.

이 모듈은 좌표·렌더를 만들지 않는다(그건 feature 채택 후). 오직 후보 feature를
곡별로 뽑아 cluster/axis_pilot_features.csv 로 남긴다 → 상관분석이 이를 소비.

f0 백엔드: librosa.pyin(mix). Demucs 보컬분리는 설치돼 있으면 자동으로 보컬 f0도 추가
(--vocal). CREPE/tensorflow 불필요.

사용:
    python tools/cluster/perceptual_features.py --pilot          # 워크시트 30곡
    python tools/cluster/perceptual_features.py --pilot --no-download   # 캐시만
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WORKSHEET = Path("cluster/axis_labels_worksheet.csv")
MANIFEST = Path("cluster/songs_top10.csv")
FULL_CACHE = Path("cluster/audio_full")     # 전곡 캐시(gitignore, 저작물). 60초 v2 캐시와 분리.
OUT = Path("cluster/axis_pilot_features.csv")
SR = 22050                                   # 스펙트럼·f0 공용(보컬 D5≈587Hz 여유). 48k 불필요.

# f0 탐색 범위: 옥타브-다운 오류 방지 위해 하한을 A2로. 여성 보컬 상단 여유 1000Hz.
F0_MIN, F0_MAX = 110.0, 1000.0

# Krumhansl-Schmuckler 조성 프로파일(장/단조 추정 → 정서 mode 후보3).
KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


# ── 음원 확보(전곡) ──────────────────────────────────────────
def _ffmpeg_location() -> list[str]:
    import os
    import shutil
    if shutil.which("ffmpeg"):
        return []
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    bindir = Path("cluster/_ffbin")
    bindir.mkdir(parents=True, exist_ok=True)
    tgt = bindir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not tgt.exists():
        shutil.copy(exe, tgt)
    return ["--ffmpeg-location", str(bindir)]


def ensure_full(rows: list[dict], download: bool) -> list[str]:
    """전곡(크롭 없음, 48kHz mono)을 audio_full/ 에 확보. 누락 idx 반환."""
    FULL_CACHE.mkdir(parents=True, exist_ok=True)
    ffloc = _ffmpeg_location() if download else []
    missing = []
    for r in rows:
        out = FULL_CACHE / f"{r['band']}__{int(r['idx']):03d}.wav"
        if out.exists() and out.stat().st_size > 1000:
            continue
        if not download:
            missing.append(r["idx"]); continue
        print(f"  [dl] {out.stem} …", flush=True)
        cmd = [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings",
               "-f", "bestaudio/best",                 # 구간 지정 없음 = 전곡
               "-x", "--audio-format", "wav",
               "--postprocessor-args", "ffmpeg:-ar 48000 -ac 1",
               *ffloc, "-o", str(FULL_CACHE / (out.stem + ".%(ext)s")), r["url"]]
        subprocess.run(cmd, capture_output=True, text=True)
        if not (out.exists() and out.stat().st_size > 1000):
            missing.append(r["idx"]); print(f"  [miss] {out.stem}", flush=True)
    return missing


# ── 보컬 분리(Demucs, spec §2) ───────────────────────────────
_demucs: dict = {}


def separate_vocals(path: str, out_sr: int = SR) -> np.ndarray | None:
    """Demucs htdemucs 로 보컬 stem 분리 → mono 파형(out_sr). 미설치/실패 시 None.

    믹스 f0 는 악기에 락되므로(진단 확인) 보컬 stem 에서 f0 를 재는 것이 spec §2 설계.
    CPU 전용. 네이티브 44.1kHz 로 로드해 분리 품질 보존 후 out_sr 로 리샘플.
    """
    import importlib.util
    if importlib.util.find_spec("demucs") is None:
        return None
    import librosa
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model
    if "model" not in _demucs:
        m = get_model("htdemucs"); m.cpu().eval()
        _demucs["model"] = m
    model = _demucs["model"]
    try:
        wav, _ = librosa.load(path, sr=model.samplerate, mono=False)
    except Exception as e:
        print(f"    demucs load fail: {e}", flush=True)
        return None
    if wav.ndim == 1:                       # mono 캐시 → stereo 복제(모델 2채널)
        wav = np.stack([wav, wav])
    ten = torch.tensor(wav, dtype=torch.float32).unsqueeze(0)
    ref = ten.mean(0)
    ten = (ten - ref.mean()) / (ref.std() + 1e-8)
    with torch.no_grad():
        src = apply_model(model, ten, device="cpu", progress=False, split=True)[0]
    src = src * (ref.std() + 1e-8) + ref.mean()
    voc = src[model.sources.index("vocals")].mean(0).cpu().numpy()   # stereo→mono
    if model.samplerate != out_sr:
        voc = librosa.resample(voc, orig_sr=model.samplerate, target_sr=out_sr)
    return voc.astype(float)


# ── 후보 feature ─────────────────────────────────────────────
def f0_p95(y: np.ndarray, sr: int) -> dict:
    """유성음 f0의 상위 백분위(spec §2.1). 옥타브 점프는 median filter로 완화.

    반환: p95/p90/median(Hz 및 semitone=MIDI), voiced 비율.
    주의: pyin의 vflag 만 사용(추가 vprob>0.5 는 mix에서 유성 프레임을 과하게 버려 버그).
    믹스 f0는 악기에 락되므로(진단), 보컬 분리 stem 을 넘겨 호출하는 것을 권장(spec §2).
    """
    import librosa
    from scipy.signal import medfilt
    f0, vflag, _vprob = librosa.pyin(y, fmin=F0_MIN, fmax=F0_MAX, sr=sr)
    keep = np.isfinite(f0) & vflag
    hz = f0[keep]
    if hz.size < 10:
        return {"f0_p95_hz": np.nan, "f0_p90_hz": np.nan, "f0_med_hz": np.nan,
                "f0_p95_semi": np.nan, "f0_med_semi": np.nan, "voiced_frac": 0.0}
    hz = medfilt(hz, kernel_size=5)          # 순간 옥타브 점프 제거
    to_semi = lambda h: 69 + 12 * np.log2(h / 440.0)
    return {
        "f0_p95_hz": float(np.percentile(hz, 95)),
        "f0_p90_hz": float(np.percentile(hz, 90)),
        "f0_med_hz": float(np.median(hz)),
        "f0_p95_semi": float(to_semi(np.percentile(hz, 95))),
        "f0_med_semi": float(to_semi(np.median(hz))),
        "voiced_frac": float(keep.mean()),
    }


def mode_valence(y: np.ndarray, sr: int) -> dict:
    """장/단조 추정(Krumhansl) → mode_score = 장조상관 − 단조상관(+면 밝음). 후보3."""
    import librosa
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    maj = [float(np.corrcoef(chroma, np.roll(KS_MAJ, i))[0, 1]) for i in range(12)]
    mnr = [float(np.corrcoef(chroma, np.roll(KS_MIN, i))[0, 1]) for i in range(12)]
    best_maj, best_min = max(maj), max(mnr)
    is_major = best_maj >= best_min
    key = (int(np.argmax(maj)) if is_major else int(np.argmax(mnr)))
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return {"mode_score": best_maj - best_min,
            "key": f"{names[key]}{'maj' if is_major else 'min'}"}


def timbre(y: np.ndarray, sr: int) -> dict:
    """밝기(centroid·rolloff, x축 보조) + 거칢 후보2(flux·flatness·contrast·zcr) + 보조."""
    import librosa
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    roll = librosa.feature.spectral_rolloff(y=y, sr=sr)
    flat = librosa.feature.spectral_flatness(y=y)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)
    rms = librosa.feature.rms(y=y)
    flux = librosa.onset.onset_strength(y=y, sr=sr)     # 스펙트럼 변화량(거칢/역동)
    tempo = float(np.atleast_1d(librosa.beat.tempo(y=y, sr=sr))[0])
    return {
        "centroid": float(cent.mean()), "rolloff": float(roll.mean()),
        "flatness": float(flat.mean()), "contrast": float(contrast.mean()),
        "flux": float(flux.mean()), "zcr": float(zcr.mean()),
        "rms": float(rms.mean()), "tempo": tempo,
    }


def features(path: str, use_vocal: bool = True) -> dict | None:
    import librosa
    try:
        y, sr = librosa.load(path, sr=SR, mono=True)
    except Exception as e:
        print(f"    load fail: {e}", flush=True)
        return None
    if len(y) < sr:
        return None
    d = {}
    mixf = f0_p95(y, sr)                              # 참고용 mix f0(악기 오염)
    d.update({f"mix_{k}": v for k, v in mixf.items()})
    voc = separate_vocals(path, SR) if use_vocal else None
    if voc is not None and len(voc) >= sr:
        d.update(f0_p95(voc, sr))                    # 보컬 f0 = canonical f0_*
        d["f0_src"] = "vocal"
    else:
        d.update(mixf); d["f0_src"] = "mix"          # 분리 실패 → mix fallback
    d.update(mode_valence(y, sr))
    d.update(timbre(y, sr))
    return d


# ── 파일럿 드라이버 ──────────────────────────────────────────
def load_rows(pilot: bool) -> list[dict]:
    src = WORKSHEET if pilot else MANIFEST
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    # 워크시트/매니페스트 모두 idx,band,song,url 보유
    return [{"idx": r["idx"], "band": r["band"], "song": r["song"], "url": r["url"]}
            for r in rows]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help="워크시트(30곡)만. 없으면 전체 매니페스트.")
    ap.add_argument("--no-download", action="store_true", help="캐시만 사용")
    ap.add_argument("--no-vocal", action="store_true",
                    help="Demucs 보컬분리 생략(믹스 f0만, 빠르나 악기 오염).")
    ap.add_argument("--limit", type=int, default=0, help="앞 N곡만(디버그).")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    rows = load_rows(args.pilot)
    if args.limit:
        rows = rows[:args.limit]
    vocal = not args.no_vocal
    print(f"대상 {len(rows)}곡 · SR={SR} · f0=pyin[{F0_MIN:.0f}-{F0_MAX:.0f}Hz] · "
          f"보컬분리={'demucs' if vocal else 'off'}", flush=True)
    miss = ensure_full(rows, download=not args.no_download)
    if miss:
        print(f"음원 누락 {len(miss)}곡 → 제외: {miss}", flush=True)

    recs = []
    cols = ["f0_src", "f0_p95_hz", "f0_p90_hz", "f0_med_hz", "f0_p95_semi", "f0_med_semi",
            "voiced_frac", "mix_f0_p95_hz", "mix_f0_med_hz", "mix_voiced_frac",
            "mode_score", "key", "centroid", "rolloff",
            "flatness", "contrast", "flux", "zcr", "rms", "tempo"]
    for i, r in enumerate(rows, 1):
        p = FULL_CACHE / f"{r['band']}__{int(r['idx']):03d}.wav"
        if not p.exists():
            continue
        print(f"[{i}/{len(rows)}] {r['band']}__{r['idx']} {r['song'][:24]}", flush=True)
        d = features(str(p), use_vocal=vocal)
        if d is None:
            continue
        recs.append({"idx": r["idx"], "band": r["band"], "song": r["song"], **d})

    # z-score 합성축(spec §2: f0 70% + centroid 20% + rolloff 10%) — 데이터셋 정규화 후.
    if recs:
        def z(key):
            v = np.array([rr[key] for rr in recs], dtype=float)
            m, s = np.nanmean(v), np.nanstd(v)
            return (v - m) / (s or 1.0)
        zf0, zc, zr = z("f0_p95_semi"), z("centroid"), z("rolloff")
        xcomp = 0.70 * np.nan_to_num(zf0) + 0.20 * zc + 0.10 * zr
        for rr, xv in zip(recs, xcomp):
            rr["x_f0_cent_roll"] = float(xv)
        cols.append("x_f0_cent_roll")

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["idx", "band", "song", *cols],
                           extrasaction="ignore")
        w.writeheader()
        for rr in recs:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in rr.items()})
    print(f"[OK] {args.out} — {len(recs)}곡 · 후보 {len(cols)}열", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
