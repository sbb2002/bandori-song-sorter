# GitHub Actions

## 역할
이 저장소의 CI/CD 전체를 담당하는 두 워크플로:

| 워크플로 | 트리거 | 하는 일 |
|---|---|---|
| `.github/workflows/pipeline.yml` | 매일 23:00 KST(14:00 UTC) 크론 + 수동(`workflow_dispatch`) | Telegram 명령 처리(`/help`·`/status`·`/pause`·`/resume`) → 신곡 감지(YouTube) → Telegram 알림. 다운로드는 안 함(세션 27에서 CI IP 봇월 확정 → 로컬 `run_local.py`가 집 IP에서 처리). |
| `.github/workflows/deploy.yml` | `main` push(`src/**`·`static/**`·`assets/**`) + 수동 | `index.html` 빌드 → GitHub Pages 배포. [github-pages.md](github-pages.md) 참조. |

## 필요한 키 (저장소 Settings → Secrets and variables → Actions)
- `TELEGRAM_BOT_TOKEN` — [telegram-bot.md](telegram-bot.md).
- `TELEGRAM_CHAT_ID` — [telegram-bot.md](telegram-bot.md).
- `YOUTUBE_API_KEY` — [youtube-data-api.md](youtube-data-api.md). 2026-07-09 등록(세션 32 핫픽스 —
  YouTube RSS 실패 시 폴백 경로에만 씀, 평소엔 호출 안 됨).
- `GITHUB_TOKEN` — **자동 제공**(별도 등록 불필요). `pipeline.yml`의 `permissions: contents: write`로
  `/pause`·`/resume` 상태 커밋 + `gh issue create`(RSS 파싱 이상 감지 시) 권한 확보.

## 만료주기
- 저장소 시크릿(위 3종) 자체는 **GitHub 쪽에서 만료시키지 않음** — 수동으로 rotate/삭제하기 전까지
  영구. 각 값의 유효성은 발급처(Telegram/Google) 정책을 따름(각 문서 참조).
- `GITHUB_TOKEN`은 잡(job) 단위로 자동 발급·자동 만료(매 실행마다 새로 생성, 실행 종료 후 무효화)
  — 유지보수 대상 아님.

## 점검 명령
```bash
gh secret list                 # 등록된 시크릿 이름·갱신일(값은 조회 불가)
gh run list --workflow=pipeline.yml --limit 5
gh run list --workflow=deploy.yml --limit 5
gh run view <run-id> --log     # 실패 로그 상세
```

## 장애 시 확인
1. `gh secret list`로 필요한 키가 다 등록돼 있는지부터 확인(하나라도 빠지면 해당 스텝만 조용히
   빈 값으로 동작하거나 에러 — 어떤 키가 어느 스텝에 쓰이는지는 워크플로 파일의 `env:` 블록 참조).
2. `pipeline.yml`은 `concurrency: cancel-in-progress: false`(중복 실행 대기), `deploy.yml`은
   `cancel-in-progress: true`(새 push가 이전 배포 취소) — 동작 다름에 유의.
3. 세션 32(2026-07-09) 사례: 신곡 감지가 전 밴드에서 실패 → 원인은 이 워크플로/시크릿 문제가
   아니라 YouTube 쪽 외부 장애였음(`docs/working/done.md` 세션 32). "이 저장소 설정 문제"와
   "외부 서비스 장애"를 구분해서 접근할 것.
