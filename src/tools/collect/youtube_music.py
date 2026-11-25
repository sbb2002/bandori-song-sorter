"""
YouTube Music 내부 웹 API 폴백 (bandori-song-sorter, youtube_rss 보조).

왜 있나: 2026-11 무렵부터 밴드 "- Topic" 채널의 RSS 피드가 HTTP 200이지만 <entry>가 0개로
온다(업로드 재생목록 소실, Data API도 404). 그래서 youtube_rss가 신곡을 전혀 못 잡는다.
이 모듈은 music.youtube.com 내부 웹 API(youtubei/v1)를 직접 호출해 아티스트 페이지의
앨범/싱글 목록과 트랙 videoId를 얻는다. 쿼터 무관, API 키 불필요.

주의: 비공식 내부 API라 언제든 구조가 바뀌거나 막힐 수 있다. 깨지면 예외가 올라가고,
youtube_rss 쪽에서 기존 anomaly 알람(유효 entry 0개 → health issue)으로 드러난다. 여기서 숨기지 않는다.
"""
import json
import re
import urllib.request

API = "https://music.youtube.com/youtubei/v1/{}?prettyPrint=false"
CTX = {"client": {"clientName": "WEB_REMIX", "clientVersion": "1.20241111.01.00", "hl": "ja", "gl": "JP"}}
COMPILATION_QUERY = "ガールズバンドパーティ カバーコレクション"
COMPILATION_PARAMS = "EgWKAQIYAWoMEA4QChADEAQQCRAF"   # 검색 필터: 앨범만
RELEASE_SHELVES = ("アルバム", "シングルと EP")       # 아티스트 페이지의 정규 릴리스 선반 제목


def _post(endpoint, body):
    body = dict(body, context=CTX)
    req = urllib.request.Request(API.format(endpoint), data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Origin": "https://music.youtube.com"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _walk(o, key):
    """o 안의 모든 dict를 재귀 탐색해 key의 값을 전부 생성한다."""
    if isinstance(o, dict):
        if key in o:
            yield o[key]
        for v in o.values():
            yield from _walk(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v, key)


def _texts(h):
    return "".join(x.get("text", "") for x in (h or {}).get("runs", []))


def _year(s):
    m = re.search(r"(\d{4})年", s or "")
    return int(m.group(1)) if m else None


def _col(r, i):
    try:
        return r["flexColumns"][i]["musicResponsiveListItemFlexColumnRenderer"]["text"]
    except (KeyError, IndexError, TypeError):
        return None


def _artist_name(d):
    for key in ("musicImmersiveHeaderRenderer", "musicResponsiveHeaderRenderer", "musicVisualHeaderRenderer"):
        for h in _walk(d, key):
            return _texts(h.get("title"))
    return ""


def _tracks(d):
    """앨범/싱글 페이지 → [(video_id, title, primary_artist or None)]. videoId 없는 행은 건너뜀."""
    out = []
    for r in _walk(d, "musicResponsiveListItemRenderer"):
        vid = (r.get("playlistItemData") or {}).get("videoId")
        if not vid:
            continue
        runs = (_col(r, 1) or {}).get("runs") or []
        # 단독 아티스트 곡은 두 번째 열이 없을 수 있음 → None. "、"로 쪼개지 않는다(밴드명 자체에 있음).
        artist = runs[0].get("text") if runs else None
        out.append((vid, _texts(_col(r, 0)), artist))
    return out


def fetch_artist_entries(channel_id, min_year):
    """아티스트(Topic 채널 id) 페이지의 앨범·싱글/EP 중 min_year 이상 릴리스의 트랙 목록.
    반환: (artist_name, [{"video_id", "title", "published": "", "artist"}]). 실패 시 예외."""
    d = _post("browse", {"browseId": channel_id})
    name = _artist_name(d)
    entries, seen = [], set()
    for car in _walk(d, "musicCarouselShelfRenderer"):
        h = car["header"]["musicCarouselShelfBasicHeaderRenderer"]
        if _texts(h.get("title")) not in RELEASE_SHELVES:
            continue
        more = (((h.get("moreContentButton") or {}).get("buttonRenderer") or {})
                .get("navigationEndpoint") or {}).get("browseEndpoint")
        if more:   # "더보기"가 있으면 전체 목록을 다시 받는다(선반에는 일부만 보임)
            body = {"browseId": more["browseId"]}
            if more.get("params"):
                body["params"] = more["params"]
            items = list(_walk(_post("browse", body), "musicTwoRowItemRenderer"))
        else:
            items = [c["musicTwoRowItemRenderer"] for c in car.get("contents", []) if "musicTwoRowItemRenderer" in c]
        for it in items:
            year = _year(_texts(it.get("subtitle")))
            if year is not None and year < min_year:
                continue   # 연도 파싱 실패는 포함(fail open), 명시된 과거 연도만 제외
            bid = it["navigationEndpoint"]["browseEndpoint"]["browseId"]
            for vid, title, artist in _tracks(_post("browse", {"browseId": bid})):
                if vid in seen:
                    continue
                seen.add(vid)
                entries.append({"video_id": vid, "title": title, "published": "", "artist": artist})
    return name, entries


def fetch_compilation_entries(min_year, queries=(COMPILATION_QUERY,)):
    """'Various Artists' 컴필레이션(아티스트 페이지에 안 뜸)을 검색으로 찾아 트랙 목록을 낸다.
    artist = 트랙의 주 아티스트명. min_year 미만·연도 파싱 실패 앨범은 제외."""
    entries, seen = [], set()
    for q in queries:
        d = _post("search", {"query": q, "params": COMPILATION_PARAMS})
        for r in _walk(d, "musicResponsiveListItemRenderer"):
            year = _year(_texts(_col(r, 1)))
            bid = ((r.get("navigationEndpoint") or {}).get("browseEndpoint") or {}).get("browseId")
            if not bid or year is None or year < min_year:
                continue
            for vid, title, artist in _tracks(_post("browse", {"browseId": bid})):
                if vid in seen:
                    continue
                seen.add(vid)
                entries.append({"video_id": vid, "title": title, "published": "", "artist": artist})
    return entries
