"""신곡 로더 로컬 러너 — 전용 클론에서 다운로드~main push (반자동 옵션2).

CI(GitHub Actions = 데이터센터 IP)는 YouTube 다운로드가 봇월에 막힘이 실증됨(세션 27, E2E 3회
hard-block). 그래서 **다운로드는 집(레지덴셜 IP)에서 이 스크립트로** 수행한다. 다운로드 이후
(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트가 없어 그대로 자동으로 흐른다.

★격리: 자동화 git 활동(main 커밋·푸시)이 데브 핫픽스 작업과 얽히지 않도록 **전용 로컬 클론에서만**
실행한다(별개 브랜치로는 워킹트리를 공유해 격리가 안 됨). 데브 레포는 전혀 건드리지 않는다.

흐름:
  ① 전용 클론(--repo-path, 기본 ../bandori-pipeline) 없으면 origin 에서 clone
  ② fetch origin → checkout main → reset --hard origin/main   (오디오 캐시=gitignore, 보존→재개)
  ③ cwd=클론에서 `python actions/orchestrate.py [옵션]`:
       감지 → 다운로드(집 IP) → demucs/pulse → 좌표 append → commit → push origin main
  ④ deploy.yml 이 main push 를 받아 라이브 재배포(자동)

사전조건: 오디오 스택 env(yt-dlp·node·torch/demucs·librosa·ffmpeg)에서 실행 + git push 자격.

사용:
  python src/tools/pipeline/run_local.py                       # 감지→반영(실제 push)
  python src/tools/pipeline/run_local.py --limit 2             # 최대 2곡
  python src/tools/pipeline/run_local.py --dry                 # 처리하되 push 안 함(검증)
  python src/tools/pipeline/run_local.py --test-band afterglow --test-video 09B-WljIiTo  # E2E 1곡(dry 강제)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # src/tools/pipeline/<file> → repo root
PY = sys.executable

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

    cmd = [PY, "actions/orchestrate.py"]
    if a.test_video:
        cmd += ["--test-band", a.test_band, "--test-video", a.test_video, "--dry"]
    else:
        if a.dry:
            cmd += ["--dry"]
        if a.limit > 0:
            cmd += ["--limit", str(a.limit)]

    print(f"\n▶ 전용 클론에서 파이프라인 실행: {repo_path}")
    rc = run(cmd, cwd=str(repo_path), check=False).returncode
    if rc == 0 and not a.dry and not a.test_video:
        print("\n✅ 완료 — main push 시 deploy.yml 이 라이브 재배포(자동).")
    else:
        print(f"\n종료(rc={rc}). 데브 레포는 무변경(전용 클론에서만 작업).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
