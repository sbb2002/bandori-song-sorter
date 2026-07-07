# semiauto-loader

신곡 로더 반자동 파이프라인의 로컬·CI 공용 코드. CI(GitHub Actions, 데이터센터 IP)에서는
YouTube 다운로드가 봇월로 막혀서(세션 27 실증) **감지·명령 처리·알림만 CI**가 하고,
**실제 다운로드~main 반영은 로컬**(레지덴셜 IP)에서 수행한다.

## 어떤 상황에 어떤 파일을 실행하나

| 상황 | 실행 | 비고 |
|---|---|---|
| 텔레그램으로 "신곡 N곡 감지" 알림을 받았다 → 로컬에 반영하고 싶다 | `python src/tools/semiauto-loader/run_local.py` | 인자 없이 실행하면 미처리 신곡 **전체**를 자동 감지해 다운로드→demucs→pulse→좌표까지 처리 후 `main`에 commit·push. 처리 후 `deploy.yml`이 자동 배포. |
| 이번엔 최대 N곡만 처리하고 싶다 | `python src/tools/semiauto-loader/run_local.py --limit N` | 나머지는 다음 실행에서 이어서 처리(멱등). |
| push 없이 먼저 검증만 해보고 싶다 | `python src/tools/semiauto-loader/run_local.py --dry` | 다운로드~좌표까지 처리하되 commit/push 생략. |
| 곡 1개로 파이프라인이 끝까지 도는지만 확인하고 싶다(E2E) | `python src/tools/semiauto-loader/run_local.py --test-band <밴드> --test-video <video_id 또는 URL>` | `--dry` 강제 적용 — 레포 데이터 불변. |
| 텔레그램 봇 명령(`/help`·`/status`·`/pause`·`/resume`)을 로컬에서 즉석으로 처리해보고 싶다 | `python src/tools/semiauto-loader/telegram_bot.py` | 보통은 `.github/workflows/pipeline.yml`이 매일 23:00 KST에 자동 실행 — 로컬 실행은 디버깅용. `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` 환경변수 필요. |
| 다른 스크립트에서 텔레그램 메시지만 보내고 싶다 | `notify.send_telegram(text)` (직접 실행 파일 아님) | urllib만 사용하는 무의존 헬퍼. 토큰/chat_id 없으면 조용히 스킵(`False` 반환). `run_local.py`·`telegram_bot.py`·`actions/orchestrate.py`가 공용으로 import. |

## 격리 원칙

`run_local.py`는 **전용 로컬 클론**(기본 `../bandori-pipeline`)에서만 자동 git 활동(commit·push)을
수행한다 — 지금 작업 중인 데브 레포와 워킹트리를 공유하지 않기 위함. 클론이 없으면 최초 실행 시
자동으로 만든다.

## 사전조건

오디오 스택(yt-dlp·node·torch/demucs·librosa·ffmpeg)이 설치된 환경 + `origin`에 push 가능한
git 자격 증명. 자세한 아키텍처는 [`docs/working/HANDOFF.md`](../../../docs/working/HANDOFF.md)
작업 3 섹션 참고.
