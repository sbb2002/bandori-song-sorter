# DONE: bandori-song-sorter 완료 작업 기록

완료된 작업의 아카이브입니다. **남은·해야 할 작업은 [HANDOFF.md](HANDOFF.md)** 참조.

## 참고 사실 (작업 시 혼동 주의)
- **v2는 `band`·곡명(`name`)·`url`만 화면에 씀.** `album_title`·`img_url`은 **미표시**(script.js에 `album` 참조 없음, `img`는 다운로드 단체사진 전용). → 신곡/데이터 추가 시 앨범 메타는 yaml 정리용일 뿐 화면과 무관.
- 저장소/원격 = **github.com/sbb2002**, 라이브 = **https://sbb2002.github.io/bandori-song-sorter/**. (로컬 git user.name이 `sbb2005`라 과거 URL을 sbb2005=404로 잘못 적은 적 있음 → sbb2002가 정답.)
- 이 환경: **node 미설치**(npm test 불가), Pillow 12 있음. 셸은 PowerShell 주력 + Bash 병행.
- 원본 보존 브랜치: `backup/main-before-redesign`, `backup/main-20260620`.
- 빌드/테스트: `python build.py` / `npm test`(=`node --test`). 데이터 수정 시 `data/*.yaml` 편집 후 `python build.py` 재실행.

---

# 세션 1 — v2.0 곡 단위 개편 (구현 완료)

앨범 드래그 방식을 폐기하고 곡 단위 소팅으로 전면 재작성. 밴드 셀렉터 → 곡 리스트 → 랭크 팝업 플로우.

## 구현 내용
**아키텍처** (정적 파이프라인 유지, GitHub Pages 호환)
- `data/*.yaml`(앨범 소스) → `build.py`(앨범→곡 평탄화 + `window.SONG_DATA` 주입) → `index.html` + vanilla JS/CSS
- YAML 포맷·`tools/converter.py` CSV 워크플로 그대로. 곡 평탄화는 빌드 시, 중복 제거는 클라이언트(core.js).

**파일**
- `static/js/core.js` (신규) — 순수 로직(중복제거·히스토그램·히트맵·링크생성·진행률), 브라우저+Node 듀얼 export
- `static/js/script.js` (재작성) — Pointer 통합 프레스, 모달 팝업, 필터칩, YT 연동, 탭, localStorage, 공유
- `templates/index_template.html` (재작성) — 목업 5영역 골격 + 데이터 주입
- `static/css/style.css` (재작성) — 다크 테마 + 반응형(≤1023px 세로 스택)
- `build.py` (수정) — 곡 평탄화(곡마다 `band` 포함), JSON 주입
- `tests/core.test.js` + `package.json` (신규) — `node --test` 16개

## 확정된 결정
- **디자인**: `docs/spec/bandori-song-sorter-mockup.html`을 주 디자인으로 채택. 검증된 조각(밴드 아이콘, YT IFrame API, 롱프레스 350ms, domtoimage, fixPath) + 모바일 반응형 + localStorage 결합.
- **티어**: 최애(1)/차애(2)/호(3)/중간(4)/불호(5). 같은 티어 재선택 시 해제. 이모지 💖💕👍😐👎.
- **곡 중복**: 밴드 내 제목 기준 중복 제거(URL 유효 항목 우선). 488곡 → 445곡.
- **저장**: localStorage(`bandori-song-ranks-v1`). 새로고침/재방문 유지.
- **인터랙션**: 짧게=유튜브 재생, 길게(350ms)·우클릭=랭크 팝업. PC/모바일 Pointer 이벤트로 통일.
- **공유**: 링크복사(현재 밴드+티어 필터 반영, DC인사이드 링크+빈줄 형식) / Download(전 밴드 히스토그램+히트맵 PNG).

## 범위 조정 (계획 대비)
- **Download PNG는 전 밴드 전체 분포**를 담음(티어 필터 무시). 통계 이미지에 필터 적용 시 반쪽 차트가 되어 부적절. 티어 선택 공유는 **링크 복사**가 담당.
- PRD의 공유 미리보기 모달(스토리 16)은 차후 확장 보류.

## 검증 상태
- ✅ `node --test` 16/16 통과 (중복제거·집계·링크 생성)
- ✅ `python build.py` 성공 (밴드 13, 곡 488→445)
- ✅ 헤드리스 스크린샷: 데스크톱 / 히스토그램 / 히트맵 / 랭크 팝업 모달 / 모바일 — 전부 정상 렌더
- ✅ **유튜브 실제 재생** — GitHub Pages 실브라우저(PC·모바일) 정상 확인
- ✅ **Download PNG 생성** — dom-to-image 캡처 정상(scale:2 화질 개선 포함)
- ✅ **링크 복사** — clipboard 정상
- ✅ **모바일 전반** — GitHub Pages에서 PC·모바일 레이아웃 및 롱터치 동작 정상 확인

---

# 세션 2 — UI 개편 및 버그 수정 (완료)

## PC UI
- 유튜브 패널 위치: 곡 리스트 하단 → **우측** (`.center`: `grid-template-rows` → `grid-template-columns: 1fr 1.5fr`)
- `body`/`.app` `height: 100vh` 고정 → **페이지 전체 스크롤 제거** (모바일은 `height: auto` 유지)
- 하단 바에 **진행률 프로그레스 바** 추가 (`#bp-fill`, `#bp-pct`)
- 랭크 팝업 **키보드 단축키**: `1`~`5` 티어 설정(토글), `Esc` 취소

## 모바일 UI
- 롱터치 애니메이션: `requestAnimationFrame` + `--lp` → **CSS transition** (`right: 100%→0`, 350ms)으로 교체 (GPU 가속)
- `touch-action: pan-y` → **`touch-action: none`**, `pointermove`에서 `list.scrollTop -= dy`로 수동 스크롤 구현
- `setPointerCapture`로 리스트 밖 드래그 시에도 이벤트 보장
- `pointercancel` 핸들러 제거 (네이티브 롱프레스 간섭 차단)
- `* { -webkit-tap-highlight-color: transparent }` — **탭 하이라이트(파란 박스) 제거**

## 기능 추가
- **밴드 셀렉터 순서 고정** (`BAND_ORDER` 배열, 미포함 밴드는 뒤에 추가)
- **다운로드 밴드 사진**: 최애→차애→호→불호 낮음 순 베스트 밴드 자동 선택, `assets/(band)/band.png` 삽입 (하단 그라디언트 블러)
- **다운로드 화질 개선**: 이미지 완전 로드 후 캡처 (`Promise.all` + `onload`), `scale: 2`
- `assets/*/band.png`, `band.webp` 전 밴드 추가
- `backup/main-20260620` 백업 브랜치 생성

---

# 세션 3 — 컨버터 / RSS 신곡 탐지기 / README (완료·푸시)

세션 2의 "다음 세션 할 작업" 1·2·3 모두 완료하고 main에 푸시.
커밋: `74fdc04`(README) · `9549098`(컨버터) · `b912fea`(RSS 탐지기) · `5d5624f`(README URL fix)

## 1. 컨버터 (`tools/converter.py`)
- 점검 결과 **yaml 구조는 세션 2에서 안 바뀜** → 기존 CSV 로직 정상.
- `yaml_to_csv`가 컬럼 하드코딩이라 새 트랙 필드(예: `release_date`)를 누락하던 문제 → **동적 컬럼**으로 수정. 빈 옵션필드는 생략, 날짜는 문자열로 인용.
- 검증: afterglow 라운드트립 **바이트 동일(무회귀)** + release_date 라운드트립 통과.

## 2. RSS 신곡 탐지기 (`tools/youtube_rss.py`, 신규)
- 곡들이 전부 밴드별 **"<Band> - Topic" 채널**(YouTube Music 자동 생성, 음원만)에서 옴을 확인 → **밴드별 Topic RSS 구독**으로 결정. 밴드 자동 배정 + 곡만 필터 + 출시일 확보.
- 무료·무API키·무AI·무외부의존(urllib + xml + PyYAML). 13밴드 채널ID는 `BAND_CHANNELS`에 하드코딩. `various_artists`(etc.yaml)는 단일 Topic 없어 제외.
- 정책: 기존곡(영상ID + 곡명 정규화) · seen 원장으로 신규만. **TV Size/Short/live/instrumental 제외, 풀버전(무태그) + 커버([cover] 태그)만**, 같은 곡 중복 업로드는 곡명 기준 1개(풀버전·최초발매일 우선). `release_date`=영상 게시일.
- 정렬: **일반곡(출시일 오름차순) → 커버(출시일 오름차순)**. 이름의 `(Cover)`는 **유지**(사용자가 커버곡임을 눈으로 구분). 실행 결과 신규 후보 **72건**(풀버전 25 + 커버 47)을 `tools/rss_inbox.csv`로 staging.
- 운영: `--dry`(쓰기X) / 인자없음(inbox·seen 기록) / `--show`(피드 덤프). 생성물(`rss_inbox.csv`·`rss_seen.json`·`__pycache__`)은 `.gitignore`.

## 3. README (`readme.md`)
- 사용자 관점 전면 재작성(라이브 링크·5단계 표·단축키·필터·공유·모바일·간결한 개발자 섹션).
- 라이브 URL이 `sbb2005`(→404)로 잘못 들어가 있던 것 → **`sbb2002`** 로 수정.

## 사용자 확인 (전부 [o])
- [o] 라이브 사이트 정상 동작 / [o] README 렌더링·링크 확인
- [o] `tools/rss_inbox.csv` 72건 검토 — 위 정렬·`(Cover)` 유지 결정 반영 완료
- [o] (선택) 컨버터 동작 확인 / [o] (선택) `youtube_rss.py --dry` 결과 확인

---

# 세션 4 — 코드베이스 구조 정리 (0·1단계 완료·푸시)

`assets/`·`data/` 등이 규칙 없이 흩어져 있어 점검 후 단계적 정리.

## 확정된 결정
- **에셋 레이아웃 = 종류별**: `assets/icons/` · `assets/bands/` · `assets/albums/<band>/`.
- **앨범 커버(aNN/mNN)는 legacy 보존**(삭제 X). 현 v2는 앨범 커버를 화면에 안 씀(v1 전용 흔적).
- `assets/icon/undefined.png` → `_fallback.png`로 개명.

## 0단계 완료 (커밋됨)
- `data/roselia.csv`·`tools/afterglow.csv` 제거(converter 산출물).
- `.gitignore`: 생성 CSV 일원화(`data/*.csv`, `tools/*.csv`).
- `assets/README.md` 신규: 종류별 레이아웃·네이밍 규칙·밴드 추가 체크리스트.

## 1단계 완료 (커밋 `f6d5ce4`)
- `git mv` 65 rename(아이콘 14 + 단체사진 12 + 앨범 39) + 15 삭제로 종류별 재배치.
- 동시 수정: `static/js/script.js` 2곳(아이콘·단체사진 경로) · 전 `data/*.yaml` `img_url` · `index.html` 재빌드(곡 488).
- 무결성 검증 통과 — 고유 `img_url` 40개 전부 추적 파일로 연결, 밴드 아이콘 13개 존재, `index.html`에 구 경로 0개. `various_artists`는 `bands/` 단체사진이 원래 없음(회귀 아님).

---

# 세션 5 — RSS 72곡 반영 · docs v1 아카이브 · jpg→webp (작업 완료, 커밋은 사용자 보류)

세션 5 핸드오프(A~E)의 **A·B·C·D(jpg→webp) 완료**. 결정은 사용자 선택(RSS 전체 72 / docs 아카이브 / jpg→webp만).
> 이 시점에 **미커밋·미푸시** 상태로 두기로 함(사용자 베타테스트 중, 직접 커밋 예정). 커밋 대기 상세는 HANDOFF.md "현재 상태" 참조.

## 처리 내역
- **A. 라이브 검증**: 사용자 `[o]` 확인 완료(아이콘·단체사진 정상).
- **B. docs v1 아카이브**: `git mv docs/index.html → docs/legacy/index.html`(이력 보존). 라이브 아님(현 사이트는 루트 `index.html`). ※ `docs/ui/`·`docs/user_manual/`은 범위 밖이라 미변경.
- **C. RSS inbox 72곡 → yaml**: `tools/rss_inbox.csv`(풀버전 25 + 커버 47, 기존곡 제목충돌 **0건** 사전확인)를 밴드별로 append.
  - **구조 근거**: v2 화면은 `band`·곡명·`url`만 사용하고 `album_title`·`img_url`은 **표시 안 함**을 코드로 확인 → 신곡은 밴드별 **`numbering: 'Single'`(album_title `New Singles`)** + **`numbering: 'Cover'`(album_title `Covers`)** 두 블록으로 묶음. `img_url`=`assets/icons/_fallback.png`. `track_number`에 **출시일**을 넣어 provenance 보존(`rss_inbox.csv`는 `.gitignore`라 yaml이 유일 기록).
  - **정렬**: 밴드 내 *기존곡 → 신규 풀버전(출시일 오름차순) → 커버(출시일 오름차순)*. 커버는 곡명의 `(Cover)` 유지(사용자 결정).
  - **밴드별**: roselia 6+4, raise_a_suilen 5+7, poppin_party 4+5, morfonica 4+4, ave_mujica 3+0, mugendai 2+0, hello_happy 1+7, afterglow 0+7, pastel 0+9, mygo 0+4.
  - 결과: `python build.py` 곡 **488 → 560**(정확히 +72). index.html에 신곡·`(Cover)` 47회 주입 확인. 신곡은 이제 yaml "known"이라 `youtube_rss` 재탐지 안 됨.
- **D. jpg→webp 통일**: `raise_a_suilen/a02`·`various_artists/{chispa,glitter_green}` 3개를 Pillow로 webp 변환, 해당 yaml `img_url` 확장자 동기화. assets 내 jpg 잔존 **0**.

## 검증
- `python build.py` 성공(밴드 13, 곡 560).
- 무결성: 고유 `img_url` **40개 전부 추적 파일로 연결(누락 0)**, assets jpg 0, index.html에 구 jpg 경로 0, 신곡 주입 확인.
- `npm test`: **이 환경 node 미설치로 미실행**. `core.js`/`script.js`/`build.py`/테스트 **무수정**(데이터만 추가)이라 단위테스트 16개 무영향 → node 설치 후 재확인 권장.

---

# 세션 6 — ux-01 반영 (밴드 순서 · 곡 종류 탭) · 세션5·6 푸시

`docs/comments/ux-01.md` 유저 피드백 2건 반영. comment-02(PC 단축키·모바일 롱터치)는 **사용자가 전건 해결 확인** → HANDOFF #3 삭제.

## 처리 내역
- **밴드 셀렉터 순서 변경**: `static/js/script.js`의 `BAND_ORDER` 재정렬 → `poppin_party · afterglow · pastel_palettes · roselia · hello_happy_world · morfonica · raise_a_suilen · mygo · ave_mujica · mugendai_mutype · millsage · ikka_dumb_rock`. (실변경: roselia를 4번째로, morfonica를 raise 앞으로)
- **곡 리스트 상단 [ALL / Ori / Cover] 탭 추가**:
  - `templates/index_template.html`: `song-list-header` 아래 탭 버튼 3개(`data-type=all/ori/cover`).
  - `static/css/style.css`: `.song-type-tabs`/`.type-tab`(알약 톤, active 시 `--accent`).
  - `static/js/script.js`: `currentType` 상태 + `isCover()` 판별 + `viewSongs()` 필터 결합 + `switchType()` + init 바인딩. 밴드 선택·티어 필터와 AND 결합.
  - **커버 판별** = `album === 'Covers' || /\(cover\)/i.test(title)`. 현재 식별 가능 커버 = 세션5 RSS 반영분 **47곡**(album='Covers'와 (Cover) 제목 정확히 47개 일치). 기존곡 커버는 데이터상 미표시 → Ori로 분류. 기존곡 커버까지 잡으려면 해당 yaml에 `(Cover)` 표기/`Covers` 분류 추가 필요.

## 검증
- `python build.py` 성공 — 밴드 13, 곡 560(세션5 반영분 유지).
- 탭 3버튼 `index.html` 주입, 커버 47 / 오리지널 513 확인.
- 런타임(탭 클릭 필터·밴드순서 렌더): **사용자 직접 검수 완료(문제 없음)**.
- `npm test`: 이 환경 node 미설치로 미실행(로직 무관, 데이터·UI 추가).

## 커밋 · 푸시
- 작업 전 백업 브랜치 `backup/main-20260622`(세션5 미커밋 스냅샷 박제).
- 세션 5(RSS 560곡·docs v1 아카이브·앨범커버 jpg→webp)와 세션 6(ux-01)을 **함께 커밋 후 main 푸시**.
- `docs/user_manual/`(베타테스트 스크린샷)은 제외(untracked 유지).

---

# 세션 8 — ux-02 최애 밴드 스코어링 구현 (완료 · 푸시 대기)

`docs/comments/ux-02-ex1.md` 설계의 스코어링 공식을 코드로 반영. 미결 3건은 설계 권장안으로 확정.

## 확정한 미결 사항
- **τ = 3.5 고정**(`SCORE_TAU`). 문서 표와 일치(n=10에서 w≈0.94, 보정 거의 소멸). 동적 평균n 미채택.
- **0점 클램핑** `max(0, Score)` 적용. 단 **표시에서 미평가(n=0)는 `—`, 평가했으나 음수는 `0.00`** 으로 구분 → "불호 밴드 = 미평가 밴드 동일 취급" 우려를 시각적으로 분리(선정 로직은 둘 다 후보 제외/0점).
- **표시 포맷 `toFixed(2)`**(예: `1.70`). 정수·백분율 미채택.

## 구현 내용
- **`static/js/core.js`** — 아키텍처 원칙(순수 로직 → core + 테스트)대로 스코어링을 core에 신설.
  - `TIERS`에 `score` 필드 추가(최애 +4 · 차애 +3 · 호 +2 · 중간 +1 · 불호 -4).
  - `SCORE_TAU = 3.5` 상수.
  - `bandScores(songsByBand, ranks, tau?)` → `{ band: {score, raw, n} }`. R_k=Σ(s_t·c)/n, w=1-exp(-n/τ), Score=max(0, R·w). n=0이면 `{0,0,0}`.
  - `bestBand(...)` → 최고 score 밴드(n>0만 후보, 동점은 입력 순서 우선). 후보 없으면 null.
  - 셋 다 export.
- **`static/js/script.js`**
  - `findBestBand()` → `C.bestBand(dedupedByBand, ranks)` 위임(기존 r1→r2→r3→r5 사전식 정렬 폐기).
  - `buildCaptureDOM()` 밴드 헤더를 flex row로 교체(밴드명 좌 / 스코어 우, 미평가 `—`). `C.bandScores`로 표시.
- **`tests/core.test.js`** — TIER score 매핑 + bandScores(설계 예시 1.8 · n=0 · 클램핑 · 소표본 수축) + bestBand(최고점 · n=0 제외 · null · 동점) **7개 추가**.

## 검증
- `npm test`: **23/23 통과**(기존 16 + 신규 7). 이 환경 **node v24.13.0 설치 확인됨**(세션 1~6의 "node 미설치"와 달라짐).
- `node --check` core.js · script.js 구문 정상. **빌드 불필요**(index.html이 `./static/js/*.js`를 `src`로 로드).
- 라이브 캡처 이미지 렌더는 기존 워크플로대로 **사용자 직접 검수 예정**.

## 참고
- core.js는 `dedupSongs`의 dedup Map 키 구분자가 **NUL(0x00) 1바이트**(기존부터·HEAD에도 존재)라 git이 binary로 취급 → core.js diff가 라인 단위로 안 보임. 기능 무해(내부 키·미저장), 이번 변경과 무관(미수정).

## 푸시 · 머지 (대기)
- `feature/ux-02`에 **커밋만 완료, 푸시는 사용자 지시 대기**.

---

# 세션 9 — ux-02 2채널 신뢰도 막대 검토·조정 확정 · main 머지 (완료·푸시)

세션 8 스코어링에 이어 다른 장치에서 2채널 막대(`ab83f36`) 구현 → 이 장치에서 시각 검토·조정 후 **옵션 B(셀렉터순) 확정**, main 머지.

## 조정 내역 (사용자 검토 피드백)
- **막대 스타일**: 골드 `#ffd06b`·14px → **우유빛 회색 `#eaeaf2`·4px**(실선). '호' 티어색과 분리.
- **투명도**: 연속값 → **3단계 카테고리** `confidenceAlpha(n)`(유령 0.15 / 희미 0.6 / 불투명 1.0). 기준 w(n)=`core.confidence`.
- **(n/곡수)**: 막대 우측 → **score 바로 오른쪽** 회색 글씨. 막대는 풀폭(좌우 여백 동일).
- **밴드 나열 순서**: `bandsInSelectorOrder()` 헬퍼 추출(`BAND_ORDER`순 + 나머지 뒤) — **좌측 셀렉터 · Download 히스토그램 · Download 히트맵 · 메인 화면 히트맵** 4곳 공유. (기존 `bands`=yaml 파일명 알파벳순이라 `etc.yaml`의 various_artists가 'e' 위치로 떴던 문제 해소.)
- **밴드명 풀네임**: nameText `ellipsis` 제거 → 항상 풀네임(Afterglow 잘림 수정).
- **various_artists**: BAND_ORDER 미포함이라 항상 맨 끝. score·신뢰도 막대 미표시 + `findBestBand` 1위 후보에서 제외(여러 아티스트 묶음이라 최애 개념 없음).

## 선택지 비교
- **옵션 A**(랭크순 정렬·미평가 하단) → `feature/ux-02-opt-a` 브랜치(`d70ec2f`)에 백업 보존.
- **옵션 B**(셀렉터순) → **확정·채택**. 사용자 피드백 "히트맵을 셀렉터 순서로"(`docs/comments/ux-02.md`)와 일치.

## 검증
- `core.js` 미변경(`confidence`·`bandScores` 그대로) → 테스트 영향 없음. 변경은 전부 `script.js` UI 렌더부.

## 커밋 · 머지
- `feature/ux-02`에 조정 커밋 + 사용자 피드백 문서 `docs/comments/ux-02.md` 동반 → push.
- main은 `feature/ux-02`의 직접 조상 → **fast-forward 머지**(충돌 없음) → main push.
- `docs/user_manual/`(PNG 13장)은 별개 작업이라 이번 제외(untracked 유지).

## comments/ 정리 (완료 피드백 → done 이관 후 폴더 삭제)
작업 피드백 메모(`docs/comments/`)는 전부 완료되어 세션별 기록에 반영 완료 → 폴더 비움. 추적용 매핑:
- `comment-01.md` → 세션 2·4: PC 진행률 바 · 밴드 사진(원래 최애비율→차애→호→불호 순 판정, 후에 ux-02 스코어링으로 대체) · 모바일 롱터치 · 셀렉터 순서 초안.
- `comment-02.md` → 랭크 팝업 키보드 단축키(최애 1·차애 2·호 3·보통 4·불호 5·취소 Esc) + 모바일 롱터치 조사·종결.
- `ux-01.md` → 세션 6: 밴드 셀렉터 순서 확정 · 곡 `[ALL/Ori/Cover]` 탭.
- `ux-02.md` → 세션 8·9: **1·2번만 완료**(히트맵/밴드영역 셀렉터순(1) · 최애 밴드 스코어링·various 제외(2)). 3~7번은 당시 미구현 → HANDOFF로 이월(이후 **#7 재생중 표시는 세션 10 완료**, 나머지 #3~6은 HANDOFF에 잔존).
- `ux-02-ex1.md` → 세션 8: 스코어링 산출식 설계 — 티어점수(+4/+3/+2/+1/−4) · `R_k=Σ(s_t·c)/n` · `w(n)=1−exp(−n/τ)` · `τ=3.5` · `Score=max(0, R·w)`. 미결 3건(τ·0점클램핑·표시포맷) 모두 세션 8에서 확정.

---

# 세션 10 — ux-02.md #7: 현재 재생 중 곡 리스트 강조 (완료·푸시)

HANDOFF 1순위(난이도 최저·리스크 없음) 작업. 곡을 짧게 클릭(재생)하면 해당 행을 강조.

## 구현
- **`static/js/script.js`**: `nowPlaying`(songKey) 상태 추가. `playSong`에서 videoId 유효 시 `nowPlaying` 갱신 + `highlightPlaying()` 호출. `highlightPlaying()`은 리스트 재렌더 없이 해당 행만 `.playing` 토글(스크롤 유지). `renderSongList`는 행 생성 시 `nowPlaying` 비교해 `.playing` 부여 → 필터/탭/밴드 전환 후에도 강조 유지. 링크 없는 곡(재생 불가)은 `nowPlaying` 미갱신 → 직전 강조 유지.
- **`static/css/style.css`**: `.song-item.playing` — `--accent`(보라) 배경 `rgba(192,132,252,0.14)` + inset 1px 박스(0.45) + 제목 굵게. 티어색과 구분, hover보다 우선.

## 검증
- 사용자 브라우저 확인 "문제없이 잘됨". 빌드 불필요(index.html이 `./static/js/*.js`·css 외부 참조). 순수 추가, 기존 로직 무수정.

---

# 세션 11 — ux-02.md #6 / HANDOFF #1: 밴드 셀렉터 진행률 링 (완료·커밋, 푸시 대기)

셀렉터 아이콘 둘레를 **밴드 평가율(ranked/total)** 로 채우는 링. 색 게이트 **0~30% Red / 31~69% Yellow / 70%~ Green**.

## 구현
- **`static/js/script.js`**: `applyBandRing(ring, band)` = `C.countRanked(dedupedByBand[band], ranks)`로 pct 계산 → `--ring-pct` + 색 버킷 클래스(`low/mid/high`). `updateBandRings()`는 셀렉터 재생성 없이(아이콘 리로드 방지) 링만 갱신 → `refreshAll()`에 연결(팝업·키보드·리셋 등 모든 랭크 변경 경로가 수렴 → 실시간 반영). `makeBandBtn`은 밴드 버튼에만 링 삽입(**ALL 제외** — 전체 진행률은 헤더·하단 바가 담당), 아이콘 로드 실패 시 `img`만 교체해 링 보존.
- **`static/css/style.css`**: 링 스타일.

## conic → SVG 전환 (계단현상)
- **1차 conic-gradient + radial mask**(`e83c36f`): 가운데 투명 마스크로 아이콘 둘레만 링. 곡선 경계의 **하드 스톱이 AA가 안 돼 작은 링(3px)에서 계단현상**. 안쪽 1px 페더로 완화했으나 한계. → **`feature/ux-02-ring-conic` 브랜치에 백업**.
- **2차 SVG stroke 채택**(`1e9913c`): `<circle pathLength="100">` 트랙+채움 2원. `stroke-dasharray:100` + `stroke-dashoffset=calc(100-pct)`로 **pct가 곧 채움 길이**, `rotate(-90deg)`로 12시 시작·시계방향. 둘레가 벡터로 그려져 **항상 서브픽셀 AA → 계단현상 제거**. 애니메이션은 `stroke-dashoffset`(길이) 네이티브 보간이라 **`@property` 불필요**(conic 때보다 호환성↑). `applyBandRing`/`updateBandRings` 로직은 **무변경**(SVG도 `style.setProperty`·`classList` 동작). 사용자 브라우저 확인 "만족".

## 참고
- ⚠️ **70% Green은 링 색상일 뿐, "70% 이상만 최애 표시" 하드게이트는 미도입**(현 최애는 스코어링 수축으로만 선정 — 별도 결정 사안, HANDOFF에 잔존).
- (부수) `exportRanking` 실패 시 원인을 **`console.error`로 로깅**하도록 `.catch` 보강. 작업 중 사용자가 본 'Download 실패'는 **페이지를 `file://`로 직접 열어** 이미지 인라인용 XHR이 CORS(origin null)로 차단된 것 — **http(localhost)/https(Pages)에선 정상**, 코드 버그 아님(사용자 환경 실수로 종결).
- **검증**: `node --test` **25/25 통과**(`core.js` 무수정). 빌드 불필요(외부 `static/*` 참조).
- **푸시 대기**: `feature/ux-02`에 커밋만, 푸시는 사용자 지시 대기.

---

# 세션 12 — ux-02.md #3 / HANDOFF #1: 티어 팝업 Comment 란 (완료·푸시)

티어 팝업에 곡 **메모(코멘트)** 입력 → 곡 리스트에 말풍선 뱃지·툴팁. + 사용자 추가요청: **링크복사 시 코멘트 동반**.

## 구현
- **저장(가장 안전한 선택)**: `ranks`는 **무변경**, 별도 키 `bandori-song-comments-v1`(`{songKey: '메모'}`)에 보관 → `core.js` 스키마·집계 로직 전부 무영향. `loadComments/saveComments/getComment/setComment`(공백뿐이면 키 삭제 → 빈 메모 미보존).
- **`templates/index_template.html`**: 팝업에 `#popup-comment` textarea(maxlength 200, placeholder "메모 (선택 · 자동 저장)") + body에 `#comment-tip` 플로팅 툴팁. `build.py`로 index.html 재생성.
- **팝업 흐름**: `openPopup`이 기존 메모를 textarea에 로드. `commitComment()`는 **모든 닫기 액션(티어 선택·취소·Esc·오버레이)** 에서 저장 → 티어 없이 메모만 입력해도 보존. `applyTier()`로 티어 토글+메모 커밋+`refreshAll` 일원화. 메모 입력 중(`#popup-comment` 포커스) 숫자키 티어 단축키 비활성(메모에 숫자 허용).
- **말풍선 뱃지·툴팁**: `renderSongList`에서 코멘트는 행 `dataset.comment`로 항상 보존, **뱃지(💬)는 티어 확정+코멘트 있을 때만** 티어뱃지 옆 생성(요구사항대로 미확정 시 뱃지 X). 표시는 **호버(데스크톱, `(hover:hover)` 미디어쿼리 게이트) / 말풍선 탭(모바일)**. 툴팁은 리스트 `overflow` 클리핑 회피 위해 **body에 `position:fixed`**, JS가 앵커 위/아래·뷰포트 클램프로 위치. 스크롤·리사이즈·재렌더·바깥 탭 시 숨김. 말풍선 탭은 press 핸들러 최상단에서 가로채 재생/팝업 진입 차단.
- **링크복사(추가요청)**: `core.js buildShareLinks(songs, comments)`로 확장 — 코멘트 있으면 `URL\n코멘트`, 곡 사이 빈 줄. `comments` 인자 생략 시 기존 동작(하위호환). `copyLinks`가 `comments` 전달.

## 사용자 피드백 반영 (2건, 푸시 전)
1. **버그 — 메모만 수정 후 취소로 닫으면 메인 화면 미갱신**: 원인 = 취소/Esc/오버레이 닫기 경로가 `commitComment`(localStorage 저장)는 하지만 `renderSongList`를 안 불러 행 `dataset.comment`가 옛 값(팝업 재오픈 시엔 localStorage서 읽어 최신값 → 증상 일치). 해결 = `commitComment()`가 **실제 변경 여부 반환**, `closePopup()`이 변경됐을 때만 `renderSongList()`(코멘트는 리스트에만 영향 → `refreshAll` 대신 경량). 티어 경로는 `applyTier`가 이미 커밋·refresh → `closePopup`에선 "변경 없음" 판정되어 중복 렌더 없음.
2. **UX — 메모 텍스트 드래그 선택 중 팝업 밖에서 마우스 릴리스 시 팝업 닫힘**: 원인 = 오버레이 닫기가 `click` 이벤트인데, `click`은 mousedown·mouseup의 **공통 조상**에 발생 → 텍스트박스(안)에서 시작해 오버레이(밖)서 떼면 공통 조상=오버레이라 닫힘. 해결 = `click` 대신 **`pointerdown`+`pointerup`이 둘 다 오버레이일 때만 닫기**(모달 표준 관용구). 텍스트 시작→밖 릴리스, 반대(밖 시작→안 릴리스) 모두 보호. 롱프레스로 팝업 여는 순간은 리스트가 포인터 capture 중이라 자동 닫힘 없음(이중 안전).

## 검증
- `node --test` **27/27 통과**(기존 25 + `buildShareLinks` 코멘트 케이스 2). `node --check` script.js·core.js 정상. `python build.py` 성공(13밴드·560곡), index.html에 textarea·comment-tip 주입 확인.
- 사용자 브라우저 확인: 메모 작성·표시·툴팁·링크복사·버그수정·드래그 닫힘방지 전부 정상.

---

# 세션 13 — youtube_rss 자동화 Phase 1 + CI 실검증 (HANDOFF #1 완료 · 머지 · 라이브 푸시)

`tools/youtube_rss.py` 프로토타입을 **GitHub Actions 크론 자동화**로 승격. 13밴드 Topic RSS에서 신곡 탐지 → **곡당 PR**(1곡=1 PR) → 사람이 머지(TP)/닫기(FP) → precision 자동 집계. 앱 런타임과 분리돼 기존 기능 무영향.

## Phase 1 구현 (커밋 1505da7·738452c·e6750f8 · `feature/youtube-rss-autoloader` → main ff)
- **모드**: `--dry`(기본·미리보기, 쓰기X) / `--propose`(CI 전용·실제 PR+로그) / `--report`(precision 대시보드) / `--audit`(휴리스틱 drop 점검=FN 은신처) / `--show`.
- **멱등 재계산(seen 영속화 폐기)**: 후보 = 13밴드 RSS − `known_ids`(매 실행 `data/*.yaml`에서 추출) − closed-unmerged PR(거절분). 머지곡은 yaml에 들어가 자동 제외 → `rss_seen.json` 불필요(폐기·.gitignore에서 제거).
- **곡당 PR + GitHub 상태 = 원장**: 브랜치 `rss/<video_id>`. 승인=머지→yaml 반영, 거절=PR 닫기(봇이 재제안 안 함). 별도 명령·파일 없음.
- **외과적 yaml 삽입(회귀 차단)**: 전체 재직렬화 금지. 대상 앨범 `tracks:` 끝에 4-space 블록만 삽입 → diff=추가 줄만. 모든 삽입은 `yaml.safe_load` 재파싱 통과해야 PR 생성.
- **길이필터**(2차 FP컷) + `variant_tag` 보강(movie/anime ver·edit·medley·remix·nightcore).
- **로깅**: `tools/rss_events.jsonl`(append-only·git추적·앱 미포함) — 매 실행 전 RSS 판정 기록. `--report`가 `gh pr list`와 **video_id로 조인** → precision=TP/(TP+FP), 사유별 drop, feed health.
- **포맷 감시**(파싱 레이어만): 여러 밴드 동시 0건=하드 알람(이슈 자동생성, 동일 이슈 중복 X). 단일 밴드 0건/신곡 0건은 정상(알람 X). fetch 실패는 연속 retry>3 때만.
- **워크플로 `.github/workflows/rss.yml`**: `schedule: '0 19 * * *'`(=04:00 KST) + `workflow_dispatch`. 권한 contents/pull-requests/issues:write. 3rd-party 액션 없이 러너 기본 `gh` CLI + `pip install pyyaml`. `python tools/youtube_rss.py --propose` 명시 호출(bare 오실행 방지).

## CI 실검증 (workflow_dispatch 2회 · 2026-06-24)
- **선결**: 크론/dispatch는 워크플로가 **기본 브랜치(main)에 있어야** 작동 → feature 브랜치를 main에 ff 머지·푸시 후 검증.
- ⚠️ **필수 리포 설정(안 켜면 PR 자동생성 불가)**: 1차 실행은 PR 생성 실패 — `GraphQL: GitHub Actions is not permitted to create or approve pull requests`. **Settings → Actions → General → Workflow permissions → "Allow GitHub Actions to create and approve pull requests" 체크** 필요. 켠 뒤 2차에서 정상.
- **인수기준 4/4 통과**: ① PR #1 생성(mugendai_mutype `これはぼくたちの生存のあらすじ`, 2026-06-21, full, New Singles append) ② `rss_events.jsonl` 커밋(`b650b5d`, staged 1 / TN 151 = known_id 107·known_name 34·variant 10) ③ 포맷 이상 이슈 0 ④ `--report` pending 1.
- **첫 곡 승인(TP) + 라이브**: 실제 6/21 발매 신곡 확인 → PR #1 **스쿼시 머지**(`0ba70f7`) → `--report` **TP 1 / precision 1.000 (1/1)**(탐지→PR→머지→집계 end-to-end 검증). `python build.py`로 곡 **560→561**, index.html 1줄 diff 커밋·푸시(`774a3ce`) = 게이트2 라이브 반영.

## 알려진 한계 · 낮은 우선순위 후속
- ⚠️ **CI에서 길이 스크랩 막힘**: 로컬 `--dry`는 235s를 긁는데 CI는 `length_s=null`(YouTube가 데이터센터 IP에 consent wall). → **CI에선 길이필터(2차 FP컷)가 비활성**, `variant_tag`만 작동. FP 정밀도 보강 시 oEmbed/대체경로 검토(HANDOFF #1 데이터 품질의 길이 점검과 로직 공유 가능).
- `tools/rss_seen.json`: 폐기된 프로토타입 산출물이 untracked로 잔존(설계상 불필요). 삭제 가능.
- 출력 "Opened N PR(s)" 카운터는 실패 시에도 staged 수를 찍음(1차 실패 때도 "Opened 1 PR(s)") — 실제 성공과 무관한 표시 버그.

## auto-merge 정책 (Phase 2 — 후속, 미도입)
- 지금은 **수동 게이트로 시작**: 사람의 머지/거절이 곧 TP/FP 라벨링 = precision 측정 기구. auto-merge로 시작하면 FP가 관측 안 돼 precision이 항상 100%로 보여 측정 불가(self-defeating).
- 신곡 ≈ 50곡/년 ≈ 주 1클릭. 무-FP 30~50건 누적 후 고신뢰 티어(variant 정상·길이 정상·임계 비근접)만 auto-merge 검토(precision 현재 1/1에서 시작).
- 🔁 PR이 번거로우면 사용자 결정으로 자동-우선(Actions가 main 직접 push) 전환 가능 — 그 순간부터 precision 측정 중단 감수. FN(놓친 신곡)은 거의 없을 전망 → deferred FN 수동등록 툴 우선순위 낮음.
- **Phase 1.5(옵션)**: main에 data 머지 시 build+deploy 자동 워크플로 → 수동 `build.py` 잡일 제거(개발 안정화 후).

---

# 세션 14 — 데이터 정합성 검수 #1 완결 (C2 배치·C1 삭제·빈url 처리·곡명 정규화 불필요 확인 · 머지)

`undefined` 더미앨범과 빈url을 전량 해소하여 **전곡 재생가능** 달성. HANDOFF #1(데이터 품질 검수) 종료.

## 도구 (전부 텍스트 기반 = YAML 포맷·따옴표 보존, dry-run 기본 + `--apply`, 적용 후 재파싱·손실0 검증 내장)
- `tools/verify_links.py` — 읽기전용 triage(data 무변경). L0 오프라인(A빈url·B url오류·C undefined분류·D앨범중복·E동명다른영상) / L1 `--oembed`(죽은링크·제목대조) / L2 `--length`. 캐시 `verify_cache.json`(재생성 가능, `.gitignore` 등재). **로컬 전용**(L2 길이 스크랩은 CI consent wall로 막힘).
- `tools/execute_placement.py` — C2 배치 실행기(`c2_placement.csv` 입력).
- `tools/delete_redundant.py` — C1 redundant 삭제(undef 블록 *범위 내에서만* 제거 → 정규앨범 보존, 빈 undef 블록 드롭).
- `tools/resolve_empty.py` — 빈url 정리(ENRICH 매핑은 New Singles 보강, 나머지 제거, 빈 undef 드롭).
- youtube_rss의 video_id/norm_name/oEmbed/insert_track 재사용(중복정의 없음).

## 확립된 규칙(데이터 정리 기준 — 이후 신곡 검수에도 적용)
1. **소스 우선순위 음원(Topic) > MV > 라이브.** 같은 곡 중복 시 더 우선 소스만 남김.
2. **곡명 = 공식 유튜브 채널 표기.** romaji 음차 지양. (→ 아래 "곡명 정규화 불필요 확인" 참조.)
3. **동명이곡은 모두 유지**(원곡 vs 커버, JP vs English 등). 앱은 `band::title`로 식별. ⚠️ title 완전 동일 시 충돌→구분 저장.
4. **album_title은 화면 미표시**(script.js:149 `isCover` 판정에만 사용). 정밀 album은 기능영향 0, 미래 메타데이터용.
5. 신곡 검수: 자동 PR 우선, 결함 시에만 CSV+알림. (memory `rss_review_workflow`)

## 작업 내역
- **선행 완료**(커밋 b765cc0→1379d88): malformed 곡명 3 · wrong-url 7(B, oEmbed로 정답 확정) · 커버 4→Covers 이동 · 음원우선 정리(mygo 静降想 MV삭제 / morfonica 2 음원교체 / ave_mujica 顔 MV교체).
- **C2 유일본 40 배치 + 중복 MV 2 삭제**(`execute_placement.py`, 커밋 67c140b): undefined 더미 36 → 각 밴드 `New Singles`(numbering `Single`; 없는 밴드 afterglow·mygo·ikka·millsage 블록 신설, img `_fallback.png`). various_artists 4는 서브유닛 앨범(Glitter\*Green/Chispa/Sumimi) `numbering:undefined`만 결함 → de-undef(이동 아님). 사용자 romaji→공식명 7 반영(예 `Haruhikage (Original)`→`春日影`, 정규 `春日影 (MyGO!!!!! ver.)`와 별개 유지). 삭제(음원우선·손실0): mugendai `Mutant Mutant`(MV) · poppin `DOKI DOKI DATE`(MV).
- **C1 redundant 24 삭제**(`delete_redundant.py`): undefined가 정규앨범과 동일 video_id → 손실0 검증 후 일괄 제거. 빈 undef 블록(ave_mujica·pastel_palettes) 드롭. 곡수 555→531.
- **빈url 16 처리**(`resolve_empty.py`, 정책 "보강 후 잔여 제거"). **보강 2**: RAS `WHAT AN EXPLOSION`/`RUNAWAY STAR`(15th single, 2026-06-10 발매 — 데이터 입력 당시 미발매라 빈url이었음. WebSearch + oEmbed `RAISE A SUILEN - Topic` 검증) → New Singles(track_number=발매일). **제거 14**: mygo `致並跡 -`×3(3rd앨범 빈슬롯) + afterglow `IGNITE GLOW`(음원중복·손실0) + 보강실패 10(GLAMOROUS SKY·紅蓮の弓矢·Take it easy 등 — 게임곡/커버라 YouTube 공식 음원 없음, 게임플레이 영상은 rule 1·2 위반이라 미채택). 잔존 빈 undef 블록(afterglow·hello·morfonica·mygo·poppin·raise·roselia + ikka·millsage·mugendai) 전량 드롭. 곡수 531→517.

## 곡명 정규화(rule 2) 불필요 확인
원래 "romaji 음차가 다수 잔존"이라는 가정의 후속 패스였으나 **불필요**로 결론:
- 일본어 미포함 곡명 212곡을 실사 → **거의 전부 공식 영어 제목**(poppin `Time Lapse`·`Dreamers Go!`, afterglow `Crow Song`·`Butter-Fly` 등). BanG Dream은 영문 제목을 공식으로 쓰는 곡이 많아 정규화 대상 아님.
- 실제 romaji 음차였던 곡(`Haruhikage`·`Kapoon`·`Mabushii` 등)은 **C2 배치 시 교정 또는 빈url 제거 시 함께 소멸**.
- 잔여 애매건(`TARINAI`·`SENSENFUKOKU`)도 공식이 로마자로 표기 → 손댈 이유 없음.
- 기능영향 0(곡명은 화면표시·검색용, romaji여도 앱 정상). → **후속 패스 폐기.**

## 최종 상태 / 검증
- **곡수 561→517 · video_id 보유 517/517(전곡 재생가능) · undefined 더미 블록 0 · 빈url 0 · B/C1/C2 모두 0.**
- `python build.py` 성공(밴드 13, 곡 517) → index.html 재생성.
- ⚠️ JS 카운트 테스트는 실재하지 않음(core.test.js는 합성 fixture만 단언) → 곡수 변동 시 갱신 불필요.
- 잔존(untracked): `c2_placement.csv`(40행, 추적가능). `verify_cache.json`은 재생성 가능이라 `.gitignore` 등재.

## 커밋 · 머지
- 커밋 `67c140b`(20 files, +848 −313) → `feature/song-validator` 푸시. 이후 main 머지.
- `tools/rss_seen.json` 폐기 잔재 삭제는 별건(미진행, HANDOFF에 잔존).

---

# 세션 15 — urgent: 재생불가(지역락) 7곡 URL 교체 + tools/ 목적별 재편 (완료)

`docs/archive/urgent.md` 대응. 일부 곡 선택 시 유튜브 iframe에 **'동영상을 재생할 수 없음. 동영상을 볼 수 없습니다.'**가 뜨는데 url 자체는 살아 있는 케이스 파악·수정. urgent.md 규약대로 처리 후 이관.

## 원인 진단 (재생불가 = 지역락 7곡, 그 외 0)
일반 메시지라 원인을 따로 가려야 해서 **두 독립 신호 교차검증**:
- **Data API**(`status,contentDetails`, 500 고유 vid): 삭제/비공개(미응답) **0** · 임베드차단(`embeddable=false`) **0** · 비공개 privacy **0** · **KR 지역차단 7**.
- **한국 IP `watch` playabilityStatus 500곡 전수**(`hl=ko&gl=KR`): `OK` 493 / `UNPLAYABLE` 7, 스크랩 실패 0(누락 구멍 없음).
- 양 신호의 video_id 7개 **완전 일치**. 7곡 모두 `blocked` 249개국(KR 포함) = 사실상 일본 전용 공식 업로드 → 한국 재생불가. iframe "재생불가" 4원인(삭제·임베드차단·연령제한·지역차단) 전부 커버, 지역차단만 검출.

## 처리 내역
- **탐지기 신규**: `tools/curate/check_embeddable.py` — Data API + KR playabilityStatus 합산 분류(plb), `fix_url.csv` 산출. 캐시 `tools/curate/plb_cache.json`(.gitignore 등재).
- CSV 산출: `[song_name, current_url, modified_url, plb]`. 사용자가 **대체 url 7개 입력**(공란 0 = 삭제 0, **교체 7**).
- **적용 전 새 url 7개 검증**: 전부 한국에서 `watch=OK`·`embeddable=True`·KR미차단, 제목 일치 확인.
- **적용기 신규**: `tools/curate/apply_fix_url.py` — current_url의 vid로 매칭해 url 줄만 텍스트 교체(포맷·따옴표 보존, 재직렬화 금지). loss 검증(매칭 1:1 · 재파싱 · old제거/new존재 · 곡수). dry-run → `--apply`.
- 교체 7곡: afterglow `Sasanqua` · ave_mujica `The Whole Blue World`/`in your blue eyes`/`素晴らしき世界 でも どこにもない場所` · poppin_party 3× `~Popipa Acoustic Ver.~`(Yes! BanG_Dream!/夏空 SUN! SUN! SEVEN!/走り始めたばかりのキミに). 변경 파일 3개, url 7줄(+7 −7).
- `python build.py` 성공(밴드 13, 곡 **517 불변**) → index.html 재생성. old vid **0**, new vid **7/7** 반영 확인. (곡수 불변이라 JS 카운트 테스트 무관.)

## tools/ 목적별 재편 (작업 중 요청)
- `tools/collect/`(수집: youtube_rss·youtube_api·backfill·band_top10·rss_events.jsonl) / `tools/curate/`(검수·수정: verify_links·delete_redundant·resolve_empty·execute_placement·check_embeddable·apply_fix_url + csv/cache) / `tools/convert/`(converter).
- 한 단계 깊어져 깨지는 참조 일괄 수정: cross-folder `sys.path`(curate→collect), `ROOT=parents[2]`, 하드코딩 `tools/<file>` 경로, **CI `rss.yml`**(`python tools/collect/youtube_rss.py`), `.gitignore`(캐시 경로), HANDOFF·docstring 실행경로.
- 검증: 10개 스크립트 import 스모크(ROOT→repo root OK) + 오프라인 dry-run(verify_links/delete_redundant/resolve_empty exit 0) + converter 왕복. **git rename 인식(이력 보존)**, 옛 경로 잔존참조 0.

## 최종 상태
- **전곡 한국 재생가능**(지역락 7곡 → 임베드 가능 대체 url로 교체 완료). 곡수 517 유지.
- 커밋 미진행(사용자 확인 대기).

---

# 세션 16 — HANDOFF #1: 백필 1-a 오리지널 29곡 추가 + 지역락 3곡 처리 + docs/ 재배치 (완료)

`feature/emoi-sentiment`. 미추가 곡 백필(1-a) — Topic 채널 오리지널 누락분을 데이터에 추가하고, 재생테스트로 KR 지역락 곡을 분리·삭제(보존), 재발 방지 가드까지.

## 백필 후보 → 사용자 검수 (new_songs.csv)
- `backfill.py` 재실행: 신규 후보 **164**(오리지널 29 / 커버 135 · namedup 403) → `tools/collect/new_songs.csv` 생성(`song_name·url·type·author·note·comment`).
- 사용자 검수 반영: `CiRCLE THANKS MUSiC♪`→various_artists 이동, `NO GIRL NO CRY (Poppin'Party Ver.)`→original 취급. 기존 데이터 중복 0·mygo `ホワイトノイズ`(공식음원 없음, 게임 간접링크뿐) 부재 확인.
- 커버 135(1-b)·namedup 403(1-c)은 **보류**(별도 배치).

## 오리지널 29곡 삽입 (insert_backfill.py 신규)
- `tools/collect/insert_backfill.py` — new_songs.csv type=original → 각 밴드 **New Singles**(numbering=Single/album=New Singles/img=FALLBACK_IMG). 발매일(track_number)은 `fetch_uploads` 재조회(백필 동일 출처).
- **(band, numbering, album_title) 3중 매칭** 삽입(`insert_track` 보강판) → various_artists 복수 Single 앨범(Glitter*Green 등) 오삽입 방지. CiRCLE은 VA 새 New Singles 블록 created.
- dry-run → loss-0 검증 → `--apply`, 멱등(이미 있는 vid 스킵). 28곡 밴드 append + 1곡 VA created = **29 삽입**.
- 분포: roselia 14·raise_a_suilen 7·poppin_party 3·morfonica 2·afterglow 1·ave_mujica 1 + VA 1.

## 재생테스트 → 지역락 3곡 삭제 (보존)
- 신규 29곡 한정 `check_embeddable.py` 로직 재사용(Data API regionRestriction + 한국 IP watch playabilityStatus, **2신호 일치**) → **KR 지역락 3곡** 검출: raise_a_suilen `DEAD HEAT BEAT`, roselia `Our Carol`·`Swear ～Night & Day～`(모두 2022 구곡, blocked 다수국).
- 정책(2026-06-29): 지역락=법적 이슈·대체 불가 → **앱 데이터에서 삭제, 곡 정보는 `tools/curate/invalid_url.csv`에 보존**(`song_name·author·current_url·modified_url·plb`).
- `apply_fix_url.py` 삭제 로직(modified_url 공란=삭제) 재사용(경로만 invalid_url.csv로, 기존 fix_url.csv 배치 불간섭) → 3곡 삭제. 곡수 546→**543**, 순증 26.

## 재발 방지 가드 (insert_backfill.py)
- insert_backfill에 `invalid_url.csv` 가드: 해당 vid는 건너뜀(modified_url 공란=보류). modified_url 채워지면 그 url로 **재등록** → 삭제한 지역락 곡이 재실행으로 부활하지 않으면서, 대체 음원 확보 시 자동 복귀. 양방향 dry-run 검증.

## 빌드·정리
- `python build.py` 성공(밴드 13, 곡 **543**, 워드클라우드 10). 신규 vid 5종 반영·지역락 vid 3종 0 확인. data diff **+84/−0**(순수 추가, 기존 url 미변경 — 이스터에그 url 포함 무손상).
- CSV 목적별 이동: `new_songs.csv`→`tools/collect/`, `invalid_url.csv`→`tools/curate/`(fix_url.csv 형제). 코드 경로(insert_backfill) 갱신.
- **docs/ 재배치**: `spec/`(PRD+mockup) · `archive/`(urgent.md) 신설, 참조 링크·도크스트링 경로 수정. HANDOFF 1-a 완료분 → 본 세션 이관.

---

# 세션 17 — 밴드 워드클라우드: 키워드 파이프라인 + 렌더 1차 + 라이브 머지 (HANDOFF #2 부분완료)

`feature/emoi-cloud` → `feature/emoi-sentiment`(2026-06-27 파이프라인·렌더, 2026-06-29 main 머지 `d6f05c7`·라이브). **품질 보완(2-c)은 미완 → HANDOFF에 남김.** 품질 진행의 단일 출처 = memory `wordcloud_quality_plan.md`.

## 키워드 추출 파이프라인 (`tools/wordcloud/`, `4d66c11`·`db226cf`)
- 가사 = 밴드별 조회수 TOP10 곡, **사용자 직접 복붙**(크롤링 안 함). 빈 템플릿만 `assets/lyrics/<band>_template.md`로 커밋, 채운 `<band>.md`는 `.gitignore`(가사 비커밋). **원문 미보관 원칙** — yaml엔 단어 단위 키워드만.
- `lyrics_parser.py`(줄 문자종으로 jp/음차/번안 트리플렛 + 곡 메타) + `build_keywords.py`(fugashi 명사추출→빈도, **커버 제외**, ko 채움) → `wordcloud/<band>.yaml` **10밴드 전부 생성**(빈 곡 0).
- **ko = 한글 번안 우선**(kiwipiepy 명사 + Dice 단어정렬 ~85–90%) → 실패분만 기계번역(deep-translator, `# 기계번역 초안` 주석) → 빈칸 0. 필터: 형식명사·영어조각·단일가나·감탄사 컷, 외래어 `-romaji` 제거, `--min-weight 2`. 산출 71~174어/밴드.
- 의존성 4종(fugashi·unidic-lite·kiwipiepy·deep-translator) → `tools/wordcloud/requirements.txt`(빌드타임 전용). 재생성 = `python tools/wordcloud/build_keywords.py`(멱등) → `python build.py`.

## 렌더 1차 (`2942dd6`)
- `build.py`가 `wordcloud/*.yaml`→`WORDCLOUD_DATA` 주입, 우패널 **3번째 탭 "밴드 정보"**에 `static/js/wordcloud2.min.js`(벤더링) 렌더. `renderWordcloud()`: 현재 밴드 따라감(ALL=전체 병합), ko 표시, 동일 번역어 빈도 합산, 상위 60, sqrt 폰트 압축, 테마색. 헤드리스 Chrome 스크린샷 검증.
- 빈 메시지 안 사라지던 버그 수정(CSS `.wc-empty[hidden]{display:none}`). '곡 클릭 시 탭 자동활성화'·jp 툴팁은 의도적 미적용(v1).

## 품질 1차 보정 (`86bb773`·`58b52ad`)
- **①TF-IDF 변별력 가중**: ALL=원빈도 / 밴드별=차별성 `w·idf`(공통어 감점·특징어 가점).
- **②가타카나 음차화**(`kana2ko.py` + `resolve_ko`: align→음차유사도검증→음차→MT→빈칸): 제·텐·밍·퐁퐁포퐁 등 노이즈 제거. align Dice 임계 0.30→0.45(N:1 오정렬 직역 폴백).

## 감성 데이터 (`248e6f0`) + 토글 롤백 (`42be797` → `c067b69`)
- 연속 극성 라벨 `tools/wordcloud/senti_lexicon.yaml`(122개) + 파이프라인 완료.
- 감성 시각화 3표현 토글을 만들었다가 **사용자 코멘트로 롤백 → 워드클라우드 단일로 복원**. **감성 데이터·`build.py senti`는 보존** — #3 클러스터의 감성막대(긍↔부정) + 진지성(진지↔유쾌) 다차원 무드 벡터로 용도 전환 예정. 탭은 추후 `[워드클라우드 | 클러스터]`로 구분 예정.
- ⚠️ 감성은 단어 단독 추출이라 밴드 실제 컨셉과 어긋날 수 있음(재미·참고용, 컨셉 단정 아님 — 경향성은 대체로 맞음, 사용자 검증).

## 머지 · 라이브
- `feature/emoi-sentiment`(워드클라우드 전체 + 세션 16 백필) → **main 머지 `d6f05c7`**, GitHub Pages 라이브 반영. **롤백 지점 `backup/main-20260629`**(머지 직전 main = `e062bca`) 보존 — 복구법은 HANDOFF.
- **밴드 퍼스널 컬러 12밴드 확정**(워드클라우드·클러스터 색): 표는 HANDOFF #2.

---

# 세션 18 — HANDOFF #1-b: 백필 커버 114곡 추가 (135 삽입 − KR 지역락 21 제거)

`feature/backfill-1b-covers`. 보류였던 1-b 커버를 사용자 요청으로 진행 — 오리지널(세션 16)과 동일한 "삽입 → 지역락 검증 → 차단곡 제거·보존" 워크플로우.

## 커버 삽입 (`insert_backfill.py --cover` 신규 모드)
- `insert_backfill.py`에 `--cover` 모드 추가: type=cover → numbering=`Cover` / album_title=`Covers`, 곡명에 `" (Cover)"` 접미(클라이언트 커버 탭 판별 = album_title 'Covers' + 곡명 '(Cover)'). 오리지널 경로·안전장치(loss-0·present·멱등·invalid 가드) 그대로 재사용.
- `new_songs.csv` type=cover **135곡** → 9밴드 Covers 앨범 append(발매일은 Topic 채널 `fetch_uploads` 재조회). dry-run loss-0 → `--apply`. 트랙 543→678, 중복 스킵 0.
- 분포: poppin 22·roselia 21·pastel 21·HHW 18·afterglow 17·RAS 15·morfonica 14·mygo 4·ave 3.

## 재생테스트 → KR 지역락 21곡 삭제 (보존)
- `check_embeddable.py` 전량 점검(678트랙·고유 661 vid, 한국 IP watch + Data API 2신호): **region_blocked 21건**, 나머지 657 ok. embed_disabled/deleted/login 0.
- 교차대조: 21건 **전부 신규 커버**(기존 데이터 0건 — 깨끗). 7밴드(afterglow·HHW·morfonica·pastel·poppin·RAS·roselia) ×3곡.
- 정책대로 `tools/curate/invalid_url.csv`에 21곡 보존(author·blank modified_url) + `apply_fix_url.py`로 삭제(loss-0 21/21, 678→657). invalid_url.csv 3→24행, 가드로 재실행 부활 방지.

## 대체 음원 워크시트 (`tools/curate/region_blocked.csv` 신규)
- 사용자 요청: 지역락 곡은 블락 없는 대체 영상을 직접 찾을 수 있으므로 `new_songs.csv` 형식 워크시트로 별도 정리.
- invalid_url.csv의 region_blocked 24곡(커버 21 + 기존 오리지널 3) → `region_blocked.csv`(song_name·url·type·author·note·comment). `url` 공란 = 사용자가 대체 영상 채움, `comment`에 블락된 원본 링크. 채우면 `insert_backfill.py --cover`(또는 new_songs.csv 병합)로 재등록.

## 빌드·결과
- `python build.py` 성공(밴드 13, 트랙 657, 워드클라우드 10). **화면 표시 곡수(고유 video_id dedup) 526 → 640(+114)** = 커버 135 − 지역락 21. 헤더 `n / 640곡 평가됨`.
- ⚠️ `npm test`는 이 장치 node 미설치로 미실행(core.js 무수정 → 회귀 위험 낮음). fix_url.csv는 스크래치 출력이라 커밋 직전 원복.

---

# 세션 19 — 지역락 커버 대체 음원 재등록 (region_blocked.csv 20곡 복귀 · 최종 지역락 4)

세션 18에서 뺀 지역락 24곡(커버 21 + 기존 오리지널 3)을 사용자가 `region_blocked.csv` 워크시트에서 블락 없는 대체 영상으로 채움 → 검증 후 재등록.

## 대체 URL 검증 (Data API)
- region_blocked.csv `url` 칸에 사용자가 대체 영상 20곡 기입 → 제목·채널·embeddable·regionRestriction 검증. 전부 KR차단 0·embed OK.
- **제목 대조로 오입력 1건 적발**: シルエット(HHW)에 afterglow `インフェルノ` vid(`DOrx3z-Z86c`)가 들어가 있었음 → 사용자 수정(`n7U-z7okdBM` = シルエット (Cover), Hello happy world Topic, 검증 통과). **단어/지역락 검증뿐 아니라 제목 대조가 오입력을 잡음.**
- Swear ～Night & Day～는 스튜디오 음원 부재 → 공식 라이브 영상(`バンドリちゃんねる☆`) 채택(곡 일치·embed·KR ok).

## 재등록 (`invalid_url.csv` modified_url → insert_backfill 가드 경로)
- 검증된 20곡(커버 19 + 오리지널 Swear)을 `invalid_url.csv`의 modified_url에 기입 → `insert_backfill.py --cover`/기본 실행: 가드가 blocked orig vid를 modified_url(대체 vid)로 **재등록**(blocked vid는 계속 가드, 부활 안 함). dry-run loss-0 → apply.
- **최종 지역락 4곡**(modified_url 공란 유지 = 끝까지 블락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. `region_blocked.csv`는 이 4곡만 남겨 기록(대체 음원 확보 시 url 채워 재등록).

## 결과
- `build.py` 성공(밴드 13, 트랙 677, 워드클라우드 10). **화면 곡수 640 → 660(+20)**. 백필 1-b 누적: 526 → **660(+134)**, 최종 KR 지역락 4곡만 제외.
