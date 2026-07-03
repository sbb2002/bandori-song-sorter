"""매니페스트 CSV → 로컬 오디오 캐시(<cache>/<band>__<idx:03d>.wav). 음원맵 전곡 확대(HANDOFF 작업 2)용.

yt-dlp 벌크 수집기. 가이드라인 출처 = docs/idea/260703.md (안티봇 'HTTP 429' 우회 5원칙).
음원 = 저작물 → **분석 후 폐기**(캐시 폴더는 .gitignore). 커밋되는 건 파생 좌표(audio_map.json)뿐.
**샘플레이트 48kHz 항상 유지**(사용자 확정 2026-07-03) — 용량과 무관하게 다운샘플 금지.

핵심 성질
- **재개 가능(idempotent)**: 이미 받은 wav(>1KB)는 건너뜀 → 중단/일시중지 후 같은 명령 재실행 = 남은 곡만.
- **fail-soft**: 단곡 실패(403·삭제·비공개 등)는 스킵하고 계속. 재실행에서 재시도.
- **일시중지(pause) 조건** — 하나라도 만족하면 멈추고 진행상태 저장 후 종료(exit 2):
  1a) **명시적 차단 신호**(HTTP 429·"Too Many Requests"·"Sign in to confirm you're not a bot") 감지 → 즉시.
  1b) **연속 실패 `--max-consec-fails`회**(기본 5) → IP 차단 추정. (단발 403 ≠ 차단: yt-dlp 서명/포맷 이슈가
      대부분이라 스킵하고 계속. 진짜 차단이면 연속으로 터진다.)
  2)  로컬 시각이 `--stop-hour`(기본 17시) 이상이면서 전체 완료 예상시간이 `--stop-eta-hours`(기본 5h) 이상.
- **진행상태 JSON을 매 곡 갱신**: `fetch_progress.json`에 현재곡·진행률·경과·예상종료(시계)를 기록 → 파일만 열면 현황 파악.
- **JS 런타임 필수**: yt-dlp 2026+ 는 YouTube 서명(nsig)에 deno/node 필요. 없으면 403 다발 → `--js-runtimes` 자동 연결.
- **출력 규약**: <band>__<idx:03d>.wav — build_perceptual_map.py 가 이 이름을 읽는다(고정).

안티봇 5원칙(idea/260703.md) — 주석 [G#]
  [G1] -f ba -x (오디오만) · [G2] 곡간 30~60s 무작위 · [G3] --sleep-requests 5 · [G4] --limit-rate 250K
  [G5] --cookies-from-browser + 크롬 UA (⚠️ 본계정=계정 리스크 pipeline §4, 기본 --no-cookies 권장)

사용
  python src/tools/cluster/build_manifest.py                              # 먼저 songs_full.csv 생성(전곡)
  python src/tools/cluster/fetch_audio.py --cache audio_full --no-cookies # 전곡 수집(권장 시작)
  python src/tools/cluster/fetch_audio.py --dry-run                       # 목록만(네트워크 없음)
  python src/tools/cluster/fetch_audio.py --limit 3                       # 앞 3곡만(스모크)
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]          # src/tools/cluster/<file> → repo root
CLUSTER = ROOT / "src" / "content" / "cluster"
DEFAULT_MANIFEST = CLUSTER / "songs_full.csv"        # 전곡 매니페스트(build_manifest.py 산출)
DEFAULT_PROGRESS = CLUSTER / "fetch_progress.json"   # 진행상태(추적됨 → 핸드오프용)

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 즉시 일시중지 = IP/봇 차단 확정 신호. 403 은 서명/포맷/JS런타임 이슈가 대부분이라 제외(연속실패로 판단).
HARD_BLOCK_SIGNS = ("http error 429", "too many requests", "sign in to confirm",
                    "not a bot", "confirm you", "rate-limit", "rate limit")
PERMANENT_SIGNS = ("video unavailable", "private video", "has been removed",
                   "http error 404", "no longer available", "video is not available",
                   "terminated", "members-only", "join this channel")


def classify_error(text: str) -> str:
    t = (text or "").lower()
    if any(s in t for s in HARD_BLOCK_SIGNS):
        return "block"
    if "403" in t or "forbidden" in t:
        return "403"
    if any(s in t for s in PERMANENT_SIGNS):
        return "permanent"
    return "other"


def find_ffmpeg() -> str | None:
    if shutil.which("ffmpeg"):
        return None
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_js_runtime(pref: str) -> str | None:
    """yt-dlp 서명 해독용 JS 런타임. auto = deno→node 자동 탐지."""
    if pref == "none":
        return None
    if pref != "auto":
        return pref if shutil.which(pref) else None
    for rt in ("deno", "node"):
        if shutil.which(rt):
            return rt
    return None


def build_cmd(url: str, out_tmpl: str, args, ffmpeg_loc, js_rt) -> list[str]:
    cmd = [
        args.ytdlp,
        "-f", "ba",                                 # [G1]
        "-x", "--audio-format", args.audio_format,  # [G1]
        "--audio-quality", "0",
        "--no-playlist",
        "--sleep-requests", str(args.sleep_requests),   # [G3]
        "--limit-rate", args.limit_rate,            # [G4]
        "--user-agent", CHROME_UA,                  # [G5]
        "--retries", str(args.retries),             # 곡당 재시도
        "--fragment-retries", str(args.retries),
        "--extractor-retries", str(args.retries),
        "--postprocessor-args", f"ffmpeg:-ac 1 -ar {args.sample_rate}",  # 모노·48kHz 유지
        "--no-progress",
        "-o", out_tmpl,
    ]
    if js_rt:
        cmd += ["--js-runtimes", js_rt]             # nsig 서명 해독(403 방지)
    if not args.no_cookies:
        cmd += ["--cookies-from-browser", args.cookies_from_browser]     # [G5]
    if ffmpeg_loc:
        cmd += ["--ffmpeg-location", ffmpeg_loc]
    cmd.append(url)
    return cmd


def fmt_dur(sec: float) -> str:
    sec = int(max(0, sec)); h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}h{m:02d}m" if h else (f"{m}m{s:02d}s" if m else f"{s}s")


def write_progress(path: Path, **fields) -> None:
    fields["updated"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="yt-dlp 오디오 벌크 수집(재개·fail-soft·일시중지).")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="입력 CSV. 기본 songs_full.csv")
    ap.add_argument("--cache", default="audio_full", help="출력 캐시 폴더명. 기본 audio_full")
    ap.add_argument("--sample-rate", type=int, default=48000, help="추출 wav 샘플레이트(항상 48kHz 유지)")
    ap.add_argument("--audio-format", default="wav", help="추출 포맷(파이프라인은 wav)")
    ap.add_argument("--min-sleep", type=float, default=30.0, help="[G2] 곡간 최소 대기(s)")
    ap.add_argument("--max-sleep", type=float, default=60.0, help="[G2] 곡간 최대 대기(s)")
    ap.add_argument("--sleep-requests", type=float, default=5.0, help="[G3] 요청간 대기(s)")
    ap.add_argument("--limit-rate", default="250K", help="[G4] 다운로드 속도 상한")
    ap.add_argument("--cookies-from-browser", default="chrome", help="[G5] 쿠키 소스 브라우저")
    ap.add_argument("--no-cookies", action="store_true", help="쿠키 연동 비활성(권장)")
    ap.add_argument("--js-runtime", default="auto", help="JS런타임: auto|node|deno|none")
    ap.add_argument("--retries", type=int, default=10, help="곡당 재시도")
    ap.add_argument("--max-consec-fails", type=int, default=5, help="연속 실패 이 횟수면 차단 추정 일시중지")
    ap.add_argument("--stop-hour", type=int, default=17, help="조건2: 이 시각(로컬) 이상이면 검사")
    ap.add_argument("--stop-eta-hours", type=float, default=5.0, help="조건2: 남은 예상 이 이상이면 중지")
    ap.add_argument("--no-stop-clock", action="store_true", help="조건2 비활성")
    ap.add_argument("--limit", type=int, default=0, help="앞 N곡만(0=전체)")
    ap.add_argument("--progress-file", default=str(DEFAULT_PROGRESS), help="진행상태 JSON 경로")
    ap.add_argument("--ytdlp", default="yt-dlp", help="yt-dlp 실행 경로")
    ap.add_argument("--dry-run", action="store_true", help="목록만 출력(네트워크 없음)")
    args = ap.parse_args(argv)

    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"‼️ 매니페스트 없음: {manifest}\n   먼저: python src/tools/cluster/build_manifest.py")
        return 1
    cache_dir = CLUSTER / args.cache
    progress_file = Path(args.progress_file)
    rows = list(csv.DictReader(open(manifest, encoding="utf-8")))
    if args.limit > 0:
        rows = rows[:args.limit]
    total = len(rows)

    todo, have = [], []
    for r in rows:
        dest = cache_dir / f"{r['band']}__{int(r['idx']):03d}.wav"
        (have if dest.exists() and dest.stat().st_size > 1024 else todo).append((r, dest))
    have0 = len(have)

    print(f"매니페스트 {manifest.name} · 대상 {total}곡 → 캐시 {cache_dir}")
    print(f"이미 받음 {have0} · 받을 것 {len(todo)}  (진행률 {have0*100//total if total else 0}%)")
    if args.dry_run:
        for r, _ in todo:
            print(f"  [받음예정] {r['band']:18} {int(r['idx']):>3} {r['song']}")
        print("\n(--dry-run: 네트워크 요청 없음)")
        return 0
    if not todo:
        print("✅ 받을 곡 없음(전부 캐시 존재).")
        write_progress(progress_file, status="done", reason="all-present", total=total,
                       present=total, remaining=0, pct=100, cache=args.cache)
        return 0

    if shutil.which(args.ytdlp) is None and not Path(args.ytdlp).exists():
        print(f"‼️ yt-dlp 없음({args.ytdlp}). pip install -r src/tools/cluster/requirements-audio.txt")
        return 1
    cache_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_loc = find_ffmpeg()
    js_rt = find_js_runtime(args.js_runtime)
    print(f"JS런타임: {js_rt or '없음(403 위험 — node/deno 설치 권장)'} · "
          f"쿠키: {'없음' if args.no_cookies else args.cookies_from_browser}")

    announced = {p for p in range(10, 101, 10) if p <= have0 * 100 // total}
    run_start = time.monotonic()
    wall_start = datetime.now()
    ok, fail, consec = 0, [], 0
    status, reason = "done", "completed"

    def present_now() -> int:
        return have0 + ok

    def eta_sec(done_att: int) -> float:
        return (time.monotonic() - run_start) / done_att * (len(todo) - done_att) if done_att else 0.0

    def snap(status_: str, reason_: str, current: str) -> None:
        done_att = ok + len(fail)
        eta = eta_sec(done_att)
        end = datetime.now() + timedelta(seconds=eta)
        write_progress(
            progress_file, status=status_, reason=reason_,
            pct=present_now() * 100 // total, present=present_now(), total=total,
            remaining=total - present_now(), session_new=ok, failed_count=len(fail),
            current=current, session_elapsed=fmt_dur(time.monotonic() - run_start),
            eta_remaining=(fmt_dur(eta) if done_att else "측정중"),
            eta_end=(end.strftime("%Y-%m-%d %H:%M") if done_att else "측정중"),
            started_at=wall_start.strftime("%Y-%m-%d %H:%M:%S"),
            sample_rate=args.sample_rate, manifest=manifest.name, cache=args.cache, failed=fail)

    def milestone(done_att: int) -> None:
        pct_now = present_now() * 100 // total
        eta = eta_sec(done_att)
        for p in range(10, 101, 10):
            if p <= pct_now and p not in announced:
                announced.add(p)
                end = datetime.now() + timedelta(seconds=eta)
                tail = f"→ 예상 종료 {end:%m-%d %H:%M}" if done_att else "→ (완료)"
                print(f"\n■ 진행률 {p}% ({present_now()}/{total}) · 세션경과 "
                      f"{fmt_dur(time.monotonic()-run_start)} · 남은 {len(todo)-done_att}곡 "
                      f"{fmt_dur(eta)} {tail}\n")

    for i, (r, dest) in enumerate(todo, 1):
        out_tmpl = str(cache_dir / f"{r['band']}__{int(r['idx']):03d}.%(ext)s")
        label = f"[{i}/{len(todo)}] {r['band']} · {r['song']}"
        print(label)
        snap("running", "", label)                  # 매 곡 진행상태 기록(현재곡 반영)
        cmd = build_cmd(r["url"], out_tmpl, args, ffmpeg_loc, js_rt)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
        except KeyboardInterrupt:
            status, reason = "interrupted", "keyboard-interrupt"
            print("\n중단됨 — 받은 wav 보존, 같은 명령으로 재개 가능.")
            break

        if proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1024:
            ok += 1
            consec = 0
        else:
            out = (proc.stderr or "") + (proc.stdout or "")
            kind = classify_error(out)
            tail = "\n     ".join(out.strip().splitlines()[-6:])
            consec += 1
            fail.append([r["band"], r["song"], r["url"]])
            if kind == "block":                     # 1a) 확정 차단 → 즉시 일시중지
                status, reason = "paused", f"hard-block({kind}) — {r['song']}"
                print(f"  ⛔ IP/봇 차단 신호 → 즉시 일시중지\n     {tail}")
                break
            if consec >= args.max_consec_fails:      # 1b) 연속실패 → 차단 추정
                status, reason = "paused", f"{consec}연속 실패(차단 추정) — 마지막 {kind}"
                print(f"  ⛔ 연속 {consec}곡 실패 → 차단 추정, 일시중지\n     {tail}")
                break
            print(f"  ⚠️ 실패(스킵 {consec}/{args.max_consec_fails}): {kind}\n     {tail}")

        done_att = ok + len(fail)
        milestone(done_att)
        snap("running", "", label)

        if not args.no_stop_clock:                   # 2) 시각/ETA 일시중지
            eta_all = eta_sec(done_att)
            if datetime.now().hour >= args.stop_hour and eta_all >= args.stop_eta_hours * 3600:
                status, reason = "paused", (f"clock>={args.stop_hour}:00 & eta "
                                            f"{fmt_dur(eta_all)}>={args.stop_eta_hours}h")
                print(f"\n⛔ 시각 {datetime.now():%H:%M} · 남은 예상 {fmt_dur(eta_all)} → 일시중지")
                break

        if i < len(todo):                            # [G2] 곡간 무작위 대기
            nap = random.uniform(args.min_sleep, args.max_sleep)
            print(f"  …대기 {nap:.0f}s")
            time.sleep(nap)

    snap(status, reason, "—")
    present = present_now()
    pct = present * 100 // total
    banner = {"done": "✅ 완료", "paused": "⛔ 일시중지", "interrupted": "⏹ 중단"}.get(status, status)
    print(f"\n{banner} — 진행률 {pct}% ({present}/{total}) · 이번 세션 신규 {ok} · 실패 {len(fail)}")
    print(f"사유: {reason}")
    for b, s, u in fail:
        print(f"  실패 {b} · {s} — {u}")
    if status in ("paused", "interrupted"):
        print("→ 재개: 같은 명령 재실행(skip-existing). 다른 로컬은 wav zip 이동 후 재개.")
    return 2 if status == "paused" else (3 if status == "interrupted" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
