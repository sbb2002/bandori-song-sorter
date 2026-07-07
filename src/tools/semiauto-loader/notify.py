"""Telegram 알림 — Bot API sendMessage (urllib, 무의존성). Actions·로컬 공용.

env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
- 둘 중 하나라도 없으면 조용히 스킵(로컬 개발 편의) → False 반환.
- 신곡 로더 반자동(옵션2): Actions 감지 워크플로우가 미처리 신곡 요약을 이걸로 전송한다.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(text: str, *, parse_mode: str | None = None, timeout: float = 15.0) -> bool:
    """Telegram 메시지 1건 전송. 성공 True. 토큰/chat_id 없거나 실패 시 False(예외 안 냄)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("  [notify] TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 없음 -> 알림 스킵")
        return False

    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    req = urllib.request.Request(
        API.format(token=token),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ok = bool(json.loads(resp.read().decode("utf-8")).get("ok"))
        print("  [notify] Telegram 전송 성공" if ok else "  [notify] Telegram 응답 ok=false")
        return ok
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"  [notify] Telegram 전송 실패: {e}")
        return False
