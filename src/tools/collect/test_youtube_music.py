"""
youtube_music 오프라인 테스트 (네트워크 없음). 실행:
  python src/tools/collect/test_youtube_music.py   (또는 pytest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import youtube_music as ym  # noqa: E402

CH = "UCtest"


def _item(title, subtitle, bid):
    return {"musicTwoRowItemRenderer": {
        "title": {"runs": [{"text": title}]},
        "subtitle": {"runs": [{"text": subtitle}]},
        "navigationEndpoint": {"browseEndpoint": {"browseId": bid}}}}


def _row(vid, title, artist=None):
    cols = [{"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": title}]}}}]
    if artist is not None:
        cols.append({"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": artist}]}}})
    return {"musicResponsiveListItemRenderer": {"flexColumns": cols,
                                                "playlistItemData": {"videoId": vid} if vid else {}}}


ARTIST = {
    "header": {"musicImmersiveHeaderRenderer": {"title": {"runs": [{"text": "Poppin'", "text2": ""}, {"text": "Party"}]}}},
    "contents": [
        {"musicCarouselShelfRenderer": {   # 무관한 선반: 무시되어야 함
            "header": {"musicCarouselShelfBasicHeaderRenderer": {"title": {"runs": [{"text": "関連アーティスト"}]}}},
            "contents": [_item("Other", "2026年", "MPREb_IGNORED")]}},
        {"musicCarouselShelfRenderer": {   # 더보기 버튼이 있는 앨범 선반
            "header": {"musicCarouselShelfBasicHeaderRenderer": {
                "title": {"runs": [{"text": "アルバム"}]},
                "moreContentButton": {"buttonRenderer": {"navigationEndpoint": {
                    "browseEndpoint": {"browseId": "MORE1", "params": "PARAMS1"}}}}}},
            "contents": [_item("Stale", "2019年", "MPREb_OLD")]}},   # 더보기가 있으니 여기 것은 안 씀
        {"musicCarouselShelfRenderer": {   # 더보기 없는 싱글/EP 선반
            "header": {"musicCarouselShelfBasicHeaderRenderer": {"title": {"runs": [{"text": "シングルと EP"}]}}},
            "contents": [_item("BRAVE JEWEL", "シングル • 2026年", "MPREb_SINGLE"),
                         _item("Old single", "2024年", "MPREb_SINGLE_OLD")]}},
    ],
}
MORE = {"contents": [
    _item("Album New", "アルバム • 2026年", "MPREb_ALB"),
    _item("Album Mid", "2025年", "MPREb_2025"),
    _item("Album Ancient", "2019年", "MPREb_2019"),   # 연도 필터로 제외 → 트랙 조회 금지
    _item("HHW Single", "2026年", "MPREb_HHW"),
]}
ALBUMS = {
    "MPREb_ALB": {"contents": [_row("a1", "Alb One"), _row(None, "No vid"), _row("s1", "BRAVE JEWEL (Poppin'Party ver.)", "Poppin'Party")]},
    "MPREb_2025": {"contents": [_row("a3", "Mid Track")]},
    "MPREb_SINGLE": {"contents": [_row("s1", "BRAVE JEWEL (Poppin'Party ver.)", "Poppin'Party")]},
    "MPREb_SINGLE_OLD": {"contents": [_row("x9", "Old")]},   # 2024년 → 제외 (선반 contents 경로)
    "MPREb_HHW": {"contents": [_row("h1", "Hello Happy Track", "ハロー、ハッピーワールド！")]},
}
def _search_row(title, subtitle, bid):   # 검색 결과는 musicResponsiveListItemRenderer 행 형태
    return {"musicResponsiveListItemRenderer": {
        "flexColumns": [{"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": title}]}}},
                        {"musicResponsiveListItemFlexColumnRenderer": {"text": {"runs": [{"text": subtitle}]}}}],
        "navigationEndpoint": {"browseEndpoint": {"browseId": bid}}}}


SEARCH = {"contents": [
    _search_row("Cover Collection", "アルバム • Various Artists • 2026年", "MPREb_COMP1"),
    _search_row("Old Collection", "アルバム • Various Artists • 2024年", "MPREb_COMPOLD"),
]}
ALBUMS.update({
    "MPREb_COMP1": {"contents": [_row("c1", "Cover A", "Roselia"), _row("c2", "Cover B", "Afterglow")]},
})
CALLS = []


def fake_post(endpoint, body):
    CALLS.append((endpoint, body))
    if endpoint == "search":
        return SEARCH
    if body["browseId"] == CH:
        return ARTIST
    if body["browseId"] == "MORE1":
        assert body.get("params") == "PARAMS1", body
        return MORE
    return ALBUMS[body["browseId"]]   # 미등록 ID면 KeyError → 잘못된 조회 감지


def test_artist_entries():
    ym._post = fake_post
    CALLS.clear()
    name, entries = ym.fetch_artist_entries(CH, 2025)
    assert name == "Poppin'Party", name
    ids = [e["video_id"] for e in entries]
    # 2025/2026 릴리스만, s1은 두 앨범에 중복 → 1번만, videoId 없는 행 제외
    assert ids == ["a1", "s1", "a3", "h1"], ids
    by = {e["video_id"]: e for e in entries}
    assert by["s1"]["title"] == "BRAVE JEWEL (Poppin'Party ver.)"
    assert by["s1"]["artist"] == "Poppin'Party"
    assert by["a1"]["artist"] is None           # 두 번째 열 없음 → None
    assert by["h1"]["artist"] == "ハロー、ハッピーワールド！"   # "、"로 쪼개지 않음
    assert all(e["published"] == "" for e in entries)
    # 더보기 경로 호출 확인 + 2019/2024 릴리스는 조회되지 않음
    browsed = [b["browseId"] for ep, b in CALLS if ep == "browse"]
    assert "MORE1" in browsed and "MPREb_2019" not in browsed and "MPREb_SINGLE_OLD" not in browsed
    assert "MPREb_IGNORED" not in browsed


def test_compilation_entries():
    ym._post = fake_post
    CALLS.clear()
    c = ym.fetch_compilation_entries(2025)
    assert [e["video_id"] for e in c] == ["c1", "c2"], c
    assert {e["artist"] for e in c} == {"Roselia", "Afterglow"}
    assert "MPREb_COMPOLD" not in [b["browseId"] for ep, b in CALLS if ep == "browse"]
    assert CALLS[0][1]["params"] == ym.COMPILATION_PARAMS


if __name__ == "__main__":
    test_artist_entries()
    test_compilation_entries()
    print("ok: youtube_music tests passed")
