"""매니페스트 CSV → 로컬 오디오 캐시(<cache>/<band>__<idx:03d>.wav). 음원맵 전곡 확대(HANDOFF 작업 2)용.

yt-dlp 벌크 수집기. 가이드라인 출처 = docs/idea/260703.md (안티봇 'HTTP 429' 우회 5원칙).
음원 = 저작물 → **분석 후 폐기**(캐시 폴더는 .gitignore). 커밋되는 건 파생 좌표(audio_map.json)뿐.

핵심 성질
- **재개 가능(idempotent)**: 이미 받은 wav(>1KB)는 건너뜀 → 중단/일시중지 후 같은 명령 재실행 = 남은 곡만.
- **fail-soft**: 삭제·비공개 등 단곡 실패는 스킵하고 계속(pipeline-automation §4). 재실행에서 재시도.
- **일시중지(pause) 조건** — 하나라도 만족하면 멈추고 진행상태 저장 후 종료(exit 2):
  1) 레이트리밋/봇월(HTTP 429·403·"not a bot" 등)이 yt-dlp 재시도(--retries/--extractor-retries) 소진 후에도 발생.
  2) 로컬 시각이 `--stop-hour`(기본 17시) 이상이면서 전체 완료 예상시간이 `--stop-eta-hours`(기본 5h) 이상.
- **10% 단위 진행률**: 누적 진행률(전체 대비)·경과·예상 종료시각(HH:MM)을 10%마다 출력 + `fetch_progress.json` 갱신.
- **출력 규약**: <band>__<idx:03d>.wav — build_perceptual_map.py 가 이 이름을 읽는다(고정).

안티봇 5원칙(idea/260703.md) — 주석 [G#]
  [G1] 트래픽 최소화 : -f ba -x (오디오 최적 포맷만, 영상/자막/썸네일 미요청)
  [G2] 인간 행동 모방 : 곡간 30~60s 무작위 대기(파이썬 루프)
  [G3] API 과부하 방지: --sleep-requests 5
  [G4] 대역폭 위장    : --limit-rate 250K
  [G5] 세션 신뢰도    : --cookies-from-browser + 크롬 User-Agent
> 추출 포맷은 파이프라인이 읽는 .wav 로 뽑는다(가이드 예시 mp3). 추출 포맷은 *다운로드 스트림*(-f ba)이
  아니라 결과물이라 안티봇 태세와 무관 → wav 로 파이프라인 정합만 맞춤.
> ⚠️ --cookies-from-browser=본계정은 계정 리스크(pipeline-automation §4 '본계정 금지'). --no-cookies 로 끌 수 있다.

사용
  python src/tools/cluster/build_manifest.py                              # 먼저 songs_full.csv 생성(전곡)
  python src/tools/cluster/fetch_audio.py --cache audio_full              # songs_full.csv → audio_full
  python src/tools/cluster/fetch_audio.py --dry-run                       # 받을/건너뛸 목록만(네트워크 없음)
  python src/tools/cluster/fetch_audio.py --limit 3                       # 앞 3곡만(스모크)
  python src/tools/cluster/fetch_audio.py --no-cookies                    # 쿠키 없이
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

# 재시도 소진 후에도 뜨면 = 레이트리밋/봇월 → 일시중지 조건 1)
RATE_LIMIT_SIGNS = ("http error 429", "too many requests", "http error 403",
                    "sign in to confirm", "not a bot", "confirm you", "rate-limit",
                    "rate limit", "429")
# 단곡 영구 실패 → 스킵(계속)
PERMANENT_SIGNS = ("video unavailable", "private video", "has been removed",
                   "http error 404", "no longer available", "video is not available",
                   "terminated", "members-only", "join this channel", "age")


def classify_error(text: str) -> str:
    t = (text or "").lower()
    if any(s in t for s in RATE_LIMIT_SIGNS):
        return "ratelimit"
    if any(s in t for s in PERMANENT_SIGNS):
        return "permanent"
    return "other"


def find_ffmpeg() -> str | None:
    """PATH의 ffmpeg → 없으면 imageio-ffmpeg 번들(추출 후처리 필요)."""
    if shutil.which("ffmpeg"):
        return None
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def build_cmd(url: str, out_tmpl: str, args, ffmpeg_loc: str | None) -> list[str]:
    cmd = [
        args.ytdlp,
        "-f", "ba",                                 # [G1] 오디오 최적 포맷만
        "-x", "--audio-format", args.audio_format,  # [G1] 추출
        "--audio-quality", "0",
        "--no-playlist",                            # list= 무시, 단일 영상만
        "--sleep-requests", str(args.sleep_requests),   # [G3]
        "--limit-rate", args.limit_rate,            # [G4]
        "--user-agent", CHROME_UA,                  # [G5]
        "--retries", str(args.retries),             # 조건1: 소진 후에도 429면 pause
        "--fragment-retries", str(args.retries),
        "--extractor-retries", str(args.retries),
        "--postprocessor-args", f"ffmpeg:-ac 1 -ar {args.sample_rate}",  # 모노·목표 SR
        "--no-progress",
        "-o", out_tmpl,
    ]
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
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                    help="입력 CSV(band,idx,song,url). 기본=songs_full.csv")
    ap.add_argument("--cache", default="audio_full", help="출력 캐시 폴더명. 기본 audio_full")
    ap.add_argument("--sample-rate", type=int, default=48000, help="추출 wav 샘플레이트(Hz)")
    ap.add_argument("--audio-format", default="wav", help="추출 포맷(파이프라인은 wav)")
    ap.add_argument("--min-sleep", type=float, default=30.0, help="[G2] 곡간 최소 대기(s)")
    ap.add_argument("--max-sleep", type=float, default=60.0, help="[G2] 곡간 최대 대기(s)")
    ap.add_argument("--sleep-requests", type=float, default=5.0, help="[G3] 요청간 대기(s)")
    ap.add_argument("--limit-rate", default="250K", help="[G4] 다운로드 속도 상한")
    ap.add_argument("--cookies-from-browser", default="chrome", help="[G5] 쿠키 소스 브라우저")
    ap.add_argument("--no-cookies", action="store_true", help="쿠키 연동 비활성")
    ap.add_argument("--retries", type=int, default=10, help="곡당 재시도(조건1 = 소진 후 429)")
    ap.add_argument("--stop-hour", type=int, default=17, help="조건2: 이 시각(로컬) 이상이면 검사")
    ap.add_argument("--stop-eta-hours", type=float, default=5.0, help="조건2: 남은 예상 이 이상이면 중지")
    ap.add_argument("--no-stop-clock", action="store_true", help="조건2(시각/ETA 중지) 비활성")
    ap.add_argument("--limit", type=int, default=0, help="앞 N곡만(0=전체). 스모크용")
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
        write_progress(progress_file, status="done", reason="all-present", manifest=manifest.name,
                       cache=args.cache, total=total, present=total, remaining=0, pct=100)
        return 0

    if shutil.which(args.ytdlp) is None and not Path(args.ytdlp).exists():
        print(f"‼️ yt-dlp 를 찾을 수 없음({args.ytdlp}). "
              f"pip install -r src/tools/cluster/requirements-audio.txt")
        return 1
    cache_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_loc = find_ffmpeg()
    if not args.no_cookies:
        print(f"쿠키: {args.cookies_from_browser} 브라우저 (크롬 종료 상태 권장)")

    # 10% 마일스톤: 이미 지난 것(재개분)은 조용히 소거
    announced = {p for p in range(10, 101, 10) if p <= have0 * 100 // total}
    run_start = time.monotonic()
    ok, fail = 0, []
    status, reason = "done", "completed"

    def present_now() -> int:
        return have0 + ok

    def milestone(i: int) -> None:
        """i = 이번 세션에서 처리한 곡 수. 새로 넘은 10% 마다 진행률+예상 종료 출력."""
        pct_now = present_now() * 100 // total
        elapsed = time.monotonic() - run_start
        avg = elapsed / i if i else 0.0
        left = len(todo) - i
        eta = avg * left
        for p in range(10, 101, 10):
            if p <= pct_now and p not in announced:
                announced.add(p)
                end = datetime.now() + timedelta(seconds=eta)
                tail = f"→ 예상 종료 {end:%H:%M}" if avg else "→ (완료)"
                print(f"\n■ 진행률 {p}% ({present_now()}/{total}) · 세션경과 {fmt_dur(elapsed)} · "
                      f"남은 {left}곡 {fmt_dur(eta)} {tail}\n")
        write_progress(progress_file, status="running", reason="", manifest=manifest.name,
                       cache=args.cache, total=total, present=present_now(),
                       downloaded_this_run=ok, failed_count=len(fail),
                       remaining=len(todo) - i, pct=pct_now,
                       eta_end=(datetime.now() + timedelta(seconds=eta)).isoformat(timespec="minutes"))

    for i, (r, dest) in enumerate(todo, 1):
        out_tmpl = str(cache_dir / f"{r['band']}__{int(r['idx']):03d}.%(ext)s")
        print(f"[{i}/{len(todo)}] {r['band']} · {r['song']}")
        cmd = build_cmd(r["url"], out_tmpl, args, ffmpeg_loc)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
        except KeyboardInterrupt:
            status, reason = "interrupted", "keyboard-interrupt"
            print("\n중단됨 — 받은 wav 보존, 같은 명령으로 재개 가능.")
            break

        if proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1024:
            ok += 1
        else:
            out = (proc.stderr or "") + (proc.stdout or "")
            kind = classify_error(out)
            tail = "\n     ".join(out.strip().splitlines()[-8:])
            if kind == "ratelimit":                 # 조건1) 일시중지
                status, reason = "paused", "ratelimit(429/bot-wall) after retries"
                print(f"  ⛔ 레이트리밋/봇월 감지(재시도 소진 후) → 일시중지\n     {tail}")
                break
            print(f"  ⚠️ 실패(스킵): {kind}\n     {tail}")
            fail.append([r["band"], r["song"], r["url"]])

        milestone(i)

        # 조건2) 시각/ETA 일시중지 검사
        if not args.no_stop_clock:
            elapsed = time.monotonic() - run_start
            avg = elapsed / i
            eta_all = avg * (len(todo) - i)
            if datetime.now().hour >= args.stop_hour and eta_all >= args.stop_eta_hours * 3600:
                status, reason = "paused", (f"clock>={args.stop_hour}:00 & eta "
                                            f"{fmt_dur(eta_all)}>={args.stop_eta_hours}h")
                print(f"\n⛔ 시각 {datetime.now():%H:%M} · 남은 예상 {fmt_dur(eta_all)} "
                      f"(≥{args.stop_eta_hours}h) → 일시중지")
                break

        if i < len(todo):                           # [G2] 곡간 무작위 대기
            nap = random.uniform(args.min_sleep, args.max_sleep)
            print(f"  …대기 {nap:.0f}s")
            time.sleep(nap)

    present = present_now()
    pct = present * 100 // total
    write_progress(progress_file, status=status, reason=reason, manifest=manifest.name,
                   cache=args.cache, total=total, present=present, downloaded_this_run=ok,
                   failed_count=len(fail), remaining=total - present, pct=pct, failed=fail)

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
