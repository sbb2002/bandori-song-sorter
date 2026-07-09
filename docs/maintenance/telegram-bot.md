# Telegram Bot API

## 역할
- 신곡 감지 결과를 매일 Telegram 메시지로 알림(`src/tools/semiauto-loader/notify.py`).
- 원격 명령 처리: `/help`·`/status`·`/pause`(감지 크론 일시정지)·`/resume`
  (`src/tools/semiauto-loader/telegram_bot.py`). 상시 서버가 없어 매일 크론 실행 맨 앞 단계에서
  밀린 명령을 한 번에 수신·처리(폴링형, 상태는 `bot_state.json`에 `{"paused": bool}`만 저장).

## 필요한 키
- `TELEGRAM_BOT_TOKEN` — [BotFather](https://t.me/BotFather)에서 봇 생성 시 발급.
- `TELEGRAM_CHAT_ID` — 알림을 받을 채팅방(개인 DM 또는 그룹) ID. **인가된 chat_id 메시지만
  명령으로 처리**하고 그 외는 무시(보안 — 아무나 봇에게 `/pause`를 못 치게 함).

저장 위치: 로컬 `.env` + GitHub Actions 저장소 시크릿(2026-07-06 등록) — YouTube API 키와 동일한
2단 관리 구조.

## 만료주기
봇 토큰은 **기본 만료 없음** — BotFather에서 `/revoke` 하기 전까지 영구. `TELEGRAM_CHAT_ID`도
채팅방/계정이 살아있는 한 고정값.

## 장애 시 확인
1. 알림이 안 옴: `gh run view <run-id> --log`로 pipeline.yml의 "Handle Telegram commands"/
   "Detect new songs + notify" 스텝 로그 확인 — `[bot] getUpdates: N건 수신` 라인이 있어야 정상 폴링.
2. 명령(`/pause` 등)이 안 먹음: 그 메시지를 보낸 chat_id가 시크릿의 `TELEGRAM_CHAT_ID`와 일치하는지
   확인(불일치면 의도적으로 무시됨 — 보안 설계, 버그 아님).
3. `bot_state.json`이 `paused: true`로 멈춰 있으면 `/resume` 전까지 감지·알림이 전부 스킵됨(정상
   동작, 장애 아님) — Telegram으로 `/status` 보내서 현재 상태 확인 가능.
