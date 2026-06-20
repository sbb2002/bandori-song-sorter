# HANDOFF: bandori-song-sorter UI 개편

## Status: v2.0 곡 단위 개편 — **구현 완료** (실브라우저 확인 일부 보류)

앨범 드래그 방식을 폐기하고 곡 단위 소팅으로 전면 재작성 완료. 밴드 셀렉터 → 곡 리스트 → 랭크 팝업 플로우.

## 구현 내용

**아키텍처** (정적 파이프라인 유지, GitHub Pages 호환)
- `data/*.yaml`(앨범 소스, 미변경) → `build.py`(앨범→곡 평탄화 + `window.SONG_DATA` 주입) → `index.html` + vanilla JS/CSS
- YAML 포맷·`tools/converter.py` CSV 워크플로 그대로 유지. 곡 평탄화는 빌드 시 수행, 중복 제거는 클라이언트(core.js).

**파일**
- `static/js/core.js` (신규) — 순수 로직(중복제거·히스토그램·히트맵·링크생성·진행률), 브라우저+Node 듀얼 export
- `static/js/script.js` (재작성) — Pointer 통합 프레스, 모달 팝업, 필터칩, YT 연동, 탭, localStorage, 공유
- `templates/index_template.html` (재작성) — 목업 5영역 골격 + 데이터 주입
- `static/css/style.css` (재작성) — 다크 테마 + 반응형(≤1023px 세로 스택)
- `build.py` (수정) — 곡 평탄화(곡마다 `band` 포함), JSON 주입
- `tests/core.test.js` + `package.json` (신규) — `node --test` 16개

## 확정된 결정
- **디자인**: `docs/bandori-song-sorter-mockup.html`을 주 디자인으로 채택. 현재 앱의 검증된 조각(밴드 아이콘, YT IFrame API, 롱프레스 350ms, domtoimage, fixPath) + 모바일 반응형 + localStorage를 결합.
- **티어**: 최애(1)/차애(2)/호(3)/중간(4)/불호(5). 같은 티어 재선택 시 해제. 이모지 💖💕👍😐👎.
- **곡 중복**: 밴드 내 제목 기준 중복 제거(URL 유효 항목 우선). 488곡 → 445곡.
- **저장**: localStorage(`bandori-song-ranks-v1`). 새로고침/재방문 유지.
- **인터랙션**: 짧게=유튜브 재생, 길게(350ms)·우클릭=랭크 팝업. PC/모바일 Pointer 이벤트로 통일.
- **공유**: 링크복사(현재 밴드+티어 필터 반영, DC인사이드 링크+빈줄 형식) / Download(전 밴드 히스토그램+히트맵 PNG).

## 범위 조정 (계획 대비)
- **Download PNG는 전 밴드 전체 분포**를 담음(티어 필터 무시). 통계 이미지에 필터 적용 시 반쪽 차트가 되어 UX상 부적절. 티어 선택 공유 의도는 **링크 복사**(필터 반영)가 담당.
- PRD의 공유 미리보기 모달(스토리 16)은 차후 확장 보류.

## 검증 상태
- ✅ `node --test` 16/16 통과 (중복제거·집계·링크 생성)
- ✅ `python build.py` 성공 (밴드 13, 곡 488→445)
- ✅ 헤드리스 스크린샷: 데스크톱 / 히스토그램(데이터) / 히트맵 / 랭크 팝업 모달 / 모바일 — 전부 정상 렌더
- ✅ **유튜브 실제 재생** — GitHub Pages 실브라우저(PC·모바일)에서 정상 확인
- ✅ **Download PNG 생성** — dom-to-image 캡처 정상 동작 확인 (scale:2 화질 개선 포함)
- ✅ **링크 복사** — clipboard 정상 동작 확인
- ✅ **모바일 전반** — GitHub Pages에서 PC·모바일 레이아웃 및 롱터치 동작 정상 확인

## Notes
- 원본 보존: `backup/main-before-redesign` 브랜치.
- 빌드/테스트: `python build.py` / `npm test`(=`node --test`).
- 데이터 수정 시 `data/*.yaml` 편집 후 `python build.py` 재실행.

---

# 세션 2 (2026-06-20) — UI 개편 및 버그 수정

## 완료된 작업

### PC UI
- 유튜브 패널 위치: 곡 리스트 하단 → **우측** (`.center`: `grid-template-rows` → `grid-template-columns: 1fr 1.5fr`)
- `body`/`.app` `height: 100vh` 고정 → **페이지 전체 스크롤 제거** (모바일은 `height: auto` 유지)
- 하단 바에 **진행률 프로그레스 바** 추가 (`#bp-fill`, `#bp-pct`)
- 랭크 팝업 **키보드 단축키**: `1`~`5` 티어 설정(토글), `Esc` 취소

### 모바일 UI
- 롱터치 애니메이션: `requestAnimationFrame` + `--lp` → **CSS transition** (`right: 100%→0`, 350ms)으로 교체 (GPU 가속)
- `touch-action: pan-y` → **`touch-action: none`**, `pointermove`에서 `list.scrollTop -= dy`로 수동 스크롤 구현
- `setPointerCapture`로 리스트 밖 드래그 시에도 이벤트 보장
- `pointercancel` 핸들러 제거 (네이티브 롱프레스 간섭 차단)
- `* { -webkit-tap-highlight-color: transparent }` — **탭 하이라이트(파란 박스) 제거**

### 기능 추가
- **밴드 셀렉터 순서 고정** (`BAND_ORDER` 배열, 미포함 밴드는 뒤에 추가)
- **다운로드 밴드 사진**: 최애→차애→호→불호 낮음 순 베스트 밴드 자동 선택, `assets/(band)/band.png` 삽입 (하단 그라디언트 블러)
- **다운로드 화질 개선**: 이미지 완전 로드 후 캡처 (`Promise.all` + `onload`), `scale: 2` 적용
- `assets/*/band.png`, `band.webp` 전 밴드 추가
- `backup/main-20260620` 백업 브랜치 생성

## 다음 세션에서 할 작업

### 1. 컨버터 수정 (`tools/converter.py`)
- `data/(밴드).yaml` ↔ `(밴드).csv` 상호 변환 도구
- yaml 구조 변경 여부 확인 후 csv 변환 로직 동기화

### 2. YouTube RSS 신곡 자동 등록
- BanG Dream Official 유튜브 채널 RSS 구독
- 신곡 감지 시 곡명·링크·출시일자를 yaml/csv에 자동 등록 후 푸시
- 기존 곡에 출시일자 등 메타데이터 추가 → 1번 컨버터와 병행 필요

### 3. README.md 재작성
- **사용자 관점**으로 전면 재작성 (현재는 개발자 관점)
- 웹페이지 조작법, 결과물(링크·히트맵·다운로드) 공유 방법, 키보드 단축키 안내 포함

---

# 세션 3 (2026-06-20) — 컨버터 / RSS 신곡 탐지기 / README

세션 2의 "다음 세션에서 할 작업" **1·2·3 모두 완료**하고 main에 푸시.
커밋: `74fdc04`(README) · `9549098`(컨버터) · `b912fea`(RSS 탐지기) · `5d5624f`(README URL fix)

## 완료된 작업

### 1. 컨버터 (`tools/converter.py`)
- 점검 결과 **yaml 구조는 세션 2에서 안 바뀜** → 기존 CSV 로직 정상(afterglow.csv도 yaml과 일치).
- 다만 `yaml_to_csv`가 컬럼 하드코딩이라 새 트랙 필드(예: `release_date`)를 **누락**하던 문제 → **동적 컬럼**으로 수정. 빈 옵션필드는 yaml에서 생략, 날짜는 문자열로 인용.
- 검증: afterglow 라운드트립 **바이트 동일(무회귀)** + release_date 라운드트립 통과.

### 2. RSS 신곡 탐지기 (`tools/youtube_rss.py`, 신규)
- **방식 전환**: 곡들이 전부 밴드별 **"<Band> - Topic" 채널**(YouTube Music 자동 생성, 음원만 업로드)에서 옴을 확인 → 원래 계획(공식채널 1개 + 수동 배정) 대신 **밴드별 Topic RSS 구독**으로 변경. 밴드 자동 배정 + 곡만 필터 + 출시일이 공짜로 해결.
- 무료·무API키·무AI·무외부의존(urllib + xml + PyYAML). 13밴드 채널ID는 `BAND_CHANNELS`에 하드코딩. `various_artists`(etc.yaml)는 단일 Topic 없어 제외.
- 정책: 기존곡(영상ID + 곡명 정규화) · seen 원장으로 신규만. **TV Size/Short/live/instrumental 제외, 풀버전(무태그) + 커버([cover] 태그)만**, 같은 곡 중복 업로드는 곡명 기준 1개(풀버전·최초발매일 우선). `release_date`=영상 게시일.
- 실행 결과: 신규 후보 **72건**(풀버전 25 + 커버 47)을 `tools/rss_inbox.csv`로 staging.
- 운영: `--dry`(쓰기X·확인용) / 인자없음(inbox·seen 기록) / `--show`(피드 덤프). 생성물(`rss_inbox.csv`·`rss_seen.json`·`__pycache__`)은 `.gitignore`.

### 3. README (`readme.md`)
- 사용자 관점 전면 재작성(라이브 링크·5단계 표·단축키·필터·공유·모바일·간결한 개발자 섹션).
- 라이브 URL이 `sbb2005`(→404)로 잘못 들어가 있던 것 발견 → **`sbb2002`** 로 수정. 저장소 소유자/원격 = `github.com/sbb2002`, 라이브 = https://sbb2002.github.io/bandori-song-sorter/

## ✅ 사용자가 체크할 사항
- [o] 라이브 사이트 정상 동작: https://sbb2002.github.io/bandori-song-sorter/ (`index.html` 미변경이라 그대로일 것)
- [o] GitHub에서 README 렌더링·링크 확인 (라이브 링크 클릭 시 404 아닌지)
- [o] `tools/rss_inbox.csv` 72건 검토 — 실제로 넣을 곡/커버 선별 -- 코멘트 : csv 확인해보니 name에 '~~ (Cover)'라고 적혀있는데, 이름에서 '(Cover)'는 지워. 그리고 곡 리스트에서 정렬할 때 일반곡(variant='')을 시간순으로 배열하고, 그 뒤에 커버곡(variant='cover')인 것을 시간순을 배열해줘.
    → **반영 완료**: `youtube_rss.py`에 정렬 추가 — **일반곡 25곡(출시일 오름차순) → 커버 47곡(출시일 오름차순)**. 이름의 `(Cover)`는 **그대로 유지**(사용자가 커버곡임을 눈으로 구분하도록 — 초기엔 제거했다가 되돌림). 기존 inbox·seen도 동일 정렬 반영(라이브 재요청 없이 검토하신 72건 그대로). ※ '시간순'을 오래된→최신(오름차순)으로 해석함 — 최신순을 원하면 정렬 키만 뒤집으면 됨.
- [o] (선택) 컨버터 동작 확인: `python tools/converter.py yaml2csv data/roselia.yaml` 후 생성 CSV 확인
- [o] (선택) `python tools/youtube_rss.py --dry` 실행해 탐지 결과 눈으로 확인 -- 결과 내용 : 
    ```
    C:\Users\User\Documents\pyworks\bandori-song-sorter>python tools\youtube_rss.py --dry
    band               feed  known  NEW
    --------------------------------------
    afterglow            15     51    0
    ave_mujica           15     22    0
    hello_happy_world    15     49    0
    ikka_dumb_rock        1      1    0
    millsage              1      1    0
    morfonica            15     34    1
    mugendai_mutype      15     21    0
    mygo                 15     35    0
    pastel_palettes      15     44    0
    poppin_party         15     86    1
    raise_a_suilen       15     43    0
    roselia              15     46    0
    --------------------------------------
    TOTAL NEW CANDIDATES: 2

    New song candidates:
    morfonica        2026-04-21 | ビューティ・フォー
    poppin_party     2026-01-13 | START!! True dreams

    (--dry: no files written)
    ```

## 남은 작업
- **신곡 반영**: inbox에서 고른 곡을 `data/*.yaml`에 추가 → `python build.py`. 곡별로 `album_title/numbering/img_url`을 직접 정해야 함(Topic 음원엔 앨범 정보 없음). 추가 후엔 seen 원장이 재탐지를 막아줌.
- **(선택) 자동화**: `youtube_rss.py`를 GitHub Actions 크론으로 → 신곡을 검토용 PR로 올리기(검토 후 푸시). 로컬 우선 결정이라 미구현.
- **(별개 트랙) UI 미해결**: `docs/comments/comment-02.md` 참고 — 모바일(삼성인터넷·크롬) 롱터치 반응성 이슈가 아직 열려 있음(히트박스 위치 의심). 이번 세션 범위 밖.

---

# 세션 4 (2026-06-20) — 코드베이스 구조 정리

`assets/`·`data/` 등이 규칙 없이 흩어져 있어 점검 후 단계적으로 정리. **0단계 완료**, 1단계는 미수행(아래 필수 과정 기록).

## 확정된 결정 (점검 후 사용자 선택)
- **에셋 레이아웃 = 종류별**: `assets/icons/` · `assets/bands/` · `assets/albums/<band>/`. (현재는 아이콘만 종류별, 나머지는 밴드별로 혼재)
- **앨범 커버(aNN/mNN)는 legacy 보존**(삭제 X). 현 v2 곡 단위 UI는 앨범 커버를 화면에 **안 씀**(build.py가 `SONG_DATA.img`로 주입하지만 script.js가 안 읽음). v1(`docs/index.html`) 전용 흔적.
- `assets/icon/undefined.png` → `_fallback.png`로 개명 예정.

## 0단계 완료 (커밋됨)
- `data/roselia.csv`·`tools/afterglow.csv` 제거(converter 산출물, `data/*.yaml`이 원본).
- `.gitignore`: 생성 CSV 일원화(`data/*.csv`, `tools/*.csv`).
- `assets/README.md` 신규: 종류별 레이아웃·네이밍 규칙·밴드 추가 체크리스트·현재→목표 이전 계획.

## 1단계 (필수) — assets/ 종류별 재배치 — ✅ 완료 (2026-06-20)

**결과**: `git mv` 65 rename(아이콘 14 + 단체사진 12 + 앨범 39) + 15 삭제로 종류별 재배치 완료. `static/js/script.js` 2곳 · 전 `data/*.yaml` `img_url` · `index.html` 재빌드(곡 488) 동시 반영. 무결성 검증 통과 — 고유 `img_url` 40개 전부 추적 파일로 연결, 밴드 아이콘 13개 존재, `index.html`에 구 경로 0개(이전 세션에서 stale했던 빌드를 재빌드로 교정). `various_artists`는 `bands/` 단체사진이 원래 없음(회귀 아님). jpg 3개(`raise_a_suilen/a02` · `various_artists/{chispa,glitter_green}`) 미변환 잔존. `docs/index.html` v1은 구 경로 하드코딩이라 깨짐 → 아카이브 미결. **라이브 아이콘/단체사진 표시는 푸시 후 사용자 확인 필요.**

아래는 원래 계획(기록 보존):

**파일 이동** (가능하면 `git mv`로 이력 보존):
- `assets/icon/<band>.png` → `assets/icons/<band>.png` (폴더명 단수→복수)
- `assets/icon/undefined.png` → `assets/icons/_fallback.png`
- `assets/<band>/band.png` → `assets/bands/<band>.png`
- `assets/<band>/band.webp` → **삭제**(미사용 — script.js는 png만 씀)
- `assets/<band>/{a,m}NN.{webp,jpg}` → `assets/albums/<band>/...` (legacy 보존)
- `assets/etc/*`(various_artists 서브유닛 커버) → `assets/albums/various_artists/...`
- `assets/<band>/temp.*`(ikka_dumb_rock, millsage) → 삭제하거나 실제 커버로 교체
- 포맷 통일: jpg(`raise_a_suilen/a02.jpg`, `etc/*.jpg`) → webp 권장

**코드·데이터 동시 수정**(안 하면 라이브 깨짐):
- `static/js/script.js` 2곳:
  - `bandIcon()`(≈45행): `'assets/icon/' + band + '.png'` → `'assets/icons/' + band + '.png'` (+ onerror fallback을 `_fallback.png`로)
  - 다운로드(≈750행): `'assets/' + bestBand + '/band.png'` → `'assets/bands/' + bestBand + '.png'`
- `data/*.yaml` 전 파일 `img_url`: 새 `assets/albums/<band>/...` 경로로 일괄 수정, `assets/icon/undefined.png` → `assets/icons/_fallback.png`
- `python build.py` 재실행 → `index.html` 갱신
- **검증**: 로컬·라이브에서 밴드 아이콘(셀렉터·히트맵)·다운로드 단체사진 정상 표시 확인. 앨범 커버는 v2 미표시라 경로만 안 깨지면 됨.

**주의**:
- `docs/index.html`(옛 v1)은 `assets/<band>/{a,m}NN` 하드코딩 + `raise_a_suiren` **오타**(실제 suilen)로 이미 일부 깨짐. 재배치하면 더 깨지므로 → `docs/legacy/`로 아카이브하거나 방치(라이브 아님). **결정 필요.**
- 슬러그에 한글/특수문자 금지(URL 인코딩 이슈). `numbering` 기반 영문 슬러그 권장(예: `1st_one-of-us.webp`).

## 2단계 (별개·선택) — 데이터 품질
구조 정리와 무관한 데이터 스멜이라 1단계 차단 요인은 아님:
- 각 밴드 yaml의 `numbering: undefined / album_title: undefined` **더미 앨범** = 다른 앨범 곡의 중복본 + `url:` 빈 트랙. 현재 클라이언트 중복제거(core.js)에 의존. 정리 시 곡 수·중복 변동 → `npm test`로 회귀 확인.
- `url:` 빈 트랙(앱에서 ♪ 표시·재생 불가) 유지/제거 정책 결정.
