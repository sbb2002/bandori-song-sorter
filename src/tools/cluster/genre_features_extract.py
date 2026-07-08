"""장르(밴드) 별 오디오 피처 재정의 — 1단계: 추출. side-project(Spotify) 후속.

Spotify의 acousticness/instrumentalness는 블랙박스라 값을 이식할 수 없음(side-project/
spotify-tracks-dataset/report.md 결론). 대신 phasec_features.py·perceptual_features.py가
이미 갖고 있는 신호처리 산출물(harmonic_ratio·flatness·voiced_frac 등)로 유사 개념을
직접 재정의해, 로컬에 캐시된 audio_full 전체(밴드=장르 대리)에서 분포를 관찰한다.

전 곡을 center 45s excerpt로 통일 계산(phasec_features.py의 harmonic_ratio 검증 패턴을
전체 feature로 확장 — 전체 로드 대비 ~5-6배 빠름).

환경: librosa/soundfile 필요(hummingbird conda env). matplotlib/pandas 불필요(이 단계는
stdlib csv만 사용) — 2단계(genre_features_analyze.py)는 반대로 pandas/matplotlib env(base)에서 실행.

기본 동작: `genre_features_sample.py`가 만든 `sample_manifest.csv`가 있으면 **그 목록에 있는
곡만** 처리(전곡 660이 로컬에 있어도 먼저 샘플만 검증하기 위함). 전곡을 처리하려면 `--all`.

사용:
  <hummingbird-python> src/tools/cluster/genre_features_extract.py           # manifest 있으면 샘플만
  <hummingbird-python> src/tools/cluster/genre_features_extract.py --all     # audio_full 전체
  <hummingbird-python> src/tools/cluster/genre_features_extract.py --limit 10   # 디버그
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from perceptual_features import timbre, mode_valence, f0_p95   # noqa: E402 (재사용)

AUDIO = ROOT / "src/content/cluster/audio_full"
SONGS_FULL = ROOT / "src/content/cluster/songs_full.csv"
OUTDIR = ROOT / "docs/working/report/genre-features"
OUT = OUTDIR / "song_features.csv"
MANIFEST = OUTDIR / "sample_manifest.csv"
PROGRESS = OUTDIR / "extract_progress.json"

SR = 22050
EXCERPT_SEC = 45.0   # phasec_features.py harmonic_ratio 검증 구간과 동일(전체 근사)

FIELDS = ["band", "idx", "song", "duration_s",
          "harmonic_ratio", "centroid", "rolloff", "flatness", "contrast", "flux", "zcr", "rms",
          "tempo_excerpt", "mode_score", "key", "voiced_frac_mix"]


def _center_excerpt(y: np.ndarray, sr: int, sec: float) -> np.ndarray:
    n = len(y)
    w = int(sec * sr)
    if n <= w:
        return y
    start = (n - w) // 2
    return y[start:start + w]


def compute(y48: np.ndarray, sr48: int) -> dict:
    import librosa
    y22 = librosa.resample(y48, orig_sr=sr48, target_sr=SR) if sr48 != SR else y48
    seg = _center_excerpt(y22, SR, EXCERPT_SEC)

    tb = timbre(seg, SR)
    mv = mode_valence(seg, SR)
    f0 = f0_p95(seg, SR)

    H, P = librosa.effects.hpss(seg)
    harmonic_ratio = float((H ** 2).sum() / ((H ** 2).sum() + (P ** 2).sum() + 1e-9))

    def r5(x):
        return "" if (isinstance(x, float) and x != x) else round(float(x), 5)

    return {
        "harmonic_ratio": r5(harmonic_ratio),
        "centroid": r5(tb["centroid"]), "rolloff": r5(tb["rolloff"]),
        "flatness": r5(tb["flatness"]), "contrast": r5(tb["contrast"]),
        "flux": r5(tb["flux"]), "zcr": r5(tb["zcr"]), "rms": r5(tb["rms"]),
        "tempo_excerpt": r5(tb["tempo"]),
        "mode_score": r5(mv["mode_score"]), "key": mv["key"],
        "voiced_frac_mix": r5(f0["voiced_frac"]),
    }


def load_songs_full() -> dict:
    rows = list(csv.DictReader(open(SONGS_FULL, encoding="utf-8")))
    return {(r["band"], r["idx"]): r["song"] for r in rows}


def load_done() -> set:
    done = set()
    if OUT.exists():
        for r in csv.DictReader(open(OUT, encoding="utf-8")):
            done.add((r["band"], r["idx"]))
    return done


def load_manifest_keys() -> set | None:
    """sample_manifest.csv가 있으면 (band,idx) 집합 반환, 없으면 None(=제한 없음)."""
    if not MANIFEST.exists():
        return None
    rows = csv.DictReader(open(MANIFEST, encoding="utf-8"))
    return {(r["band"], str(int(r["idx"]))) for r in rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="앞 N곡만(디버그)")
    ap.add_argument("--all", action="store_true", help="sample_manifest 무시하고 audio_full 전체 처리")
    args = ap.parse_args(argv)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    songs = load_songs_full()
    files = sorted(AUDIO.glob("*.wav"))

    manifest_keys = None if args.all else load_manifest_keys()
    if manifest_keys is not None:
        files = [p for p in files
                 if (p.stem.rsplit("__", 1)[0], str(int(p.stem.rsplit("__", 1)[1]))) in manifest_keys]
        print(f"[genre-features] sample_manifest.csv 적용 — {len(files)}/{len(manifest_keys)}곡 로컬에 존재", flush=True)

    if args.limit:
        files = files[:args.limit]
    done = load_done()

    new_file = not OUT.exists()
    fh = open(OUT, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new_file:
        w.writeheader()

    total = len(files)
    n_done = len(done)
    started = time.time()
    print(f"[genre-features] 전체 {total}곡 · 완료 {n_done}", flush=True)

    for i, p in enumerate(files, 1):
        stem = p.stem  # "{band}__{idx:03d}"
        band, idx_s = stem.rsplit("__", 1)
        idx = str(int(idx_s))
        key = (band, idx)
        if key in done:
            continue
        try:
            import soundfile as sf
            y48, sr48 = sf.read(str(p), dtype="float32")
            if y48.ndim > 1:
                y48 = y48.mean(axis=1)
            rec = {"band": band, "idx": idx, "song": songs.get(key, ""),
                   "duration_s": round(len(y48) / sr48, 1)}
            rec.update(compute(y48, sr48))
        except Exception as e:
            print(f"  ! {key} 추출 실패: {e}", flush=True)
            rec = {"band": band, "idx": idx, "song": songs.get(key, ""), "duration_s": ""}
            rec.update({k: "" for k in FIELDS if k not in rec})
        w.writerow(rec)
        fh.flush()
        n_done += 1
        elapsed = time.time() - started
        rate = (n_done - len(done)) / elapsed if elapsed > 0 else 0
        eta_min = (total - n_done) / rate / 60 if rate > 0 else float("nan")
        print(f"[{n_done}/{total}] {band}__{idx} {rec['song'][:24]} (ETA {eta_min:.1f}min)", flush=True)

    fh.close()
    print(f"[완료] {n_done}/{total} -> {OUT.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
