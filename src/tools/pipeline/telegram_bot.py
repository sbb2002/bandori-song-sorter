"""Telegram 명령 봇 — GitHub Actions getUpdates 기반 파이프라인 제어.

상시 서버가 없어(반자동) Telegram 명령을 CI에서 수신·처리한다(.github/workflows/pipeline.yml
맨 앞 단계 — 매일 23:00 KST 단일 크론에서 "명령 수신·처리 → 감지 → 알림"을 한 실행으로 수행,
2026-07-07 통합: 이전의 별도 5분 폴러는 제거됨). **인가된 chat_id(TELEGRAM_CHAT_ID) 메시지만**
처리한다(그 외 무시 = 보안). public 레포라 Actions 분(minutes)은 무제한·무료.

명령:
  /help    — 명령어 설명
  /status  — 크론 주기 + 트리거 가능(활성/일시정지) 상태
  /pause   — 일일 감지 크론 일시정지(봇 폴러는 계속 동작 → /resume 수신 가능)
  /resume  — 일시정지 해제

※ /detect 는 deprecated(제거). 감지는 pipeline.yml 일일 크론이 처리 후(= 봇이 미리 받은
pause/resume 등을 반영한 뒤) 자동 수행하므로 수동 트리거가 필요 없다.

일시정지 상태 = actions/bot_state.json {"paused": bool}. 변경 시 pipeline.yml 이 [skip ci]
커밋한다. 같은 실행의 감지 단계는 이 파일을 읽어 paused 면 감지·알림을 건너뛴다.

offset 은 로컬에 저장하지 않는다 — 처리 후 getUpdates(offset=last+1) 로 Telegram 서버에 ack →
다음 실행은 새 명령만 받는다(무상태 재개; 크래시로 재처리돼도 모든 명령은 멱등).

한 폴링에 여러 명령이 밀려 들어온 경우, 아직 처리 안 한 명령들 중 /pause 뒤에 /resume 이
순서대로 1쌍을 이루면 서로 상쇄되는 조작이므로 둘 다 무효 처리(응답·상태변경 없이 skip)한다.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # src/tools/pipeline/<file> → repo root
sys.path.insert(0, str(ROOT / "src" / "tools" / "pipeline"))

import notify                                        # noqa: E402  (Telegram 전송, urllib 무의존)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STATE_PATH = ROOT / "actions" / "bot_state.json"
CRON_DESC = "매일 23:00 KST (cron 0 14 * * *) — 명령 처리·감지·알림 단일 실행"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

HELP = (
    "🤖 밴도리 신곡 로더 봇\n"
    "\n"
    "/help — 이 도움말\n"
    "/status — 크론 주기·트리거 상태\n"
    "/pause — 일일 감지 크론 일시정지\n"
    "/resume — 일시정지 해제\n"
    "\n"
    "※ 신곡 반영(다운로드~배포)은 로컬에서 run_local.py 로 실행합니다."
)


def api(method: str, params: dict | None = None) -> dict:
    """Telegram Bot API 호출(JSON POST)."""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(params).encode("utf-8") if params else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def reply(text: str) -> None:
    """인가 chat(=TELEGRAM_CHAT_ID)으로 응답. notify.send_telegram 재사용."""
    notify.send_telegram(text)


def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"paused": False}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


# ── 명령 핸들러 (상태 미변경) ──

def cmd_help() -> None:
    reply(HELP)


def cmd_status() -> None:
    paused = load_state().get("paused", False)
    trig = "⏸ 일시정지(감지 대기)" if paused else "▶ 활성"
    reply(f"📊 상태\n· 트리거: {CRON_DESC}\n· 감지: {trig}")


# ── 상태 변경 핸들러 (True = bot_state.json 변경됨) ──

def cmd_pause() -> bool:
    st = load_state()
    if st.get("paused"):
        reply("⏸ 이미 일시정지 상태입니다.")
        return False
    st["paused"] = True
    save_state(st)
    reply("⏸ 일일 감지 크론을 일시정지했습니다. /resume 으로 재개하세요.")
    return True


def cmd_resume() -> bool:
    st = load_state()
    if not st.get("paused"):
        reply("▶ 이미 활성 상태입니다.")
        return False
    st["paused"] = False
    save_state(st)
    reply("▶ 일일 감지 크론을 재개했습니다.")
    return True


HANDLERS = {"/help": cmd_help, "/status": cmd_status}
STATE_HANDLERS = {"/pause": cmd_pause, "/resume": cmd_resume}


def _cmd_of(text: str) -> str:
    """'/pause@BotName arg' → '/pause'."""
    return text.strip().split()[0].lower().split("@", 1)[0]


def _emit_state_changed() -> None:
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write("state_changed=true\n")


def main() -> int:
    if not TOKEN or not CHAT_ID:
        print("[bot] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 없음 — 종료")
        return 1

    try:
        updates = api("getUpdates", {"timeout": 0}).get("result", [])
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"[bot] getUpdates 실패: {e}")
        return 1
    print(f"[bot] getUpdates: {len(updates)}건 수신", flush=True)
    if not updates:
        return 0

    last_id = 0
    queue: list[str] = []
    for u in updates:
        last_id = max(last_id, u.get("update_id", 0))
        msg = u.get("message") or u.get("edited_message") or {}
        chat = str((msg.get("chat") or {}).get("id", ""))
        text = msg.get("text", "") or ""
        if chat != str(CHAT_ID):
            print(f"[bot] 무시(비인가 chat={chat})")
            continue
        if not text.startswith("/"):
            print(f"[bot] 비명령 메시지 skip: {text[:20]!r}")
            continue
        queue.append(_cmd_of(text))

    # 미처리 명령 중 /pause → /resume 이 순서대로 1쌍을 이루면 서로 상쇄(무효 처리).
    cancelled: set[int] = set()
    cancelled_pairs = 0
    pending_pause: list[int] = []
    for i, cmd in enumerate(queue):
        if cmd == "/pause":
            pending_pause.append(i)
        elif cmd == "/resume" and pending_pause:
            j = pending_pause.pop()
            cancelled.add(j)
            cancelled.add(i)
            cancelled_pairs += 1

    for _ in range(cancelled_pairs):
        reply("⏸▶ /pause·/resume 이 함께 도착해 서로 상쇄되어 무효 처리했습니다"
              "(상태 변경 없음).")

    state_changed = False
    for i, cmd in enumerate(queue):
        if i in cancelled:
            print(f"[bot] 명령: {cmd} (pause/resume 상쇄 — skip)")
            continue
        print(f"[bot] 명령: {cmd}")
        if cmd in HANDLERS:
            HANDLERS[cmd]()
        elif cmd in STATE_HANDLERS:
            state_changed = STATE_HANDLERS[cmd]() or state_changed
        else:
            reply(f"❓ 알 수 없는 명령: {cmd}\n/help 로 목록 확인")

    # ack: 처리분(<= last_id) 확정 → 다음 실행은 새 명령만
    try:
        api("getUpdates", {"offset": last_id + 1, "timeout": 0})
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"[bot] ack 실패(다음 실행 재처리 가능): {e}")

    if state_changed:
        _emit_state_changed()                        # 워크플로우가 bot_state.json 커밋
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
