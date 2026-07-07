"""Telegram 알림 — Bot API sendMessage (urllib, 무의존성). Actions·로컬 공용.

토큰/chat_id 출처(우선순위): ① 환경변수 TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID
(CI 는 secrets 로 주입) → ② 없으면 repo 루트 `.env`(로컬 편의; gitignore·python-dotenv 무의존,
youtube_api.load_env_key 와 동일 규약). 둘 다 없으면 조용히 스킵 → False 반환(호출부 무영향).
- 신곡 로더 반자동(옵션2): Actions 감지 워크플로우가 미처리 신곡 요약을 이걸로 전송한다.
- run_local.py 는 로컬 처리 완료/실패 결과를 이걸로 전송한다.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.telegram.org/bot{token}/sendMessage"
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"   # src/tools/semiauto-loader/<file> → repo root
_ENV_LOADED = False


def _load_env_once() -> None:
    """repo 루트 `.env` 의 KEY=VALUE 를 os.environ 로 로드(이미 있으면 유지 = 환경변수 우선).
    CI 는 `.env` 가 없고 secrets 로 env 가 이미 차 있어 no-op. 1회만 파싱."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        if k and k not in os.environ:
            os.environ[k] = v.strip().strip('"').strip("'")


def send_telegram(text: str, *, parse_mode: str | None = None, timeout: float = 15.0) -> bool:
    """Telegram 메시지 1건 전송. 성공 True. 토큰/chat_id 없거나 실패 시 False(예외 안 냄)."""
    _load_env_once()
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
