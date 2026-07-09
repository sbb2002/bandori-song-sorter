# 외부 서비스 유지보수 문서

이 앱(bandori-song-sorter)을 서비스하기 위해 의존하는 **외부 웹서비스** 목록과, 각 서비스가
끊기거나 키가 만료됐을 때 무엇을 확인해야 하는지 정리한다. 코드 자체의 작업 이력은
[../working/done.md](../working/done.md), 남은 작업은 [../working/HANDOFF.md](../working/HANDOFF.md) 참조.

## 한눈에 보기

| 서비스 | 역할 | 필요한 키 | 만료주기 | 문서 |
|---|---|---|---|---|
| GitHub Pages | 정적 사이트 호스팅(라이브 서비스) | 없음(저장소 설정값만) | 없음 | [github-pages.md](github-pages.md) |
| GitHub Actions | CI/CD — 배포·신곡 감지·알림 자동화 | 저장소 시크릿 3종(아래) | 시크릿 자체는 무만료 | [github-actions.md](github-actions.md) |
| Umami | 방문자 수 카운팅(analytics) | 없음(공개 website-id만) | 없음 | [umami.md](umami.md) |
| YouTube Data API v3 (Google Cloud Console) | 채널 업로드 조회·백필·RSS 장애 폴백 | `YOUTUBE_API_KEY` | 기본 무만료(수동 rotate 권장) | [youtube-data-api.md](youtube-data-api.md) |
| Telegram Bot API | 신곡 알림 + 원격 제어(/pause 등) | `TELEGRAM_BOT_TOKEN`·`TELEGRAM_CHAT_ID` | 기본 무만료 | [telegram-bot.md](telegram-bot.md) |

## 현재 등록된 GitHub Actions 시크릿 (2026-07-09 기준)
`gh secret list`로 이름만 확인 가능(값은 조회 불가):
- `TELEGRAM_BOT_TOKEN` — 2026-07-06 등록
- `TELEGRAM_CHAT_ID` — 2026-07-06 등록
- `YOUTUBE_API_KEY` — 2026-07-09 등록(세션 32 핫픽스, `hotfix/auto-loader`)

## 장애 시 우선 확인 순서
1. **GitHub Actions 탭**에서 최근 실행 로그 확인(`pipeline.yml`=신곡 감지·알림, `deploy.yml`=배포).
2. 로그에 `[feed error]`/`404`/`quotaExceeded`/`401` 등이 있으면 아래 개별 문서의 "장애 시 확인"
   절 참조.
3. 외부 서비스 자체 장애(예: 세션 32 — YouTube legacy RSS 엔드포인트 전역 404, `docs/working/done.md`
   세션 32 참조)인지, 이 레포 키/설정 문제인지 구분 — 무관한 대상으로 재현되면 외부 장애 쪽에 무게.
4. 이 저장소는 `docs/working/urgent.md`에 서비스 차질급 사건을 기록한다(처리 후 done.md로 이관).
