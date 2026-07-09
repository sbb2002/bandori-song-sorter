"""Phase B0 — onset 파생 후보 feature 산출 (오디오 없이, base env). 작업 5.

660곡 onset JSON(src/content/cluster/onsets/<band>__<idx>.json)에서 energy/tempo 지각축
후보 feature 를 뽑아 CSV(side-project/emoi-map-emotion-axes/phase-b0/onset_features.csv)로 남긴다.
후속 b0_correlate.py 가 이 CSV 를 n=28 손라벨(energy/tempo)과 상관 검정한다.

후보(260708-final_comment.md §2):
  E1 e1_mean_dyn    = mean(dyn.v)            — 전체 강도(현 energy 원천)
  E2 e2_lra_dyn     = p90(dyn.v)-p10(dyn.v)  — 다이내믹 레인지(LRA 근사)
  E3 e3_onset_rate  = level0.n / dur         — 박-레벨 온셋 밀도
  + onset_rate_fine = level2.n / dur         — 최密 온셋 밀도
  + dyn_std/p90/p10                          — 강도 분포
  + pulse_bpm       = pulse.pulse_bpm        — ACF 기반 템포(librosa tempo와 별개, tempo 후보)
  + tempo_json      = tempo                  — librosa 템포(참고, 옥타브오류 기지)

진행 관측/제어(사용자 요청):
  b0_progress.json — 곡마다 갱신: 진행률·ETA·마지막 곡·상태(running/paused/done).
  b0_control.json  — {"command":"pause"} 면 다음 곡 직전에 협조적 중단(재개 시 이어감).
  재개 = 재실행 시 onset_features.csv 에 이미 있는 (band,idx) 는 skip(체크포인트).
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MASTER = ROOT / "src/content/cluster/songs_full.csv"
ONSETS = ROOT / "src/content/cluster/onsets"
OUTDIR = ROOT / "side-project/emoi-map-emotion-axes/phase-b0"
FEATURES = OUTDIR / "onset_features.csv"
PROGRESS = OUTDIR / "b0_progress.json"
CONTROL = OUTDIR / "b0_control.json"

FIELDS = ["idx", "band", "song", "e1_mean_dyn", "e2_lra_dyn", "e3_onset_rate",
          "onset_rate_fine", "dyn_std", "dyn_p90", "dyn_p10", "pulse_bpm",
          "tempo_json", "dur", "has_onset"]


def onset_path(band: str, idx) -> Path:
    return ONSETS / f"{band}__{int(idx):03d}.json"


def compute(d: dict) -> dict:
    v = np.asarray(d.get("dyn", {}).get("v", []), dtype=float)
    dur = float(d.get("dur") or 0.0)
    levels = d.get("levels", []) or []
    n0 = levels[0].get("n", 0) if len(levels) > 0 else 0
    n2 = levels[-1].get("n", 0) if levels else 0
    pulse = d.get("pulse") or {}
    if v.size:
        p90, p10 = float(np.percentile(v, 90)), float(np.percentile(v, 10))
        e1, e2, std = float(v.mean()), p90 - p10, float(v.std())
    else:
        p90 = p10 = e1 = e2 = std = float("nan")
    rate0 = n0 / dur if dur > 0 else float("nan")
    rate2 = n2 / dur if dur > 0 else float("nan")

    def r5(x):
        return "" if x != x else round(x, 5)   # NaN → ""

    return {
        "e1_mean_dyn": r5(e1), "e2_lra_dyn": r5(e2), "e3_onset_rate": r5(rate0),
        "onset_rate_fine": r5(rate2), "dyn_std": r5(std),
        "dyn_p90": r5(p90), "dyn_p10": r5(p10),
        "pulse_bpm": pulse.get("pulse_bpm", ""), "tempo_json": d.get("tempo", ""),
        "dur": "" if dur <= 0 else round(dur, 1),
    }


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


def write_progress(total, done_n, run_done, started, last_song, status):
    elapsed = time.time() - started
    rate = run_done / elapsed if (elapsed > 0 and run_done > 0) else 0.0   # 이번 실행 처리율(초당 곡)
    remain = total - done_n
    eta_s = remain / rate if rate > 0 else None
    prog = {
        "phase": "B0 · onset-feature 추출",
        "status": status,
        "total": total, "done": done_n, "remaining": remain,
        "pct": round(100 * done_n / total, 1) if total else 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started)),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": round(elapsed, 1),
        "rate_per_sec": round(rate, 2),
        "eta": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + eta_s)) if eta_s is not None else None,
        "eta_remaining_sec": round(eta_s, 1) if eta_s is not None else None,
        "last_song": last_song,
    }
    PROGRESS.write_text(json.dumps(prog, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    master = list(csv.DictReader(open(MASTER, encoding="utf-8")))
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

    print(f"[B0] 시작 — 전체 {total}곡, 이미 완료 {done_n}곡, 남은 {total - done_n}곡")
    for row in master:
        key = (row["band"], row["idx"])
        if key in done:
            continue
        if paused():
            write_progress(total, done_n, run_done, started, row["song"], "paused")
            print(f"[일시정지] {done_n}/{total} 지점에서 멈춤 (다음 곡: {row['song']}). 재개 시 이어서 진행.")
            fh.close()
            return 2
        p = onset_path(row["band"], row["idx"])
        rec = {"idx": row["idx"], "band": row["band"], "song": row["song"]}
        if p.exists():
            try:
                d = json.load(open(p, encoding="utf-8"))
                rec.update(compute(d))
                rec["has_onset"] = 1
            except Exception as e:
                print(f"  ! {key} onset 파싱 실패: {e}")
                rec.update({k: "" for k in FIELDS if k not in rec})
                rec["has_onset"] = 0
        else:
            rec.update({k: "" for k in FIELDS if k not in rec})
            rec["has_onset"] = 0   # onset 트랙 없음(fail-soft, 상관에서 제외됨)
        w.writerow(rec)
        fh.flush()
        done_n += 1
        run_done += 1
        write_progress(total, done_n, run_done, started, row["song"], "running")
    fh.close()
    write_progress(total, done_n, run_done, started, "(완료)", "done")
    print(f"[완료] {done_n}/{total} → {FEATURES.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
