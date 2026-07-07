"""신곡 로더 로컬 러너 — 전용 클론에서 다운로드~main push (반자동 옵션2).

CI(GitHub Actions = 데이터센터 IP)는 YouTube 다운로드가 봇월에 막힘이 실증됨(세션 27, E2E 3회
hard-block). 그래서 **다운로드는 집(레지덴셜 IP)에서 이 스크립트로** 수행한다. 다운로드 이후
(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트가 없어 그대로 자동으로 흐른다.

★격리: 자동화 git 활동(main 커밋·푸시)이 데브 핫픽스 작업과 얽히지 않도록 **전용 로컬 클론에서만**
실행한다(별개 브랜치로는 워킹트리를 공유해 격리가 안 됨). 데브 레포는 전혀 건드리지 않는다.

흐름:
  ① 전용 클론(--repo-path, 기본 ../bandori-pipeline) 없으면 origin 에서 clone
  ② fetch origin → checkout main → reset --hard origin/main   (오디오 캐시=gitignore, 보존→재개)
  ③ cwd=클론에서 `python src/tools/semiauto-loader/orchestrate.py [옵션]`:
       감지 → 다운로드(집 IP) → demucs/pulse → 좌표 append → commit → push origin main
  ④ deploy.yml 이 main push 를 받아 라이브 재배포(자동)
  ⑤ 처리 결과(신곡 0건 / N곡 반영 / 전부 실패 / 오류)를 터미널 + 텔레그램에 1건 통지

사전조건: 오디오 스택 env(yt-dlp·node·torch/demucs·librosa·ffmpeg)에서 실행 + git push 자격.
  텔레그램 결과 통지는 TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID(환경변수 또는 repo 루트 `.env`) 필요 —
  없으면 통지만 조용히 스킵되고 처리는 정상 진행.

사용:
  python src/tools/semiauto-loader/run_local.py                       # 감지→반영(실제 push)
  python src/tools/semiauto-loader/run_local.py --limit 2             # 최대 2곡
  python src/tools/semiauto-loader/run_local.py --dry                 # 처리하되 push 안 함(검증)
  python src/tools/semiauto-loader/run_local.py --test-band afterglow --test-video 09B-WljIiTo  # E2E 1곡(dry 강제)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # src/tools/semiauto-loader/<file> → repo root
PY = sys.executable

sys.path.insert(0, str(Path(__file__).resolve().parent))   # 형제 notify.py import 용
import notify                                               # noqa: E402  (Telegram, urllib 무의존)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def run(cmd, *, cwd=None, check=True, capture=False) -> subprocess.CompletedProcess:
    where = f"   (cwd={cwd})" if cwd else ""
    print(f"$ {' '.join(str(c) for c in cmd)}{where}")
    p = subprocess.run(cmd, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                       capture_output=capture)
    if capture and p.stdout:
        print(p.stdout, end="")
    if check and p.returncode != 0:
        raise SystemExit(f"‼️ 실패(rc={p.returncode}): {' '.join(str(c) for c in cmd)}")
    return p


def run_streamed(cmd, *, cwd=None) -> tuple[int, str]:
    """실시간으로 stdout/stderr(합쳐서)를 터미널에 그대로 흘리는 동시에 전체 텍스트를 모아 반환.
    orchestrate.py 실행 결과(신곡 0건/반영/실패 메시지)를 실행 후 판별하는 데 씀."""
    where = f"   (cwd={cwd})" if cwd else ""
    print(f"$ {' '.join(str(c) for c in cmd)}{where}")
    proc = subprocess.Popen(cmd, cwd=cwd, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    lines: list[str] = []
    for line in proc.stdout:
        print(line, end="")
        lines.append(line)
    proc.wait()
    return proc.returncode, "".join(lines)


def origin_url() -> str:
    return run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
               capture=True).stdout.strip()


def ensure_clone(repo_path: Path) -> None:
    if (repo_path / ".git").exists():
        return
    url = origin_url()
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"전용 클론 없음 → clone {url}\n              → {repo_path}")
    run(["git", "clone", url, str(repo_path)])


def sync_main(repo_path: Path) -> None:
    g = ["git", "-C", str(repo_path)]
    run(g + ["fetch", "origin", "--prune"])
    run(g + ["checkout", "main"])
    run(g + ["reset", "--hard", "origin/main"])     # 오디오 캐시는 gitignore라 보존(clean 안 함)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="신곡 로더 로컬 러너(전용 클론에서 다운로드~push)")
    ap.add_argument("--repo-path", default=str(ROOT.parent / "bandori-pipeline"),
                    help="전용 클론 경로(기본 ../bandori-pipeline). 데브 레포와 달라야 함")
    ap.add_argument("--limit", type=int, default=0, help="이번 실행 처리 최대 곡 수(0=전체)")
    ap.add_argument("--dry", action="store_true", help="처리하되 커밋/푸시 안 함")
    ap.add_argument("--test-band", default=None, help="[테스트] 감시 밴드(예: afterglow)")
    ap.add_argument("--test-video", default=None,
                    help="[테스트] video_id/URL — 이 곡만 강제 처리(orchestrate 가 --dry 강제)")
    a = ap.parse_args(argv)

    repo_path = Path(a.repo_path).resolve()
    if repo_path == ROOT:
        raise SystemExit("‼️ --repo-path 가 데브 레포와 동일 — 별도 경로(전용 클론)가 필요합니다.")
    if a.test_video and not a.test_band:
        raise SystemExit("‼️ --test-video 는 --test-band 와 함께 지정하세요.")

    ensure_clone(repo_path)
    sync_main(repo_path)

    cmd = [PY, "src/tools/semiauto-loader/orchestrate.py"]
    if a.test_video:
        cmd += ["--test-band", a.test_band, "--test-video", a.test_video, "--dry"]
    else:
        if a.dry:
            cmd += ["--dry"]
        if a.limit > 0:
            cmd += ["--limit", str(a.limit)]

    print(f"\n▶ 전용 클론에서 파이프라인 실행: {repo_path}")
    rc, output = run_streamed(cmd, cwd=str(repo_path))

    # 검증/테스트 실행(--dry·--test-video)은 결과 통지 없이 종료(레포·데이터 무변경).
    if a.dry or a.test_video:
        print(f"\n종료(rc={rc}). 데브 레포는 무변경(전용 클론에서만 작업).")
        return rc

    # 실제 반영 실행 → 결과 한 문장(터미널 + 텔레그램 동일 소스). 텔레그램은 토큰 없으면 조용히 스킵.
    if rc != 0:
        summary = f"✗ 밴도리 신곡 로더(로컬) — 오류 종료(rc={rc}), 반영 없음. 위 로그에서 원인 확인."
    elif "신곡 없음 — 종료(멱등)." in output:
        summary = "ℹ️ 밴도리 신곡 로더(로컬) — 신곡 0건, 처리할 것 없음(commit/push 없음, 정상)."
    else:
        m = re.search(r"반영 (\d+)곡 · 실패 (\d+)곡", output)
        if not m:
            summary = f"⚠️ 밴도리 신곡 로더(로컬) — 종료(rc={rc}), 결과 메시지 못 찾음. 로그 직접 확인 권장."
        else:
            landed, failed = int(m.group(1)), int(m.group(2))
            if landed > 0:
                tail = f" (실패 {failed}곡 — 다음 실행 재시도)" if failed else ""
                summary = (f"✅ 밴도리 신곡 로더(로컬) — {landed}곡 반영 완료{tail}. "
                           f"main push→deploy.yml 라이브 재배포(자동).")
            else:
                summary = f"⚠️ 밴도리 신곡 로더(로컬) — 신곡 {failed}곡 전부 실패, 반영 없음(push 안 됨). 로그 확인."

    print(f"\n{summary}")
    notify.send_telegram(summary)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
