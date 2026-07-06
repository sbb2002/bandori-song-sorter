"""신곡 로더 오케스트레이터 — RSS 감지 → 데이터 반영 → emoi-map/pulse 증분 → main (spec §3).

기존 모듈을 import/호출만 하는 **얇은 래퍼**(파일 이동 없음). full-auto: PR 게이트 없이 감지된
신곡을 곡별 fail-soft 로 처리해 **데이터 파일만** 커밋·푸시한다. index.html 재빌드는 별도
deploy.yml(Pages 아티팩트)이 담당하므로 여기선 손대지 않는다(핫픽스 충돌 회피).

곡 1개 처리(모두 성공해야 커밋 대상에 포함 — 실패 시 공유파일 스냅샷 복원):
  ① 임시 매니페스트(1행) → fetch_audio → audio_full/<band>__<idx>.wav (실패=스킵)
  ② feats → 좌표 entry(동결 norm, 미기록)
  ③ separate_drums → build_beat_track → build_dynamics → onsets/<band>__<idx>.json(+dyn)
  ④ 공유파일 반영: songs_full.csv append · audio_map.json append+centroid · songs/<band>.yaml 삽입
  ⑤ wav/드럼 정리

⚠️ idx = 전역 max+1 로 CSV 끝에 append(build_manifest 재실행은 전역 재번호 → onset 파일명 붕괴).
⚠️ separate_drums/build_beat_track 은 CWD-상대경로 → 모든 subprocess 를 cwd=ROOT 로 실행.

사용:
  python actions/orchestrate.py            # 감지→처리→커밋·푸시(CI/실계정)
  python actions/orchestrate.py --dry       # 감지·처리까지 하되 커밋/푸시 안 함(로컬 검증)
  python actions/orchestrate.py --detect-only  # 감지 목록만(오디오·git 없음)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                  # actions/<file> → repo root
sys.path.insert(0, str(ROOT / "src" / "tools" / "collect"))
sys.path.insert(0, str(ROOT / "src" / "tools" / "cluster"))

import youtube_rss as rss                                    # noqa: E402
# append_song_map 은 librosa 등 오디오 스택을 끌어오므로 곡 처리 시 지연 import
# (감지 전용 경로 --detect-only 는 가볍게 유지).

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

CLUSTER = ROOT / "src" / "content" / "cluster"
MANIFEST = CLUSTER / "songs_full.csv"
MAP = CLUSTER / "audio_map.json"
ONSETS = CLUSTER / "onsets"
AUDIO_FULL = CLUSTER / "audio_full"
AUDIO_DRUMS = CLUSTER / "audio_drums"
PY = sys.executable

# git add 대상 = 데이터 파일만(index.html 등 생성물 제외).
DATA_PATHS = [
    "src/content/songs",
    "src/content/cluster/songs_full.csv",
    "src/content/cluster/audio_map.json",
    "src/content/cluster/onsets",
    "src/tools/collect/rss_events.jsonl",
]


# ──────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────

def run(cmd: list[str], *, check: bool = False, quiet: bool = False) -> subprocess.CompletedProcess:
    """cwd=ROOT 로 실행. 실패해도 예외 안 냄(fail-soft) — check=True 일 때만 raise."""
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if not quiet and (p.returncode != 0):
        tail = "\n     ".join((p.stderr or p.stdout or "").strip().splitlines()[-8:])
        print(f"  [rc={p.returncode}] {' '.join(cmd[:3])}…\n     {tail}")
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} 실패(rc={p.returncode})")
    return p


def csv_rows() -> list[dict]:
    with open(MANIFEST, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def next_idx(rows: list[dict]) -> int:
    return (max((int(r["idx"]) for r in rows), default=-1)) + 1


def append_csv_row(idx: int, band: str, song: str, url: str) -> None:
    """songs_full.csv 끝에 한 줄 append(기존 행 불변 → 전역 idx 안정)."""
    line = ",".join(_csv_field(v) for v in (idx, band, song, url))
    with open(MANIFEST, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\r\n")


def _csv_field(v) -> str:
    s = str(v)
    if any(c in s for c in (",", '"', "\n", "\r")):
        return '"' + s.replace('"', '""') + '"'
    return s


def write_temp_manifest(idx: int, band: str, song: str, url: str) -> Path:
    """fetch_audio·build_dynamics 용 1행 임시 매니페스트(real CSV 미오염)."""
    fd = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     encoding="utf-8", newline="")
    w = csv.writer(fd)
    w.writerow(["idx", "band", "song", "url"])
    w.writerow([idx, band, song, url])
    fd.close()
    return Path(fd.name)


def insert_yaml(cand: dict, band_file: dict) -> str:
    """songs/<band>.yaml 에 트랙 수술 삽입(open_pr 로직 재사용, git 없음). url(youtu.be) 반환."""
    band, vid = cand["band"], cand["video_id"]
    path = band_file.get(band) or (rss.DATA_DIR / f"{band}.yaml")
    numbering = "Cover" if cand["is_cover"] else "Single"
    album_title = "Covers" if cand["is_cover"] else "New Singles"
    track_number = cand["published"] or datetime.date.today().isoformat()
    url = rss.WATCH_SHORT.format(vid)
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    norm = raw.decode("utf-8").replace("\r\n", "\n")
    new_norm, _action = rss.insert_track(norm, band, numbering, album_title,
                                         rss.FALLBACK_IMG, track_number, cand["name"], url)
    if not rss._verify_insertion(new_norm, band, vid):
        raise RuntimeError(f"insert_track verify 실패: {vid} {cand['name']!r}")
    out = new_norm.replace("\n", "\r\n") if crlf else new_norm
    path.write_bytes(out.encode("utf-8"))
    return url


# ──────────────────────────────────────────────
# 곡 1개 처리(원자적: 성공해야 landed)
# ──────────────────────────────────────────────

def process_song(cand: dict, idx: int, band_file: dict) -> dict | None:
    """신곡 1곡을 데이터에 반영. 성공 시 요약 dict, 실패 시 None(공유파일 스냅샷 복원)."""
    band = cand["band"]
    oid = f"{band}__{idx:03d}"
    url = rss.WATCH_SHORT.format(cand["video_id"])
    song = cand["name"]
    wav = AUDIO_FULL / f"{oid}.wav"
    drum = AUDIO_DRUMS / f"{oid}.wav"
    onset = ONSETS / f"{oid}.json"

    # 실패 시 되돌릴 공유파일 스냅샷(신곡 여러 개가 같은 파일에 누적 → 부분 실패 격리).
    import append_song_map as asm       # 지연 import(오디오 스택; 감지 전용 경로는 불필요)

    yaml_path = band_file.get(band) or (rss.DATA_DIR / f"{band}.yaml")
    snap = {p: p.read_bytes() for p in (MANIFEST, MAP, yaml_path) if p.exists()}
    tmp_manifest = None

    def cleanup_temp():
        for p in (wav, drum):
            p.unlink(missing_ok=True)
        if tmp_manifest:
            tmp_manifest.unlink(missing_ok=True)

    try:
        # ① 오디오 수집(임시 매니페스트 1행 → fetch_audio, skip-existing·fail-soft)
        tmp_manifest = write_temp_manifest(idx, band, song, url)
        run([PY, "src/tools/cluster/fetch_audio.py",
             "--manifest", str(tmp_manifest), "--cache", "audio_full",
             "--no-cookies", "--no-stop-clock", "--no-stop-size"])
        if not (wav.exists() and wav.stat().st_size > 1024):
            print(f"  ⚠️ 다운로드 실패 → 스킵(다음 실행 재시도): {band} · {song}")
            cleanup_temp()
            return None

        # ② 좌표(feats 1회, 아직 맵 미기록)
        contrast, mode, tempo = asm.feats_of(band, idx, cache="audio_full")
        doc = asm.load_map(MAP)
        entry = asm.build_entry(band, song, url, contrast, mode, tempo, doc["norm"])

        # ③ pulse 프리셋(demucs 드럼분리 → beat 그리드 → dyn 곡선)
        run([PY, "src/tools/cluster/separate_drums.py", band, str(idx),
             "--cache", "audio_full"], check=True)
        run([PY, "src/tools/cluster/build_beat_track.py", band, str(idx),
             "--cache", "audio_drums"], check=True)
        run([PY, "src/tools/cluster/build_dynamics.py",
             "--manifest", str(tmp_manifest), "--start", "0", "--count", "1"], check=True)
        if not onset.exists():
            raise RuntimeError(f"onset 미생성: {onset}")

        # ④ 공유파일 반영(빠르고 저위험 — 여기까지 오면 확정)
        append_csv_row(idx, band, song, url)
        cent = asm.apply_entry(doc, entry)
        asm.write_map(doc, MAP)
        insert_yaml(cand, band_file)

        cleanup_temp()
        print(f"  ✅ {band} · {song}  (idx={idx} x={entry['x']} y={entry['y']} "
              f"→ centroid x={cent['x']} y={cent['y']} n={cent['n']})")
        return {"band": band, "idx": idx, "song": song, "video_id": cand["video_id"],
                "url": url, "x": entry["x"], "y": entry["y"], "published": cand["published"],
                "variant": cand["variant"], "length_s": cand["length_s"]}

    except Exception as exc:
        print(f"  ✗ 처리 실패(롤백·스킵): {band} · {song} — {exc!r}")
        for p, b in snap.items():          # 공유파일 원복
            p.write_bytes(b)
        onset.unlink(missing_ok=True)      # 이 곡 파생물 제거
        cleanup_temp()
        return None


# ──────────────────────────────────────────────
# git (데이터 파일만 커밋 → main, rebase-retry)
# ──────────────────────────────────────────────

def commit_and_push(landed: list[dict]) -> bool:
    run(["git", "add", "--"] + DATA_PATHS)
    if run(["git", "diff", "--cached", "--quiet"], quiet=True).returncode == 0:
        print("커밋할 데이터 변경 없음.")
        return False
    titles = ", ".join(f"{s['band']}·{s['song']}" for s in landed[:5])
    more = f" 외 {len(landed) - 5}곡" if len(landed) > 5 else ""
    body = "\n".join(f"- {s['band']} / {s['song']} (idx={s['idx']}, {s['video_id']})"
                     for s in landed)
    msg = f"feat(songs): 신곡 자동 반영 {len(landed)}곡 — {titles}{more} [auto]\n\n{body}"
    run(["git", "commit", "-m", msg], check=True)

    for attempt in range(1, 4):            # non-ff 경합 대비 rebase-retry
        run(["git", "pull", "--rebase", "origin", "main"])
        if run(["git", "push", "origin", "HEAD:main"]).returncode == 0:
            print(f"push 성공(시도 {attempt}).")
            return True
        print(f"push 거부 → rebase 후 재시도({attempt}/3)")
        time.sleep(2)
    print("‼️ push 3회 실패 — 다음 실행에서 재시도(데이터는 재감지됨).")
    return False


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────

def _emit_github_output(key: str, val) -> None:
    """GITHUB_OUTPUT 이 있으면 step output 기록(워크플로우 감지 게이트용)."""
    import os
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"{key}={val}\n")


def log_events(landed: list[dict], failed: list[dict]) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    recs = []
    for s in landed:
        recs.append({"ts": now, "band": s["band"], "video_id": s["video_id"],
                     "title": s["song"], "published": s["published"], "length_s": s["length_s"],
                     "variant": s["variant"], "decision": "auto_added", "idx": s["idx"]})
    for c in failed:
        recs.append({"ts": now, "band": c["band"], "video_id": c["video_id"],
                     "title": c["name"], "published": c["published"], "length_s": c["length_s"],
                     "variant": c["variant"], "decision": "auto_failed"})
    rss.append_events(recs)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="신곡 로더 오케스트레이터(full-auto)")
    ap.add_argument("--dry", action="store_true", help="처리까지 하되 git 커밋/푸시 안 함")
    ap.add_argument("--detect-only", action="store_true", help="감지 목록만(오디오·git 없음)")
    ap.add_argument("--limit", type=int, default=0, help="이번 실행 처리 최대 곡 수(0=전체)")
    ap.add_argument("--test-band", default=None, help="[테스트] 감시 밴드 중 하나")
    ap.add_argument("--test-video", default=None,
                    help="[테스트] video_id 또는 URL — 감지 건너뛰고 이 곡만 강제 처리(--dry 필수)")
    a = ap.parse_args(argv)

    # ── [테스트] 강제 처리: 감지를 건너뛰고 지정 곡 1개를 end-to-end 실행(다운로드·demucs·
    #    펄스·좌표). --dry 강제 → 커밋/푸시 없음. CI 러너는 작업트리를 폐기하므로 레포 무변동.
    if a.test_video:
        if not a.dry:
            print("‼️ 테스트 모드는 안전을 위해 --dry 필수(레포 데이터 커밋 안 함).")
            return 1
        band = a.test_band
        if band not in rss.BAND_CHANNELS:
            print(f"‼️ --test-band 는 감시 밴드 중 하나여야 함: {list(rss.BAND_CHANNELS)}")
            return 1
        vid = rss.video_id(a.test_video) or a.test_video       # URL이면 id 추출
        _, _, band_file = rss.load_existing()
        cand = {"band": band, "video_id": vid, "name": f"[TEST] {vid}",
                "published": datetime.date.today().isoformat(), "variant": "",
                "length_s": None, "url": rss.WATCH_PAGE.format(vid), "is_cover": False}
        idx = next_idx(csv_rows())
        print(f"▶ [TEST/dry] {band} · {vid} → idx {idx}  "
              f"(커밋 없음 · 작업트리 변경은 러너 폐기 시 소멸)")
        res = process_song(cand, idx, band_file)
        print(f"\n테스트 결과: {'✅ 성공(다운로드·펄스·좌표 전 과정 통과)' if res else '✗ 실패 — 위 로그 확인(다운로드 봇월 등)'}")
        return 0

    # ── 감지(dedup=커밋된 YAML, idempotent) ──
    candidates, drops, health, band_file = rss.collect_candidates(set(), scrape_length=True)
    print(f"감지: 신곡 후보 {len(candidates)}곡 (drop {len(drops)}, 밴드 {len(health)})")
    for c in candidates:
        tag = f" [{c['variant']}]" if c["variant"] else ""
        print(f"  · {c['band']:16} {c['published']} | {c['name']}{tag}")

    anomalies = [b for b, h in health.items() if (not h["ok"]) or h["valid"] == 0]
    _emit_github_output("candidates", len(candidates))       # 워크플로우 감지 게이트
    if a.detect_only:
        if anomalies:
            print(f"파싱 이상 밴드: {anomalies}")
        return 0
    if not candidates:
        print("신곡 없음 — 종료(멱등).")
        if anomalies:
            rss.open_health_issue(anomalies, health)
        return 0

    if a.limit > 0:
        candidates = candidates[:a.limit]

    # ── 곡별 처리(fail-soft, idx=전역 max+1 부터 성공분만 연속 부여) ──
    rows = csv_rows()
    base = next_idx(rows)
    landed, failed = [], []
    for c in candidates:
        idx = base + len(landed)                       # 성공한 만큼만 전진(실패는 idx 재사용)
        print(f"\n▶ [{c['band']}] {c['name']}  → idx {idx}")
        res = process_song(c, idx, band_file)
        (landed if res else failed).append(res or c)
        if len(candidates) > 1:
            time.sleep(3)                              # 유튜브 예의(경미)

    print(f"\n반영 {len(landed)}곡 · 실패 {len(failed)}곡")
    log_events(landed, [c for c in failed])

    if not landed:
        print("반영된 신곡 없음 — 커밋 생략.")
        return 0
    if a.dry:
        print("--dry: git 커밋/푸시 생략(작업트리에 변경 남김).")
        return 0

    commit_and_push(landed)
    if anomalies:
        rss.open_health_issue(anomalies, health)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
