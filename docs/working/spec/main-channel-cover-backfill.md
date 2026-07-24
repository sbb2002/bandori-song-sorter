# 설계: 메인 채널 歌ってみた(커버) 백필 확장

## 배경 (읽고 시작할 것)

레포: `C:\Users\User\Documents\pyworks\bandori-song-sorter` (이 레포에서만 작업. `bandori-playlist-maker`는 건드리지 않는다).

이 레포는 각 밴드마다 YouTube가 자동 생성하는 **"<Band> - Topic" 채널**(음원만 올라오는 채널)을
`BAND_CHANNELS` 딕셔너리(`src/tools/collect/youtube_rss.py:95`)로 감시한다. 여기엔 이미
두 갈래 파이프라인이 있다:

1. `youtube_rss.py` — RSS(최근 ~15~20개)로 매일 신곡 감지 → PR 자동 생성. (건드리지 않음)
2. `backfill.py` + `insert_backfill.py` — Data API(`fetch_uploads`, 페이징 전체 조회)로
   Topic 채널의 **과거 업로드 전체**를 훑어 RSS가 놓친 백로그를 찾는 반자동 도구.
   - `backfill.py [band...]` : 후보를 **출력만** 한다(데이터 미변경).
   - 사람이 출력을 보고 `src/tools/collect/new_songs.csv`에 수동으로 행을 추가한다
     (컬럼: `song_name,url,type,author,note,comment`, `type`은 `original`|`cover`).
   - `insert_backfill.py [--cover] [--apply]` : `new_songs.csv`를 읽어 각 밴드
     `src/content/songs/<band>.yaml`에 삽입한다(dry-run 기본, `--apply`로 실기록).

## 문제

사용자가 예로 든 곡 `【 歌ってみた 】唱 / Ado【 covered by 仲町あられ・峰月律 】`
(video_id=`zVdR0urFjnc`)은 **Topic 채널이 아니라 밴드의 메인(공식) 채널**에만 올라와 있다.
`mugendai_mutype`의 경우:

- Topic 채널(현재 `BAND_CHANNELS["mugendai_mutype"]`) = `UCeXzCxZsDcaF5xI68fK5owA`
  ("Mugendai MewType - Topic", 45개 업로드, 음원만).
- 메인 채널(현재 미등록) = `UCxL_Vlnhfo46sN6vPHR_4hA` ("夢限大みゅーたいぷ", 248개 업로드,
  공식 MV·라이브영상·생방송·미니애니·잡담쇼츠·**歌ってみた(커버)** 등 다 섞여 있음).

`backfill.py mugendai_mutype`를 실제로 실행해 확인함 — 이 곡은 등록된 Topic 채널
45개 업로드 안에 없다(신규 0, namedup 21, variant제외 1). 즉 **Topic 채널만 보는 현재 구조로는
이 커버곡이 영원히 감지되지 않는다.**

메인 채널의 실제 업로드 250개를 전수 조사한 결과(스크래치패드
`mutype_main_uploads.txt` 참고), 콘텐츠가 매우 다양하다:
- `【Official Music Video】...` / `【Animation Music Video】...` — 이미 아는 곡의 다른 영상(존재하는
  곡명과 매칭되어 `known_names`로 자동 dedup됨, 문제 없음).
- `【ライブ映像】...`, `【Dance Practice】...` — variant_tag가 `live` 등으로 잡아 자동 제외됨.
- **문제**: 미니애니(`ミニアニメ...`), 잡담/퀴즈 쇼츠, 생방송 다시보기, CM, Chronicle Movie,
  라디오 등은 `variant_tag()`가 인식하는 키워드가 전혀 없어 **기본값 `""`(= "완전판 오리지널
  곡"으로 간주)로 폴스루**된다. 즉 Topic 채널 전제로 만들어진 `variant_tag`의 블랙리스트 방식
  필터를 메인 채널에 그대로 적용하면, 노래가 아닌 잡담/애니/쇼츠 영상이 "신곡"으로 오탐된다.
- 반면 **실제 歌ってみた 커버**는 8개 확인됨(전부 제목에 `歌ってみた`가 정확히 포함, 예:
  `【 歌ってみた 】唱 / Ado【 covered by 仲町あられ・峰月律 】`,
  `【歌ってみた】ビッグマウス feat.りむる【真新宿GR学園(電音部)×夢限大みゅーたいぷ】` 등).

## 설계 결정: 블랙리스트가 아니라 화이트리스트

메인 채널은 콘텐츠 종류가 계속 늘어난다(생방송 다시보기, 라디오, 신규 이벤트 포맷 등) —
아직 안 나온 새 잡담/이벤트 포맷을 전부 블랙리스트로 선제 차단하는 건 지속 불가능하고
위험하다(하나라도 빠지면 오탐 데이터가 곡 데이터셋에 섞임). 대신 **"제목에 '歌ってみた'가
포함된 경우만 후보로 본다"는 화이트리스트**를 쓴다. 실측 250개 중 실제 커버곡 8개가 전부
이 마커를 갖고 있었고, 이 마커가 없는 나머지 242개 중에는 커버곡이 하나도 없었다 —
이 채널·기간에 한해 정밀도 100%로 검증된 필터다.

메인 채널 스캔의 목적은 "이 채널의 모든 노래 콘텐츠"가 아니라 **딱 사용자가 요청한
"歌ってみた 시리즈 커버곡"**으로 좁힌다. 오리지널 곡은 이미 Topic 채널 경로로 전부
커버되므로 메인 채널에서 오리지널까지 다시 찾을 필요는 없다.

## 변경 범위 (파일 1개만 수정: `src/tools/collect/backfill.py`)

`youtube_rss.py`, `insert_backfill.py`, `youtube_api.py`는 **수정하지 않는다** —
전부 기존 그대로 재사용(import)한다. 새 코드는 `backfill.py` 안에만 추가한다.

### 1. 새 상수: 메인 채널 맵

```python
# 밴드의 메인(공식) 채널 — Topic 채널과 별개. 아직 mugendai_mutype만 확인됨(2026-07-25,
# 사용자 요청으로 조사). 나머지 11개 정식 밴드의 메인 채널 id는 미조사 상태 — 여기 추가하기
# 전에 반드시 YouTube Data API channels.list 등으로 실제 채널이 맞는지 확인할 것(추측 금지,
# 잘못된 채널을 넣으면 엉뚱한 콘텐츠가 그 밴드 데이터로 잘못 들어갈 위험).
BAND_MAIN_CHANNELS = {
    "mugendai_mutype": "UCxL_Vlnhfo46sN6vPHR_4hA",
}

# 메인 채널 스캔 전용 화이트리스트 마커. Topic 채널(BAND_CHANNELS)이 아니라 메인 채널은
# 노래 외 콘텐츠(생방송·잡담쇼츠·미니애니·CM 등)가 다수라 variant_tag()의 블랙리스트 방식이
# 안전하지 않다(미인식 제목은 전부 "오리지널 곡"으로 폴스루됨). 이 마커가 제목에 있는
# 경우만 커버곡 후보로 본다(실측 mutype 250개 업로드 전수조사에서 정밀도 100% 확인).
_COVER_SERIES_MARKERS = ("歌ってみた",)


def is_cover_series_title(title: str) -> bool:
    """제목에 '歌ってみた' 마커가 있으면 True (NFKC 정규화 후 부분일치)."""
    import unicodedata
    t = unicodedata.normalize("NFKC", title or "")
    return any(m in t for m in _COVER_SERIES_MARKERS)
```

(`import unicodedata`는 함수 안이 아니라 파일 상단 import 블록으로 옮겨도 된다 — 기존
파일 스타일에 맞춰서 배치할 것. 기존 `backfill.py`에 `unicodedata` import가 없으면 상단에
추가.)

### 2. `main()`의 밴드별 루프 수정

현재 구조(요약, 실제 줄번호는 `backfill.py` 파일 참고):

```python
for band in bands:
    uploads = fetch_uploads(BAND_CHANNELS[band], key)
    known_ids = ids_by_band.get(band, set())
    known_names = names_by_band.get(band, set())
    new, namedup, variant_drop, seen = [], [], [], set()
    for u in uploads:
        ... (기존 필터링 로직 — 그대로 둔다)
    ... (출력)
```

**메인 채널도 같은 dedup 상태(`known_ids`/`known_names`/`seen`)를 공유**해야 한다 — 안 그러면
메인 채널의 Official MV가 Topic 채널 쪽에서 이미 known_names로 잡혔는데 메인 채널 쪽에서
다시 "신규"로 뜨는 이중집계가 생긴다. 따라서 **Topic 루프가 끝난 직후, 같은 밴드의
`known_ids`/`known_names`/`seen`을 이어받아서** 메인 채널을 추가로 훑는 방식으로 짠다.

의사코드(정확한 변수명·삽입 위치는 실제 파일 읽고 맞출 것):

```python
for band in bands:
    uploads = fetch_uploads(BAND_CHANNELS[band], key)
    known_ids = ids_by_band.get(band, set())
    known_names = names_by_band.get(band, set())
    new, namedup, variant_drop, seen = [], [], [], set()

    for u in uploads:
        # (기존 Topic 채널 루프 — 그대로)
        ...

    # ── 메인 채널 추가 스캔(歌ってみた 화이트리스트만) ──
    main_new = []
    main_ch = BAND_MAIN_CHANNELS.get(band)
    if main_ch:
        try:
            main_uploads = fetch_uploads(main_ch, key)
        except APIError as e:
            print(f"[{band}] ‼️ 메인 채널 API 오류: {e}")
            main_uploads = []
        for u in main_uploads:
            if u["video_id"] in known_ids:
                continue
            if not is_cover_series_title(u["title"]):
                continue                      # 화이트리스트 미통과 → 스캔 대상 아님
            kn = norm_name(u["title"])
            if kn in known_names:
                namedup.append((u, "cover")); continue
            if kn in seen:
                continue
            seen.add(kn)
            main_new.append((u, "cover"))     # variant는 강제 'cover' (마커 자체가 커버 확정)

    total_new += len(new) + len(main_new)
    ...
```

- `main_new`의 variant는 `variant_tag()`를 호출하지 말고 **무조건 `"cover"`로 고정**한다.
  이유: `variant_tag()`는 영어 "cover"(예: "covered by") 부분일치로만 커버를 인식하는데,
  실측 데이터 중 `【歌ってみた】ビッグマウス feat.りむる【真新宿GR学園(電音部)×夢限大みゅーたいぷ】`처럼
  "covered by"가 없는 제목도 있다. 이미 `is_cover_series_title()`로 커버 확정이므로
  variant를 다시 추론할 필요가 없다.
- **길이 필터 추가**: 오탐 방어로 `youtube_rss.MIN_LENGTH_S`(90초) 이상만 후보로 남긴다.
  `main_new`로 넘어가기 전, 화이트리스트를 통과한 항목에 한해서만(전체 업로드가 아니라
  좁혀진 소수에 대해서만) `youtube_rss.fetch_length_seconds(video_id)`를 호출해 90초 미만이면
  `variant_drop`에 추가하고 건너뛴다. (`fetch_length_seconds`는 `youtube_rss.py`에 이미 있음 —
  import해서 재사용, 재구현 금지.)
- 출력 시 메인 채널 후보는 `new`와 합쳐서 출력하되, 어느 채널에서 왔는지 사람이 구분할 수
  있게 태그를 붙인다. 예: 출력 줄에 `[MAIN]` 접미사를 붙이거나, `(u, var)` 튜플 대신
  `(u, var, source)`로 확장해서 출력 시 `source == "main"`이면 `[MAIN]` 표시.
  (`new_songs.csv`에 넣을 때 사람이 `type=cover`로만 적으면 되고 채널 출처는 안 남겨도 무방 —
  단, 콘솔 출력에서는 검토자가 "이거 메인 채널에서 새로 찾은 거구나"를 알 수 있어야 한다.)
- summary 표(`band, upl, new, namedup, var제외`)에도 메인 채널 분량이 섞여 합산되는 건
  괜찜음 — 단, `upl` 컬럼은 Topic 채널 업로드 수만 의미가 헷갈리지 않게 하려면
  `upl(main)` 같은 부가 컬럼을 추가하거나, 최소한 총합 라인에 "(메인 채널 스캔: N개 밴드)"
  같은 안내를 덧붙인다. 표 포맷을 크게 바꾸지 말고 최소 변경으로.

### 3. 하지 말아야 할 것 (중요 — 서브에이전트 실수 방지)

- `youtube_rss.py`의 `BAND_CHANNELS`, `variant_tag`, `KEEP_VARIANTS`, RSS 데일리 크론 경로는
  **절대 건드리지 않는다**. 이번 변경은 `backfill.py` 전용(반자동/저빈도 수동 실행 경로)이다.
- `insert_backfill.py`는 채널 출처를 몰라도 되므로 **수정 불필요**. `new_songs.csv`에
  `type=cover,author=mugendai_mutype`로만 적으면 기존 `insert_backfill.py --cover --apply`가
  그대로 처리한다.
- `BAND_MAIN_CHANNELS`에 **mutype 외 다른 밴드를 추측해서 채워 넣지 말 것.** 나머지 11개
  밴드는 메인 채널 id가 검증되지 않았다(이번 작업 범위 밖). 빈 채로 두거나 mutype 하나만
  넣는다.
- 기존 Topic 채널 루프의 동작(변수명, 출력 포맷, `KEEP_VARIANTS` 필터링 로직 등)은 **한 글자도
  바꾸지 않는다** — 순수 추가(additive)만 한다.
- 새 의존성(yt-dlp 등) 추가 금지. 기존처럼 `youtube_api.fetch_uploads`(Data API, stdlib)만 쓴다.

### 4. 검증 방법 (구현 후 내가 직접 확인함 — 서브에이전트는 아래를 실행해서 결과만 콘솔에 보여줄 것)

```
cd src/tools/collect
python backfill.py mugendai_mutype
```

기대 결과: 출력에 `zVdR0urFjnc`(唱/Ado 커버)를 포함해 최소 8개의 `[MAIN]` 커버 후보가
`신규 후보`로 나와야 하고, 미니애니/잡담쇼츠/생방송 등은 후보에 전혀 나오면 안 된다.
`backfill.py`(다른 밴드 인자 없이 전체 실행)도 한 번 돌려서 기존 11개 밴드의 Topic 채널
출력이 이전과 동일하게(회귀 없이) 나오는지 확인할 것 — `BAND_MAIN_CHANNELS`에 mutype만
있으므로 다른 밴드는 출력이 전혀 안 바뀌어야 정상이다.

## 이후 단계 (이번 작업 범위 아님, 참고만)

1. 이 PR 반영 후 `python backfill.py mugendai_mutype` 출력을 사람이 보고
   `new_songs.csv`에 8곡을 `type=cover,author=mugendai_mutype`로 수동 추가.
2. `python insert_backfill.py --cover --apply mugendai_mutype` 로 yaml에 실기록.
3. 이 레포(`bandori-song-sorter`)에 커밋(일반 PR 플로우).
4. 머지 후 `bandori-playlist-maker`의 기존 autoloader(`tools` 브랜치)가 다음 실행 시
   `origin/main` diff로 이 8곡을 자동 감지 — 그쪽은 **아무 코드 변경도 필요 없다**
   (`sources.py`의 `detect_new`가 video_id 기준으로 이미 처리).
5. 나머지 11개 밴드의 메인 채널 id 조사는 별도 작업으로 분리(이번 범위 아님).
