"""Phase C — 정식 오디오 feature 추출 (Timbre·Valence·Arousal). 작업 5.

audio_full 원본(48kHz WAV)에서 lean 추출 — perceptual_features 의 timbre()/mode_valence() 를
재사용하되 느린 demucs 보컬분리·pyin f0 는 건너뛴다. Russell/Thayer V-A 원형모델 + ESTM 논문
(docs/ref) 단서로 3정서 축 후보를 뽑는다:

  [Arousal 후보] lufs(정규화 확인됨=약함) · lra(단기 loudness 스프레드, 정규화 불변) ·
                 rms_std/crest(강도 변동, PDF "강도의 변화") · tempo_acf/pulse_clarity(tempogram) ·
                 vbl(비트간격 분산, PDF 식4 VBL) · onset_rate
  [Valence 후보] mode_score(장/단조) · harmonic_ratio(HPSS 협화도, 중앙45s excerpt≈전체) · centroid · rolloff
  [Timbre 후보] contrast · flatness · flux · zcr · rms

후속 phasec_correlate.py 가 손라벨(rough/valence/energy/tempo, n=30)과 상관검정.

진행/제어(사용자 요청): phasec_progress.json(곡마다 진행률·ETA·마지막 곡),
  phasec_control.json{command:pause} 협조적 중단, phasec_features.csv 체크포인트(재실행 skip=재개).

사용:
  python src/tools/cluster/phasec_features.py --labeled   # 손라벨 30곡(테스트, 기본)
  python src/tools/cluster/phasec_features.py --full       # 전곡 660(통과 후)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import pyloudnorm as pyln

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from perceptual_features import timbre, mode_valence   # noqa: E402  (재사용)

WORKSHEET = ROOT / "src/content/cluster/legacy/axis_labels_worksheet.csv"
SONGS_FULL = ROOT / "src/content/cluster/songs_full.csv"
AUDIO = ROOT / "src/content/cluster/audio_full"
OUTDIR = ROOT / "docs/working/report/emotion-axes"
FEATURES = OUTDIR / "phasec_features.csv"
PROGRESS = OUTDIR / "phasec_progress.json"
CONTROL = OUTDIR / "phasec_control.json"

SR22 = 22050   # 스펙트럼·템포 표준(48k 원본은 LUFS 전용)

FIELDS = ["idx", "band", "song", "url",
          # arousal
          "lufs", "lra", "rms_std", "crest", "tempo_acf", "pulse_clarity", "vbl", "onset_rate",
          # valence
          "mode_score", "key", "harmonic_ratio", "centroid", "rolloff",
          # timbre
          "contrast", "flatness", "flux", "zcr", "rms", "tempo_librosa",
          "has_audio"]


def _vid(u: str) -> str:
    u = (u or "").strip()
    for p in ("https://youtu.be/", "https://www.youtube.com/watch?v=", "http://youtu.be/"):
        if u.startswith(p):
            u = u[len(p):]
    return u.split("&")[0].split("?")[0]


def _short_term_lufs(y, sr, meter, win=3.0, hop=1.0):
    """단기 loudness 시퀀스(3s 창, 1s hop) → LRA 근사(p95-p10)용."""
    w, h = int(win * sr), int(hop * sr)
    vals = []
    for i in range(0, max(1, len(y) - w), h):
        try:
            L = meter.integrated_loudness(y[i:i + w])
            if np.isfinite(L):
                vals.append(L)
        except Exception:
            pass
    return np.asarray(vals)


def compute(y48: np.ndarray, sr48: int) -> dict:
    import librosa
    y22 = librosa.resample(y48, orig_sr=sr48, target_sr=SR22) if sr48 != SR22 else y48

    tb = timbre(y22, SR22)            # centroid,rolloff,flatness,contrast,flux,zcr,rms,tempo
    mv = mode_valence(y22, SR22)      # mode_score,key

    meter = pyln.Meter(sr48)
    lufs = float(meter.integrated_loudness(y48))
    st = _short_term_lufs(y48, sr48, meter)
    lra = float(np.percentile(st, 95) - np.percentile(st, 10)) if st.size > 3 else float("nan")

    rms_env = librosa.feature.rms(y=y22)[0]
    rms_std = float((20 * np.log10(rms_env + 1e-9)).std())    # dB 변동(강도의 변화)
    peak = float(np.abs(y22).max())
    rms_all = float(np.sqrt((y22 ** 2).mean()))
    crest = float(20 * np.log10((peak + 1e-9) / (rms_all + 1e-9)))

    oenv = librosa.onset.onset_strength(y=y22, sr=SR22)
    tg = librosa.feature.tempogram(onset_envelope=oenv, sr=SR22)
    ac = np.mean(tg, axis=1)
    tempo_acf = float(np.atleast_1d(librosa.feature.tempo(onset_envelope=oenv, sr=SR22, aggregate=np.median))[0])
    pulse_clarity = float(ac.max() / (ac.mean() + 1e-9))
    _, beats = librosa.beat.beat_track(onset_envelope=oenv, sr=SR22)
    ibi = np.diff(librosa.frames_to_time(beats, sr=SR22))
    vbl = float(np.var(ibi)) if ibi.size > 1 else float("nan")
    onset_rate = float(len(librosa.onset.onset_detect(onset_envelope=oenv, sr=SR22)) / (len(y22) / SR22))

    # harmonic_ratio: 중앙 45s excerpt HPSS (전체 근사·6배 빠름, 검증됨)
    n = len(y22); w = int(45 * SR22)
    seg = y22[(n - w) // 2:(n - w) // 2 + w] if n > w else y22
    H, P = librosa.effects.hpss(seg)
    hr = float((H ** 2).sum() / ((H ** 2).sum() + (P ** 2).sum() + 1e-9))

    def r5(x):
        return "" if (isinstance(x, float) and x != x) else (round(float(x), 5) if isinstance(x, (int, float)) else x)

    return {
        "lufs": r5(lufs), "lra": r5(lra), "rms_std": r5(rms_std), "crest": r5(crest),
        "tempo_acf": r5(tempo_acf), "pulse_clarity": r5(pulse_clarity), "vbl": r5(vbl), "onset_rate": r5(onset_rate),
        "mode_score": r5(mv["mode_score"]), "key": mv["key"], "harmonic_ratio": r5(hr),
        "centroid": r5(tb["centroid"]), "rolloff": r5(tb["rolloff"]),
        "contrast": r5(tb["contrast"]), "flatness": r5(tb["flatness"]),
        "flux": r5(tb["flux"]), "zcr": r5(tb["zcr"]), "rms": r5(tb["rms"]), "tempo_librosa": r5(tb["tempo"]),
    }


def build_master(labeled: bool) -> list[dict]:
    """추출 대상 [{idx,band,song,url}]. 오디오 파일명은 songs_full 의 (band,idx) 기준.

    --labeled: worksheet 30곡을 url(vid)로 songs_full 에 매핑 → canonical (band,idx) 확보.
    --full   : songs_full 660곡 그대로.
    """
    sf_rows = list(csv.DictReader(open(SONGS_FULL, encoding="utf-8")))
    if not labeled:
        return [{"idx": r["idx"], "band": r["band"], "song": r["song"], "url": r["url"]} for r in sf_rows]
    by_vid = {_vid(r["url"]): r for r in sf_rows}
    out = []
    for r in csv.DictReader(open(WORKSHEET, encoding="utf-8")):
        m = by_vid.get(_vid(r["url"]))
        if m:
            out.append({"idx": m["idx"], "band": m["band"], "song": m["song"], "url": m["url"]})
    return out


def audio_path(band, idx) -> Path:
    return AUDIO / f"{band}__{int(idx):03d}.wav"


def load_done() -> dict:
    done = {}
    if FEATURES.exists():
        for r in csv.DictReader(open(FEATURES, encoding="utf-8")):
            done[(r["band"], r["idx"])] = r
    return done


def paused() -> bool:
    if CONTROL.exists():
        try:
            return json.load(open(CONTROL, encoding="utf-8")).get("command") == "pause"
        except Exception:
            return False
    return False


def write_progress(mode, total, done_n, run_done, started, last_song, status):
    elapsed = time.time() - started
    rate = run_done / elapsed if (elapsed > 0 and run_done > 0) else 0.0
    remain = total - done_n
    eta_s = remain / rate if rate > 0 else None
    PROGRESS.write_text(json.dumps({
        "phase": f"C · 정식 feature 추출 [{mode}]", "status": status,
        "total": total, "done": done_n, "remaining": remain,
        "pct": round(100 * done_n / total, 1) if total else 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started)),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(elapsed, 1), "rate_per_sec": round(rate, 2),
        "eta": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + eta_s)) if eta_s is not None else None,
        "eta_remaining_sec": round(eta_s, 1) if eta_s is not None else None,
        "last_song": last_song,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="전곡 660(기본=labeled 30)")
    ap.add_argument("--labeled", action="store_true", help="손라벨 30곡(기본)")
    ap.add_argument("--limit", type=int, default=0, help="앞 N곡만(디버그)")
    args = ap.parse_args(argv)
    labeled = not args.full
    mode = "labeled30" if labeled else "full660"

    OUTDIR.mkdir(parents=True, exist_ok=True)
    master = build_master(labeled)
    if args.limit:
        master = master[:args.limit]
    total = len(master)
    done = load_done()
    done_n = len(done)
    started = time.time()
    run_done = 0

    new_file = not FEATURES.exists()
    fh = open(FEATURES, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new_file:
        w.writeheader()

    print(f"[Phase C:{mode}] 전체 {total}곡 · 완료 {done_n} · 남은 {total - done_n}", flush=True)
    for row in master:
        key = (row["band"], row["idx"])
        if key in done:
            continue
        if paused():
            write_progress(mode, total, done_n, run_done, started, row["song"], "paused")
            print(f"[일시정지] {done_n}/{total} (다음: {row['song']}). 재개 시 이어감.", flush=True)
            fh.close()
            return 2
        p = audio_path(row["band"], row["idx"])
        rec = {"idx": row["idx"], "band": row["band"], "song": row["song"], "url": row["url"]}
        if p.exists():
            try:
                y, srr = sf.read(str(p), dtype="float32")
                if y.ndim > 1:
                    y = y.mean(axis=1)
                rec.update(compute(y, srr))
                rec["has_audio"] = 1
            except Exception as e:
                print(f"  ! {key} 추출 실패: {e}", flush=True)
                rec.update({k: "" for k in FIELDS if k not in rec})
                rec["has_audio"] = 0
        else:
            rec.update({k: "" for k in FIELDS if k not in rec})
            rec["has_audio"] = 0
        w.writerow(rec)
        fh.flush()
        done_n += 1
        run_done += 1
        write_progress(mode, total, done_n, run_done, started, row["song"], "running")
        print(f"[{done_n}/{total}] {row['band']}__{row['idx']} {row['song'][:22]}", flush=True)
    fh.close()
    write_progress(mode, total, done_n, run_done, started, "(완료)", "done")
    print(f"[완료] {done_n}/{total} → {FEATURES.relative_to(ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
