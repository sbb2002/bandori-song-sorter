"""
YouTube Data API v3 클라이언트 (stdlib 전용) — bandori-song-sorter.

youtube_rss.py 의 'no API key' 원칙은 RSS 자동수집(CI 일일 실행) 전용이고,
이 모듈은 **일회성/저빈도 조회**(조회수 수집 · 미추가 곡 백필)를 위해 API 키를 쓴다.
키는 .env 의 YOUTUBE_API_KEY (python-dotenv 없이 직접 파싱, 의존성 0).

무료 쿼터 10,000 units/day — 모두 1 unit/call:
  · videos.list        (조회수, 50개 배치)
  · channels.list      (업로드 재생목록 id)
  · playlistItems.list (업로드 전체, 50개 배치 페이징)
"""
import os
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
API_BASE = "https://www.googleapis.com/youtube/v3/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


class APIError(RuntimeError):
    pass


def load_env_key(name="YOUTUBE_API_KEY"):
    """.env 에서 KEY 값을 읽는다(환경변수 우선). 없으면 None."""
    if os.environ.get(name):
        return os.environ[name]
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    return None


def api_get(endpoint, params, key):
    q = dict(params)
    q["key"] = key
    url = API_BASE + endpoint + "?" + urllib.parse.urlencode(q, doseq=True)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise APIError(f"{endpoint} HTTP {e.code}: {body[:400]}")
    except Exception as e:
        raise APIError(f"{endpoint} 요청 실패: {e!r}")


def _batched(seq, n=50):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch_view_counts(vids, key):
    """{video_id: view_count(int)}. 통계 없는(비공개/삭제) 영상은 결과에서 누락."""
    out = {}
    for batch in _batched(list(vids), 50):
        data = api_get("videos", {"part": "statistics", "id": ",".join(batch)}, key)
        for it in data.get("items", []):
            vc = it.get("statistics", {}).get("viewCount")
            if vc is not None:
                out[it["id"]] = int(vc)
    return out


def uploads_playlist_id(channel_id, key):
    """채널의 업로드 재생목록 id (contentDetails.relatedPlaylists.uploads)."""
    data = api_get("channels", {"part": "contentDetails", "id": channel_id}, key)
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def fetch_uploads(channel_id, key):
    """채널 업로드 전체 → [{video_id, title, published}] (페이징, RSS 15개 한계 없음)."""
    pl = uploads_playlist_id(channel_id, key)
    if not pl:
        return []
    out, token = [], None
    while True:
        params = {"part": "snippet,contentDetails", "playlistId": pl, "maxResults": 50}
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", params, key)
        for it in data.get("items", []):
            cd = it.get("contentDetails", {})
            sn = it.get("snippet", {})
            vid = cd.get("videoId")
            if vid:
                out.append({
                    "video_id": vid,
                    "title": sn.get("title", ""),
                    "published": (cd.get("videoPublishedAt") or sn.get("publishedAt") or "")[:10],
                })
        token = data.get("nextPageToken")
        if not token:
            break
    return out
