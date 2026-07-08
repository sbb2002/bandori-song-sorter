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

---

# 세션 20 — 워드클라우드 품질 2-c(A·B·C) + 키워드 밴드 퍼스널 컬러·투톤·네온 (HANDOFF #1 완료, (D)만 남음 · 머지)

`feature/emoi-cloud`(main 기준 생성 — 원격 동명 브랜치는 main의 옛 조상이라 손실 없이 fast-forward). 이 장치는 **node 설치됨**(`node --check`로 script.js 문법 검증 가능 — 세션 17 장치와 다름).

## (A)(C) yaml 검수 — `wordcloud/*.yaml` 10개 전면 재작성
- **align N:1 오역 교정**: 사자성어/복합어가 형태소 분해돼 각 조각이 전체 번역으로 매핑된 것 다수 교정(熊 코끼리→곰, 身体 충동→몸, 香り 격조→향기, 有りの侭 있는 떡→있는 그대로, 果て 내면→끝, 宝石 순도→보석 등). 단 같은 ko로 병합되는 사자성어(因果/応報/報い→인과응보)는 `mergeBandKeywords`가 재병합하므로 유지.
- **노이즈 줄 삭제**: 보컬리제·의미불명 단편 제거(ドゥビドゥバッポー·オオ·タ・イ·只·感·大 등). hello_happy_world 130→102로 대폭 정리.
  - ⚠️ **`weight:0`은 큐레이션에 무효** — `mergeBandKeywords`의 `(k.weight || 1)` 때문에 렌더에서 1로 살아남. 완전 제거는 **yaml 줄 삭제**여야 함(HANDOFF #1-C가 "weight 0/삭제"라 한 부분의 함정).
- **외래어 음차 표준화**: 텐숀→텐션, 모부→모브, 멘바→멤버, 팡파레→팡파르 등.
- **통일 규칙**: 輝き→빛남, 笑顔→미소(顔=얼굴과 구분), 思い→생각(心=마음과 구분), 無限→무한, 道程→여정.
- **재생성 대비**: `build_keywords.py` OVERRIDE(외래어 표준+반복 오정렬 ~40항목)·STOPWORDS(분해조각 12자) 확장. 단 이 장치엔 가사 원문 없어 재생성 불가 → yaml 직접 편집으로 진행.
- 검증: 전 yaml **빈 ko=0 · ko 일본어 잔존=0**.

## (B) 렌더 가독성 — `script.js`
- 표시 개수 60→40, 폰트 하한 h/18→h/15, gridSize w/64→w/48(여백 확대).

## 키워드 색상 — `script.js` (사용자 요청: "키워드 색을 밴드 이미지 컬러로", HANDOFF #2 표 근거)
- `BAND_COLORS`(퍼스널 컬러 12밴드) + `hexToHsl`: 밴드별 키워드를 **퍼스널 컬러 hue 고정**, 빈도(폰트 px t)에 따라 **명도 35~82% 변주**(저빈도 가라앉힘·고빈도 강조). 어두운 퍼스널 컬러(roselia·mygo·ave)도 다크 배경(#1e1e2a)에서 보이게 명도 강제.
- **mutype 투톤**: `BAND_SUBCOLORS`(#2288dd) → `ctx.createLinearGradient(0,-size/2,0,size/2)`(textBaseline=middle 로컬 좌표)로 키워드 **글자 아래 ~22%만 보조색** 세로 그라데이션. wordcloud2가 color 반환값을 `fillStyle`에 직접 넣어 `CanvasGradient` 객체가 유효함을 확인.
- **네온 글로우**: 표시 키워드 폰트 분포 **Q2(중앙값) 이상(상위 절반)**에 같은 색 `shadowBlur:8`. 단어별 명시 리셋으로 번짐 차단. (명도 75%↑ → Q2 기준으로 사용자가 변경) 각 밴드 Q2(t)는 0.08~0.29(명도 38~48%).
- **ALL 탭**은 키워드가 밴드 구분 없이 병합되므로 기존 6색 팔레트(`WC_PALETTE`) 유지.

## 결과
- `index.html`은 `script.js`를 외부 참조(`<script src=...>`)라 색상 작업은 재빌드 불필요. `build.py` 성공·`node --check` 통과.
- HANDOFF #1은 **(D) 워드클라우드 배치 결정**만 남음(#2 클러스터 게시위치와 함께 사용자 결정 사안).

---

# 세션 21 — 음원맵 축 지각 재정의: 30곡 파일럿 검증 + 구현 + UI (HANDOFF #2-v3 완료, 전곡 확대만 남음)

`docs/spec/audio-map-axes.md` §5 검증을 30곡 손 라벨로 실행 → 축을 **음향 feature로 직접 재정의**. 전곡 확대(스케일업)만 남았고, 그 구현 스펙은 **[spec/audio-map-fullscale.md](spec/audio-map-fullscale.md)** 로 분리.

## 검증 (n=28, 워크시트 손 라벨 ↔ feature 상관)
- **spec 예상 뒤집힘**: x축(f0/음고) **실패**(r≈0) — BanG Dream 전곡 여성보컬·유사 음역이라 f0 median이 뭉쳐 곡별 변별력 없음. §2.1 peak-f0 가설 반증. Demucs 보컬분리는 필수였으나(믹스 f0는 베이스에 락) 분리해도 음역 균질.
- **채택 축**: x = **spectral contrast**(r=−0.81, 오른쪽 거칢/왼쪽 매끄러움), y = **mode_score 장·단조**(r=+0.51, 위 밝음/아래 어두움). contrast가 valence·rough 양쪽 지배 → 카탈로그가 **음향적으로 사실상 1차원**, mode만 독립(r=0.37). 측정가능 2D = (contrast, mode) 하나뿐.

## 구현
- `tools/cluster/build_perceptual_map.py`(신규 채택본) — contrast·mode만·z-score 직접좌표(**PCA/f0/Demucs 불필요**), `cluster/songs_top10.csv` → `cluster/audio_map.json`. `carry_sim()`으로 v2 CLAP sim 승계, songs에 url 포함.
- `tools/cluster/perceptual_features.py`(Demucs+f0+mode/timbre, mode_valence=Krumhansl KS 프로파일) · `tools/cluster/axis_correlation.py`(피어슨/스피어만) · `cluster/axis_labels_worksheet.csv`(손 라벨 30행) · `cluster/axis_pilot_features.csv`.
- **튜닝**: `Y_SHIFT=+10`(데이터 평균이 밝은팝 치우침 → RAS '약간 마이너' 앵커) · `BAND_OVERRIDES morfonica dy+15`(★측정 아님★ 바이올린 음색 밝음이 어떤 feature로도 안 잡힘 → 밴드 큐레이션, `audio_map.json.overrides` 투명 기록). ave는 미보정(y 정확·x만 프록시 한계).
- 보고서 `docs/report/cluster-correlation/README.md`(§7 x축 재검정·§8 구현·§8.1 morfonica).

## UI (script.js `_clDraw` 재작성 — 두 모드)
- **ALL 개요**: 완전 정적(호버=타밴드 흐림만, 이동 없음 → 센트로이드 클릭 안정) · 곡 s=0.5로 밴드 중심 뭉침 · **밴드 센트로이드=`assets/icons/<band>.png` 아이콘** · zero-line 없음.
- **밴드 포커스**: 센트로이드를 [0,0]에 놓고 축을 대칭 범위로 잡아 **정중앙 배치** · 센트로이드 통과 **x·y 축선 점선** · 곡은 센트로이드 기준 상대좌표.
- 밴드셀렉터 ↔ 음원맵 양방향(센트로이드 클릭=그 밴드 선택, ALL 빈영역=개요). 곡 점 클릭=재생(리스트 선택과 동일). CLAP 연결선/유사목록 **표시 제거**(JSON 데이터는 보존). **재생 곡 파동 애니메이션**(effectScatter rippleEffect). `_clRangeKey` 가드로 호버·재생 시 줌 리셋 방지. `.cl-similar` 고정높이+스크롤(하단 점 가림 버그 수정).

## 결과 / 남은 것
- TOP10×10 **97곡 미리보기 라이브 확인 완료**. `index.html`은 `<script src>` 외부 참조라 JS·CSS 수정은 재빌드 불필요(템플릿 변경만 `python build.py`).
- **남은 작업 = 전곡 확대뿐** → **[spec/audio-map-fullscale.md](spec/audio-map-fullscale.md)** 참조. 미머지(feature/emoi-cluster-v2).

---

# 세션 22 — 레이아웃 확정(작업 1-D 완결) + 정적파일 기능분할 리팩터 (feature/emoi-cluster-v3a · main FF 머지)

HANDOFF "열린 결정(레이아웃 묶음)"을 확정하고, 비대해진 `style.css`(956줄)·`script.js`(1581줄)를 기능별 파일로 분할. 오디오 전곡 수집(작업 2 Phase 1[A])은 **진행 중** → 현황·재개는 HANDOFF.

## 레이아웃 확정 (작업 1-D + 음원맵 게시 위치)
대안 A(전체폭 하단 독, `36d4629`)는 "너무 비대" 피드백 → **대안 B 채택**(`6373745`): 유튜브 컬럼 하단 슬롯을 세로 분할선으로 **좌=음원맵 / 우=워드클라우드**(`.yt-bottom-split`, flex 1.2:1). 워드클라우드 상시 렌더(탭 게이트 제거).
- **B 정제**(`bf522a8`): 곡리스트 폭 30%↓(`.center` 0.7fr:1.8fr) → 유튜브+음원맵/WC 확대. 긴 곡이름 = 평상시 말줄임, **호버/재생·선택 시 마퀴**(`.st-text`·`markSongTitleOverflow`, scrollWidth 측정 → `--st-shift`/`--st-dur`).
- **레이아웃 확정**(`5a7caf4`): 유튜브 **16:9 스테이지**(`aspect-ratio:16/9`·`max-height:52vh`) + 우패널 **탭 제거 → 히스토그램(위)·히트맵(아래) 동시 표시** + 음원맵 하단 유사곡 목록 **표시 숨김**(`.cl-similar{display:none}`, 요소·JS 보존).
- **우패널 비율**(`db04a6a`): 히스토그램 내용 높이(`flex:0 0 auto`)·히트맵 남는 세로 전부(`flex:1 1 0`) → 히트맵 스크롤 최소화.
- **모바일 붕괴 수정**(`4083f11`): 세로 스택에서 `.yt-bottom-split .audiomap-area`가 데스크톱 `flex:1.2 1 0`(basis 0)을 물려받아 높이 0으로 붕괴(워드클라우드에 파묻힘) → 명시적 `flex:none;height:320px`로 특이성 오버라이드.
- 대안 매핑 = memory `wordcloud-layout-alternatives.md`.

## 정적파일 기능분할 리팩터 (`d9f3b1b`)
- **CSS 3분할**: `style.css` → `common.css`(변수/리셋/헤더/팝업/면책) · `desktop.css`(§3-8 레이아웃+컴포넌트) · `mobile.css`(@media ≤1023px). 섹션 경계로만 분리·로드순서 고정(common→desktop→mobile) → 렌더 바이트 동일. 재배치된 popup/disclaimer 셀렉터 충돌 0 검증.
- **JS 19분할**: `script.js` → `static/js/functions/01~19-*.js`(§1 state ~ §17 init). **classic 순서 로드**(전역 스코프·가변상태 공유 유지, ES모듈 아님). 유일한 코드 변경 = §1 상태 로드(`loadRanks`/`loadComments`)를 `19-init.js` DOMContentLoaded 선두로 이동(파일 간 함수 호이스팅 회피). 검증: `node --check` 19/19 PASS, 연결본==편집원본(바이트 일치).
- 주입: `build.py` `static_paths.css`(리스트)·`js`(functions 글롭) + 템플릿 `<link>`/`<script>` 반복. **편집 시 주의**: CSS/JS는 이제 분할 파일을 직접 편집(참조식이라 리빌드 불필요), 템플릿 변경만 `python src/build.py`.

## 결과
- 위 전부 `feature/emoi-cluster-v3a` → **main FF 머지·푸시**(라이브 반영). `index.html`은 링크/스크립트 태그만 변경(데이터 불변).
- HANDOFF **작업 1(워드클라우드) 완전 완료**(품질 done 20 + 배치 D done 22). "열린 결정 — 레이아웃 묶음" 해소.
- ⏳ **진행 중(별도 추적)**: 작업 2 오디오 전곡 수집(Phase 1[A]) — 현황·조건3(7GB)·403 실패분석은 HANDOFF. 커밋 대기분(일시중지 시): `fetch_audio.py` 조건3, `migrate_local_cache.bat`→legacy 이관.

---

# 세션 23 — 음원맵 전곡 확대 659곡 완결·동결 + 재생 펄스 방안 A + 음원맵 HUD (feature/emoi-cluster-v3b)

`feature/emoi-cluster-v3a`(원격) 이어받아 `feature/emoi-cluster-v3b`에서 진행. 오디오 수집 완주→전곡 빌드·동결, 지각 pulse 추정, 음원맵 HUD/연출. 커밋 `274657e`·`39c82f3`·`69e9334`·`3e5e11c`(전부 v3b, 미머지).

## 작업 2 음원맵 전곡 확대 — ✅ 완결·동결 (`274657e`)
- **오디오 수집 완주 659/660**: v3a 285곡 USB 이관 후 재개. `fetch_audio.py` **`--extractor-args` 추가**(403 CDN 거부 복구) — 실패 24곡 중 **`android_music` 클라이언트로 19곡 회수**. ⚠️ HANDOFF 예시 `tv/web_safari/ios`는 전부 DRM/PO토큰이라 실패, **`android_music`이 정답**(단일곡 진단으로 규명). roselia `競宴Red×Violet` 1곡만 DRM 미해결.
- **전곡 빌드·동결**: `build_perceptual_map.py --manifest src/content/cluster/songs_full.csv --cache audio_full` → `audio_map.json` **285→659곡/13밴드**(loo 0.134). **`--manifest` 인자** 추가(하드코딩 MANIFEST 대체) + **`norm` 파라미터 동결 저장**(contrast·mode의 mean/std/k/clip + shift + overrides + formula) = pipeline §5 증분 append 선결 충족(fullscale §4·§6 "마지막 튜닝 순간"). `build.py`로 index.html 반영.
- 환경: node를 conda(`conda install -c conda-forge nodejs`)로 이 장치 설치(nsig 서명해독=403 회피). librosa/numpy/imageio-ffmpeg 등 기설치.

## 재생 펄스 방안 A(지각 pulse 추정) (`39c82f3`)
- `build_beat_track.py` **`perceptual_pulse()`**: onset ACF로 base(beat_track) vs ×2 비교, **ratio=ACF(fast)/ACF(slow)≥τ(0.96)면 8분** 채택. onsets json에 `pulse{}` 저장. 파일럿 7곡 **6/7 선호 일치**(afterglow 0.976→8분·morfonica 0.837→박 — 실제 tempo 둘다 185 동일한데 구분). **τ 0.9→0.96**(mygo 0.941 반례로 재튜닝). mugendai만 난곡 실패. 상세 [report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md).
- **펄스 프리셋 5→3단계**: 볼륨 경계 [0.2,0.6], 1단계=펄스없음/2=구3단계/3=구5단계(`CL_PULSE_R3`·`CL_PULSE_SPEED3`). **박 고정 확정**(`CL_ONSET_DEFDIV={}`).
- **펄스색 가시성 보정** `_clPulseColor`(HSL 밝기 하한 L≥0.62): 어두운 밴드색(ave_mujica `#881144`→`#e95393`)이 어두운 배경에 묻히던 문제 해소 + 두께 3·글로우.

## 음원맵 HUD·연출 (`69e9334`, 버그수정 `3e5e11c`)
- subdivision 탭 제거(박 고정, 로직·라벨 보존→추후 '설정'). 센트로이드 포커스 시 반투명(0.3)·데이터뒤로(z:1)·클릭/호버 비활성(ALL 복귀 재활성). 데이터포인트 선택곡 밝게+심볼글로우+느린점멸 헤일로/나머지 ×0.62.
- **HUD 오버레이**(우주선 스타일, 시안 `--hud` 모노스페이스·코너브래킷): 밴드명(ALL=`BanG Dream`)·밴드별곡수/센트로이드좌표(우상단) + 재생곡 거리·좌표·**밴드중심 방향 화살표**·곡메타(제목·앨범). 희미한 격자(`splitLine`)·원점십자·**센트로이드별 절대원점 방향지시기**(custom series, 밴드색·투명도 승계). 설계 = `docs/idea/260704-hud.png`.
- **버그수정**(`3e5e11c`): ① 화살표 방향 절대원점→**밴드중심** 정정 · ② 줌/팬 시 글로우(zrender 절대픽셀) 분리→**dataZoom 이벤트 위치 갱신** · ③ custom series 삽입으로 밀린 `seriesIndex` 하드코딩(센트로이드 클릭/호버 회귀)→**`seriesId` 판단** 교체.

## 남은 것
- **머지**: `feature/emoi-cluster-v3b` → `feature/emoi-cluster` → `main`(라이브). 브라우저/모바일 실검수 후.
- roselia 1곡(DRM) → 작업 3 증분 파이프라인으로. 오디오 캐시(`audio_full` 659곡)는 동결 후 폐기 가능.
- (선택) pulse 전곡 확대(`build_pulse_all.py`, demucs CPU) + onsets lazy fetch.

---

# 세션 24~25 — 펄스 전곡 확대 + 렌더 lazy-fetch + 에너지 동적 subdivision (음원맵 클러스터링 마무리 · main 머지)

**음원맵(F2) 클러스터링/재생펄스 계열을 여기서 완결.** roselia DRM 1곡 확보로 전곡 660 완비 → 좌표·펄스 전곡화 → 렌더 최적화 → 재생 펄스를 "에너지 기반 동적 subdivision"으로 완성. `feature/emoi-cluster-v3b` → **main 머지**(fee5bd0) → `feature/emoi-cluster-v4`에서 렌더·튜닝 마무리.

## 데이터·추출 (전곡 660)
- **오디오 660/660**: roselia `競宴Red×Violet`(idx629) DRM을 `--extractor-args youtube:player_client=android_music`로 확보 → `audio_map.json` **660곡/13밴드/13센트로이드 재빌드·norm 660 재동결**(증분 append 수치 = `audio_map.json.norm`).
- **펄스 onset 전곡 660**: `build_pulse_all.py`(demucs htdemucs 4샤드 병렬) → `onsets/*.json`(박/8분/16분 3레벨 + 지각 pulse ACF). 원본 audio 미수정(librosa 읽기전용). 실험데이터 → `cluster/legacy/`.

## 렌더 lazy-fetch (task#4)
- onsets 전곡 ≈42MB → index.html 인라인 불가. `build.py` `load_onsets`(전곡 인라인) → **`load_onset_list`(경량 [band,song,id] 매니페스트)**, 데이터는 런타임 곡별 fetch(`16-audiomap.js _clFetchOnset`, `./src/content/cluster/onsets/<id>.json`, 캐시·file://→BPM폴백). **index.html 0.30MB**. `.nojekyll`로 Pages가 src/ 서빙.

## 재생 펄스 = 에너지 기반 동적 subdivision (핵심 결정)
- **진단**: `diagnose_pulse_variability.py`(full-mix tempogram → **circular octave% spread**; linear std는 90 fold경계 위양성). 전곡 스캔 `report/emoi-cluster-pulse/pulse_variability.csv` — ~70% 안정, ~22%만 곡내 pulse 변동(방안 B 후보).
- **방안 B(구간 tempo) 대신 '에너지 동적 subdivision' 채택**(사용자): 구조(intro/verse) 판별 없이 **에너지(음량)로 subdivision 제어**. `build_dynamics.py`가 full-mix **절대 음량(RMS dB)을 글로벌 앵커(−22~−7dB)로 정규화**(★곡별 아님 → 곡 간 절대 energy 보존: Symbol I=시종 dense·軌跡 1절=박)한 `dyn` 곡선(2Hz)을 onset JSON에 추가. `16-audiomap.js _clDynLevel`이 매 프레임 dyn으로 **박/8분** 선택(`CL_DYN_T1/T2`, `CL_DYN_MAX=1`=16분 끔, 히스테리시스).
- **볼륨 프리셋 4단계**(v 0.2/0.4/0.6 경계, `_clVolStep`): 1·2=발생안함 · 3(0.6~0.9)=24px·3px · 4(0.9~1.0)=48px·7px(`CL_PULSE_R3/LW3/SPEED3`). **경계는 곡 최대볼륨(`_clOnsetVmax`)에 상대화**(`CL_VOL_ADAPTIVE`).

## 버그·기타
- **광고 펄스 오발화**: 프리롤 광고 중 getCurrentTime로 onset 오발화 → `getDuration()`이 트랙 길이 ±5s일 때만 발화(`CL_ONSET_DUR_TOL`).
- **ikka_dumb_rock 색**: `BAND_COLORS` 키 오타(`ikka_dump_rock`→`ikka_dumb_rock`) 수정(배경·글로우 #ffaa33) + `assets/icons/ikka_dumb_rock.png` 남색→#ffaa33 재색칠.
- 음원맵 제목 **"밴드 음원 지도" → "EMOI-MAP"**(템플릿 동기).

## 산출물
- 도구: `build_pulse_all.py`·`separate_drums.py`·`build_beat_track.py`·`diagnose_pulse_variability.py`·`build_dynamics.py`(`src/tools/cluster/`).
- 문서: `docs/research/`(cluster-map-extraction·pulse-onset-extraction 논문) · `report/emoi-cluster-pulse/README.md`(방법론+프로브+구현) · `pulse_variability.csv`.
- 커밋(v4): 진단 `5dfbc42` · 광고펄스+박기본 `fb4ffba` · 동적subdiv `334a0eb` · 글로벌음량 `03a5dc1` · 프리셋튜닝 다수 · 볼륨적응 `afc9a75` · ikka색 `8602392`.

## 보류(향후, 착수 안 함)
- **방안 B(구간 tempo period)**: 프로토타입만(`section_pulse_proto.py`, tmp). millsage 172↔112 구간 검출까진 확인. 필요시 재개.
- 볼륨 정규화 max→p95(아웃라이어 완화) 옵션.
- onset 기본 subdivision 예외 큐레이션(`CL_ONSET_DEFDIV`).

---

# 세션 26 — 자동화 파이프라인(신곡 로더) 구축 + Pages 아티팩트 배포 전환 (feature/new-song-loader → main)

**작업 3 인프라 완성·배포.** 리팩터로 깨진 RSS 자동화를 복구하고, full-auto **신곡 로더**(감지→데이터→emoi-map/pulse 증분→라이브)를 GitHub Actions 2워크플로우로 구축. **index.html을 Pages 아티팩트 배포로 전환(Option A)** → 자동화의 데이터-only 커밋과 사용자 핫픽스가 생성물에서 충돌하는 것을 원천 차단. deploy·감지·게이트 실증 green. **남은 것 = 오디오 경로 E2E 검증 1회**(HANDOFF 작업 3).

## 버그 원인 (깨진 자동화)
- `rss.yml`이 `db0771c`(레이아웃 리팩터 `tools/`→`src/tools/`, `data/`→`src/content/songs/`) 후 **스크립트 경로 미갱신** → `python tools/collect/youtube_rss.py` 없음으로 잡 실패(정적파일 분할 `d9f3b1b`은 무관·오해). 스크립트 내부 경로는 이미 마이그레이션됨 → **rss.yml 은퇴**(PR `--propose` 코드는 `youtube_rss.py`에 수동용 보존), `pipeline.yml`로 대체.

## 5단계 배선 (기존 모듈 재사용 = 얇은 오케스트레이터, spec §3)
- 신규 **`actions/orchestrate.py`**: ① `youtube_rss.collect_candidates()`(감지, dedup=커밋 YAML=idempotent) → ② `insert_track`(songs/*.yaml 수술삽입) → ③ `append_song_map`(좌표) → ④ `separate_drums`→`build_beat_track`→`build_dynamics`(pulse) → ⑤ **데이터-only 커밋·rebase-retry push**. **곡별 fail-soft**(공유파일 스냅샷 복원, 실패곡=흔적없이 스킵→다음 실행 재감지). fetch_audio는 단곡 인자 없어 **임시 매니페스트 1행**으로 호출, build_dynamics도 그 임시 매니페스트 `--start 0`.
- 신규 **`src/tools/cluster/append_song_map.py`**: `build_perceptual_map.feats()` + `audio_map.json.norm`(동결) → 신곡 raw contrast/mode를 동결 공식으로 z변환 → **재다운로드 없이** `songs[]` append + **해당 밴드 centroid 재계산**(baked centroid라 focus/재생 HUD가 이 값을 읽음) + `metrics.n`. 4-space pretty-print 유지. ⚠️ **idx=전역 max+1로 CSV 끝 append** — `build_manifest` 재실행은 전역 재번호=커밋된 onset 파일명 붕괴, **금지**. **검증: `afterglow__000` 동결 norm 재현 = x16.57 y33.52 bpm123.0 = 커밋값 정확 일치.**

## 워크플로우 2개
- **`pipeline.yml`**(cron 04:00 KST + dispatch): **감지 게이트** — `pyyaml`만으로 `--detect-only` 실행, `$GITHUB_OUTPUT`의 candidates>0일 때만 setup-node+오디오스택(torch CPU·demucs·librosa…) 설치+처리 → 0곡 날 무거운 설치 스킵. `contents/issues: write`. **실증: 첫 실행 152 dedup·0곡→스킵→green.**
- **`deploy.yml`**(main push `src/**·static/**·assets/**` + dispatch): `build.py`→루트 index.html 생성 → `_site`에 index.html+static+assets+**onsets**(런타임 lazy-fetch) 스테이징 → **upload-pages-artifact→deploy-pages**. `pages/id-token: write`. 커밋 안 하므로 push 루프 없음. **실증: 아티팩트 24.9MB 배포 성공·라이브 재배포**(https://sbb2002.github.io/bandori-song-sorter/).

## Option A 전환 (사용자 조치 완료)
- repo Settings→Pages→Source=**"GitHub Actions"** 전환 + 첫 배포 성공 확인. `.gitignore`에 `/index.html` 추가(커밋 해제 `git rm --cached`는 선택, 현재 index.html은 무해한 vestigial).

## E2E dry-run 테스트 모드 (레포 무변동 검증 수단)
- `orchestrate.py --test-band --test-video`(+`--dry` 필수): 감지 건너뛰고 지정 곡 1개 **다운로드→demucs→pulse→좌표** end-to-end 실행하되 **커밋/푸시 없음** → CI 러너 폐기로 레포 무변동. `pipeline.yml` workflow_dispatch inputs(`test_band`/`test_video`)로 트리거. **용도: CI 다운로드 봇월 여부(spec §4 미검증 리스크) 안전 관측.** 테스트법 = HANDOFF 작업 3.

## 산출물
- 신규: `actions/orchestrate.py` · `actions/requirements.txt` · `src/tools/cluster/append_song_map.py` · `.github/workflows/pipeline.yml` · `.github/workflows/deploy.yml`. 삭제: `.github/workflows/rss.yml`. 수정: `.gitignore`(+`/index.html`) · `HANDOFF.md`.
- 로컬 env: 오디오 스택=`hummingbird` conda env(librosa/scipy/soundfile), 경량=base(pyyaml/jinja2) — 단일 env로 전체 e2e 불가, CI가 검증 무대(memory `python-envs`).

## 남은 것 (HANDOFF 작업 3)
- **E2E dry-run 테스트 1회** → CI 다운로드 봇월 여부 판명 → 막히면 대책(버너 쿠키/클라이언트 로테이션/셀프호스티드, spec §4).
- DRM `競宴Red×Violet` 자동 불가(fail-soft 스킵). 영구실패 재시도 상한 가드 = 후속.

---

# 세션 27 — CI 다운로드 봇월 확정(E2E 3회) → 반자동 전환 결정 (feature/new-song-semiauto)

**작업 3 인프라(세션 26)의 마지막 미검증 = CI 오디오 다운로드 경로를 E2E dry-run으로 검증 → ⛔ 봇월 확정.** GitHub Actions(Azure 데이터센터 IP)에서 YouTube 다운로드가 `Sign in to confirm you're not a bot` hard-block에 막힘. 대책(spec §4)을 약→강으로 실증 소진 후 **반자동(다운로드만 로컬 레지덴셜 IP)** 아키텍처로 전환 결정.

## E2E 실증 3회 (전부 `--dry`, 레포 무변동)
`gh workflow run pipeline.yml --ref <branch> -f test_band=afterglow -f test_video=09B-WljIiTo` (ON YOUR MARK, 확실히 받아지는 영상).
- **run `28789165878`(main)**: 기본 클라이언트 → `[youtube] Downloading android vr player API JSON`에서 `hard-block(block)` rc=2. **다운로드 직전까지 전 스텝 green**(checkout·python·node·오디오스택 설치·git identity) → 벽은 오직 다운로드. demucs/pulse/좌표는 wav 없어 **미도달**(process_song이 다운로드 실패 시 즉시 return None).
- **run `28789906761`(feature/ci-download-client-rotation, 커밋 `dfdb1e5`)**: orchestrate.py fetch_audio 호출에 `--extractor-args youtube:player_client=tv,web_safari,ios` 주입. 로테이션 **작동 확인**(로그가 web safari→ios 시도) **그러나 셋 다 hard-block**.
- **run `28791454189`(같은 브랜치, 커밋 `6e861ed`)**: PO 토큰 — pipeline.yml에 bgutil provider Docker 기동(127.0.0.1:4416, 헬스체크 ✅), requirements `bgutil-ytdlp-pot-provider` 플러그인, 클라 `web_safari,tv,mweb`. provider 정상·클라 전환 확인됐으나 **셋 다 hard-block**.

## 결론 (확정)
- **벽 = 클라이언트가 아니라 데이터센터 IP 평판.** spec §4 카드 ①(yt-dlp 최신, CI가 이미 2026.7.4)·②(로테이션)·PO토큰(익명 visitor)까지 소진. bgutil=계정無 익명 토큰이라 안전하나 약함.
- **Render 등 다른 클라우드도 동일**(전부 AWS/GCP/Azure 데이터센터 IP; Discord 음악봇 PaaS 사례 다수). 클라우드로는 도망 불가.
- **본계정 PO토큰/쿠키는 부적합**: 데이터센터 IP 플래그 리스크 + PO토큰 수시간 만료(일일 cron 부적합) + 매칭 쿠키 필요 + IP가 여전히 벽. 버너 쿠키는 최후 수단으로 보류.
- ★**핵심 확증**: 다운로드 이후(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트 없음 → **다운로드만 레지덴셜(집) IP로 빼면 나머지 100% 자동.** 집 IP 다운로드는 전곡 660 벌크로 이미 실증.

## 채택 = 반자동 (계획 `~/.claude/plans/floofy-tickling-corbato.md`)
1. **(Actions, 매일 23:00 KST)** `orchestrate.py --detect-only --notify` → 미처리 신곡 요약 Telegram 1건(다운로드 안 함).
2. **(Local, 원커맨드)** 전용 클론에서 다운로드(집 IP)→demucs/pulse→좌표 append→push main→deploy 자동.
- 격리: 전용 로컬 클론(데브 핫픽스 워킹트리와 분리). 코드 = `src/tools/pipeline/`(run_local.py·notify.py) + orchestrate `--notify` 신설. pipeline.yml은 감지+알림 전용으로 재작성. 구현/검증 = 진행 중(HANDOFF 작업 3).
- 폐기: 실험 브랜치 `feature/ci-download-client-rotation`(로테이션·PO토큰 커밋) — CI 다운로드 포기로 무용.

# 세션 28 — 신곡 로더 반자동 파이프라인 운영화: 봇 통합·상쇄·리네이밍·로컬 Telegram 통지 (2026-07-07, main 직접 머지)

세션 27 반자동 아키텍처를 실운영 형태로 다듬음. 6개 독립 변경을 브랜치별 커밋 후 main 머지.

## 1) telegram 명령 봇 정리 (docs/idea/260707.md 고찰 반영)
- `/detect` deprecated·제거 — 감지는 일일 크론이 자동 수행하므로 수동 트리거 불필요.
- 한 실행에 밀린 명령 중 `/pause`→`/resume`이 순서쌍이면 서로 상쇄(무효 처리, 상태변경·응답 없이 skip) + "함께 도착해 상쇄" 안내 1건. 2-패스(큐 수집→상쇄 판정→실행).
- 커밋 030d796. 실운영 검증: run 28835461588(status/pause/resume)·28835571685(pause/status/resume) 로그에서 상쇄 skip 확인.

## 2) 5분 폴러 → 단일 23:00 크론 통합
- 문제: `telegram-bot.yml`(5분 폴링)과 `pipeline.yml`(일일 감지)이 분리 → "명령 수신→파이프라인 기동→결과 알림"이 한 실행으로 안 이어짐.
- `telegram-bot.yml` 제거, 명령 처리 단계를 `pipeline.yml` 맨 앞으로 흡수 → 매일 23:00 KST 한 실행에서 [명령 처리(help/status/pause/resume) → paused 아니면 감지 → 알림] 순차. permissions `contents:write`(상태 커밋). 트레이드오프: 명령 응답은 최대 하루 지연이나 인프라 단순화.

## 3) 감지 알림 개선
- `orchestrate.py --notify`가 candidates>0 조건 없이 매 실행 전송 → 신곡 0곡도 "신곡 0곡 발견(미처리 없음)" Telegram 1건. 감지가 실제로 돌았는지 무응답으로 의심할 일 제거.

## 4) 리네이밍·디렉터리 정리
- `src/tools/pipeline/` → `src/tools/semiauto-loader/`(역할 명확화) + 폴더 README.md 신설(상황별 실행 파일 표).
- 루트 `actions/`(orchestrate.py·bot_state.json·requirements.txt) → `src/tools/semiauto-loader/` 흡수. 'actions'는 GitHub 예약어와 이름만 겹칠 뿐 특별 역할 없음. ⚠️ orchestrate.py ROOT `parents[1]`→`parents[3]` 재계산(안 고치면 레포 루트 오인 → 데이터 경로 붕괴).

## 5) run_local.py 결과 로그·메시지 개선
- orchestrate 내부 subprocess가 성공 시 출력을 통째 삼키던 것 → 기본 스트리밍(터미널에 실시간 노출, quiet=True만 억제).
- run_local이 orchestrate 출력을 tee하며 종료 후 [신곡 0건 / N곡 반영 / 전부 실패 / 오류]를 구분된 한 문장으로 정리(기존엔 rc==0이면 무조건 "완료" 문구라 0건도 배포된 듯 오해).

## 6) 로컬 처리 결과 Telegram 통지 + notify .env 자동 로드
- run_local이 결과 문장을 터미널과 동일하게 `notify.send_telegram`로 1건 전송(다운로드+demucs가 곡당 수 분 → 자리 비워도 완료/실패 수신). --dry·--test-video는 통지 안 함.
- notify.py에 repo 루트 `.env` 자동 로드(환경변수 우선, python-dotenv 무의존 = youtube_api.load_env_key 규약). CI는 secrets로 no-op, 로컬은 `.env`의 TELEGRAM_BOT_TOKEN·TELEGRAM_CHAT_ID.
- 로컬 통지 라이브 확인: `.env` 키 오타(`TLEGRAM_CHAT_ID`→`TELEGRAM_CHAT_ID`) 수정 후 send 성공. (.env는 gitignore·비커밋.)

## 상태
✅ 반자동 파이프라인 운영화 완료·라이브. 남은 것 = (선택) 다운로드 이후 분석-only 스크립트(분석 라이브러리 없는 로컬용, run_local은 유지) · DRM 1곡 수동.

---

# 세션 29 — EMOI-MAP 딥스페이스/별 시각화: 곡=에너지 별 + canvas 별밭 + 밴드 성운 (2026-07-07, feature/emoi-map-starfield → main 104e709)

음원맵 곡 점(660)을 **딥스페이스에 떠 있는 별**처럼 표현(HANDOFF 작업 4). 기존 HUD·격자·펄스·클릭 재생·줌/팬·툴팁은 전부 유지, 별 표현은 그 위에 얹음.

## 1) 곡 점 = 빛나는 별 (energy 구동)
- `songMark`(`16-audiomap.js`): 곡 점 = 밝힌 밴드색 코어 + 흰 림 + **에너지 비례 글로우**(shadowBlur). 재생 곡=가장 밝은 별(테두리+글로우 강조) · ALL 개요=작게(엉겨붙음 완화, 색 유지) · 호버 흐림=글로우 억제. dim(0.62)·3상태 로직 보존.
- **별 밝기 = 곡 에너지**: onset `dyn.v`(2Hz 정규화 RMS) 평균 → 전곡 percentile rank(0~1) → `src/tools/cluster/add_energy.py`(신규, base env)가 `audio_map.json songs[].energy`에 baked(660/660). 재분석·재다운로드 불필요(순수 파생). 없으면 프론트 0.5 폴백.

## 2) 딥스페이스 배경 + 별밭 canvas + 밴드 성운
- 배경 = `.cluster-wrap` 딥스페이스 그라데이션 + `isolation`(스택 컨텍스트). `#cluster-chart` z-index:1(투명 ECharts 캔버스라 뒤가 비침), `#cl-starfield` z-index:0. (`desktop.css`)
- 데이터 뒤 canvas `#cl-starfield`(JS 동적 생성, `_clBuildSensTabs` 패턴 = 새 파일·템플릿 무변경) = **반짝이는 별밭 + 느린 드리프트**(rAF 루프, 가산합성 `lighter`, 면적 비례 개수, 탭 숨김 시 정지). `_clSky*`/`_clSkyTick`/`_clBuildStarfield`.
- 밴드 포커스 시 밴드색 **성운**(`_clSetNebula` → 루프가 부드럽게 lerp) — 구 `_clBandBg` 배경 통째 교체 대신 `_clDraw`가 성운 색만 갱신. ALL/various_artists는 성운 off.

## 3) Ave Mujica EMOI-MAP 전용 색
- Ave Mujica 색(`#881144` 다크 와인)이 딥스페이스 배경과 톤이 겹쳐 강조 안 됨 → `CL_COLOR_OVERRIDE={ave_mujica:'#e64c8c'}`(밝은 로즈 마젠타) + `_clBandColor()` 헬퍼. **EMOI-MAP 내부에서만** 적용(곡 색·글로우·성운·화살표·유사곡 점), 전역 `BAND_COLORS`(워드클라우드·리스트 공유)는 **불변**.

## 편집 규칙 / 커밋
- JS(`16-audiomap.js`)·CSS(`desktop.css`) 분할파일 직접수정 = 리빌드 불필요 · 별밭 캔버스 JS 생성 · **energy 반영만** `python src/build.py`(index.html은 gitignore = deploy CI 재생성).
- 커밋: `a8e5367`(별밭+energy+add_energy.py+HANDOFF) → `1af855c`(좌표계 고찰 핸드오프 docs) → **`104e709` main 머지**(--no-ff). 계획 원본 = `~/.claude/plans/emoi-map-proud-valley.md`.

## 롤백
- `songMark` 고정 size/op 복귀 · `.cluster-wrap` 배경 `var(--surface2)` · `_clBuildStarfield` 미호출. energy 필드는 남아도 무해.

## 상태
✅ 완료·main 머지·푸시(104e709). 후속 = **작업 5 EMOI-MAP 좌표계 고찰**(260708, HANDOFF § 작업 5) — 다음 세션 `feature/emoi-map-starfield`에서.

---

# 세션 30 — 작업 5: EMOI-MAP 좌표계 고찰 (Phase A 정직화 + B0·C 정서축 연구) · main 머지 172684e (2026-07-07)

작업 5 완결. 브랜치 사슬 A(`feature/emoi-map-starfield`) → B0(`feature/emoi-cluster-energy-tempo`) → C(`feature/emoi-starfield-timbre-valence`) → main(`--no-ff` 172684e, Pages 배포). 상세·판정·재현은 논문 [../research/emotion-axes-extraction.md](../research/emotion-axes-extraction.md).

## Phase A — 맵 정직화 (라이브, 커밋 a6ad2bf)
- **축 라벨 괄호 한정**: x `거칢(음색)`/`매끄러움(음색)`, y `밝음(장조)`/`어두움(단조)` — "리듬의 거칢"·"경쾌=밝음" 오독 차단.
- **energy 노출**: 툴팁 `· 에너지 NN%`(`songMark._e`) + 헤더 범례 칩 `★ 밝기·크기 = 곡 에너지`(`_clBuildEnergyLegend`·`.am-legend`) + **코어 색 명도 = energy**(`_clEnergyColor` L 0.40~0.82, hue/채도 유지, `_clPulseColor` L오버라이드 재사용).
- **n=1 override**: millsage `dx=−18`(x 13.93→−4.07), ikka `dy=+18`(y −9.28→+8.72). 근거 1지각점≈18좌표(norm k=25·좌표 σ≈24·r회귀). `overrides`+`norm.overrides`+baked 좌표+`BAND_OVERRIDES` 일관 기록, **만료=n≥5**. 잠정 별 = centroid n<3 반투명(×0.5)+툴팁 `n=1·잠정`.
- **ave_mujica** EMOI-MAP 색 오버라이드(#e64c8c) 제거 → 원 지정색 `#881144`(와인) 복귀(명도 변조가 가시성 보정 대체, `CL_COLOR_OVERRIDE={}`).
- 파일: `audio_map.json`(+build.py)·`16-audiomap.js`·`desktop/mobile.css`·`build_perceptual_map.py`. 브라우저 실검수 통과.

## Phase B0 — onset 파생 arousal 스크리닝 (전멸, 커밋 98290d9)
- onset JSON 파생 9종(E1 mean·E2 LRA근사·E3 온셋밀도·dyn std/p90/p10·ACF pulse_bpm·librosa tempo) × 손라벨 energy/tempo(n=30) → **PASS 0/9**. 원인 = `dyn.v`가 재생펄스용 곡별 정규화값이라 절대 에너지 씻김.
- 산출 `report/cluster-energy-axis/`(onset_features.csv 660·correlation·screening.png). 도구 `b0_{onset_features,correlate,plot}.py`.

## Phase C — 정식 오디오 feature 3정서축 (timbre×valence 확정 / arousal 불가, 커밋 c4031b0)
- `audio_full` 원본에서 정식 feature 18종(LUFS·LRA·rms변동·tempogram·VBL·HPSS + `timbre()`·`mode_valence()` 재사용) × 손라벨 4축(rough/valence/energy/tempo, n=30, 곡당 ~4.4s).
- **Timbre** `contrast`×rough r=**−0.815** PASS · **Valence** `mode`×valence r=**+0.576** PASS(합성 mode+centroid+harmonic R=0.595 미개선 → mode 유지).
- **Arousal 탈락**: 전용 feature(LUFS·LRA·tempo_acf·VBL·rms변동) 전멸 · **측정 템포 tempo_acf×지각 tempo r=0.087**(측정≠지각) · 지각 energy/tempo는 스펙트럴 밝기(centroid·rolloff r≈0.6)가 잡으나 **contrast와 collinear(r≈0.52)라 독립 축 아님**.
- **"실질 1.x차원" 확증**(contrast가 rough·energy·tempo·valence 4라벨 지배). **결정**: x=timbre·y=valence 유지, arousal 새 축 없음, Millsage·Ikka는 Phase A override가 최종.
- 논문 `docs/research/emotion-axes-extraction.md`. 산출 `report/emotion-axes/`. 도구 `phasec_{features,correlate,plot}.py`(`--full`로 전곡 추출 가능·진행률/pause·resume).

## 데이터 보관 (사용자 요청 — 폐기 금지)
- 두 조사 데이터 커밋 보존: `onset_features.csv`(660) · `phasec_features.csv`(30) · 각 correlation/png.
- `audio_full`(660·15GB) 로컬 보존(gitignore). 전환성 `*_progress.json`·`*_control.json`만 gitignore.

---

# 세션 31 — done 이관·HANDOFF 슬림화 + EMOI-MAP minor fix (2026-07-08, fix/emoi-map-labels-pulse → main)

작업 1·2·3·5의 본류 완료를 git·done 대조로 확인하고, HANDOFF의 완료 상세 절을 done 참조로 축약(readme 규칙 적용).

## 완료 확인
- **작업 1**(워드클라우드) = 완전 완료(done 20·22), 잔여 없음.
- **작업 2**(음원맵 전곡) = 완결·동결(done 23), v3b→main 머지됨. 잔여는 선택적 구파일 폐기뿐.
- **작업 3**(반자동 파이프라인) = 운영화 완료·라이브(done 26·27·28).
- **작업 5**(좌표계 고찰) = A·B0·C 완료·머지(`172684e`, done 30).

## 부분 미완 1건 (본류 밖 · 백로그 이동)
- **작업 3 분석-only 로컬 스크립트**: HANDOFF에 `(사용자 요청)`으로 명시됐으나 **미구현**. 반자동 본류(감지→알림→`run_local.py` 일체형 처리)는 라이브지만, 다운로드/분석 역할 분리 편의 스크립트는 아직 없음. 본류 밖이라 § 보류·백로그로 이동.
- 기타 잔여(DRM 1곡·구파일 정리·재시도 가드 등)도 전부 선택 → § 보류·백로그로 통합.

## 문서 변경
- HANDOFF: 갱신선 세션 31 추가 + § 작업 1·2·3·5 상세 절을 요약+done/spec/논문 링크로 축약 · 완료된 과거 실행 기록(구 '병렬 실행 계획' 블록) 제거 · 선택 잔여를 § 보류·백로그로 집약.
- done: 본 세션 31 항목 append.

## EMOI-MAP minor fix (사용자 요청 3건 + research 규칙)
- **축 라벨 표현 개선**(`audio_map.json` axes): x `거칢(음색)/매끄러움(음색)` → `음색이 거친/음색이 부드러운`, y `밝음(장조)/어두움(단조)` → `발랄한 느낌/진지한 느낌`. `python src/build.py`로 index.html(CLUSTER_DATA baked) 재생성 → 4모서리 축 라벨(`_clAxisLabels`)·방향 화살표 라벨 자동 반영. (index.html=gitignore, deploy가 CI 재빌드.)
- **재생 HUD 밴드평균 기준화**(`16-audiomap.js` `_clUpdateHud`): 재생곡 절대좌표 표시 → 밴드 평균점(centroid) 대비 편차로 변경. `밴드 평균점으로부터 거리 r` · `밴드 평균보다 |dx|만큼 거침(부드러움)` · `밴드 평균보다 |dy|만큼 발랄함(진지함)`(편차 부호로 거침↔부드러움·발랄↔진지 단어 선택).
- **펄스 16분 주석 비활성**(`_clDynLevel`·상수): 이미 `CL_DYN_MAX=1`로 16분(레벨2)이 clamp돼 박/8분만 표시되던 상태 → 계산 경로는 유지하고 주석으로 "clamp 비활성" 명확화(사용자 지시=제거 말고 주석 정도). `CL_DYN_MAX=2`로 올리면 16분 부활.
- **research 작성 규칙**(`docs/research/README.md`): 논문 양식(초록→동기→방법→실험여정[판정 이모지]→전환점→최종방법→한계→재현)·승격 기준(report에서 "고민한 탐색"만)·문체 원칙(시간순 서사·음의결과 보존·절대날짜) 명문화 + emotion-axes-extraction.md 등재.
- 밴드 포커스 HUD·부제·주석의 옛 용어(거침/밝음)는 요청 범위 외라 미변경.

## 문서화 경로 규칙 확립 + 축 라벨 버그 수정 (후속)
- **문서화 경로 규칙**(`working/readme.md` 「구현 유형별 문서화 경로」): 작업을 분석 시도 횟수로 분류 — 단순구현(0회)=done · 분석 필요(1회)=+report(수치·표·플롯·그림 + 간단 해석) · 2회 이상 분석 후 종결=+research(논문화, 그림·표·플롯 전부). research/README 승격 기준도 "2회+분석·종결"로 일치·상호링크.
- **축 라벨 버그 수정**(`16-audiomap.js`·`desktop.css` · 단순): ALL 개요는 auto scale이라 원점(0,0)이 화면 중앙이 아닌데 축 방향 라벨은 CSS 50% 고정 → 축선(markLine x=0·y=0)과 어긋남. `_clPositionAxisLabels()` 신설(`convertToPixel`로 x=0·y=0 픽셀 위치를 구해 top/bottom 라벨은 `left`, left/right 라벨은 `top`에 정렬) → `_clDraw` 끝·`dataZoom`·`resize`·초기화에서 호출. #cluster-chart가 .cluster-wrap(relative)을 100% 채워 캔버스 픽셀=라벨 부모 좌표(offset 무). + 축 라벨 폰트 0.56→0.68rem.

## HANDOFF 병합 충돌 마커 제거 + 완료 절 완전 삭제 (추가 슬림화)
- **버그 발견**: `docs/working/HANDOFF.md`에 git 병합 충돌 마커(`<<<<<<< Updated upstream`/`=======`/`>>>>>>> Stashed changes`)가 3곳 그대로 커밋돼 있었음(직전 커밋 `c3bdf76`이 "Solved: Conflict"라 되어 있었으나 실제로는 마커 미제거). 세션 31 최신본("Updated upstream")과 `feature/emoi-map-starfield`의 구버전("Stashed changes")을 대조 → 구버전 내용이 이미 § 보류·백로그에 전부 반영돼 있어 유실 없이 구버전 블록 삭제, 마커 제거(`e94c93d`).
- 관련해 stale `stash@{0}`(같은 브랜치의 구 HANDOFF WIP, main이 이미 앞질러 무의미) 삭제. `src/content/cluster/onsets/afterglow__000.json`의 unstaged 변경(pretty-print 차이뿐, 데이터 동일 — 사용자 확인)은 `git checkout --`로 되돌림.
- **readme.md 규칙보다 한 단계 더 슬림화**: 완료된 작업(잔여 없음)은 "done N 참조" 한 줄도 남기지 않고 **§ 작업 N 절 자체를 삭제** — 우선순위 표(✅ + done 링크)만으로 충분하고, 상세 절 내용은 어차피 done.md·spec·research에 이미 있어 3중 중복이었음(작업 1·2·3·5 전부 해당, 작업 4는애초 절 없이 표만 있었음). 남기는 값어치가 있던 "16-audiomap.js·desktop.css 직접수정" 편집 컨벤션만 § 참고(TODO 아님)로 이전.
- **readme.md 갱신**: HANDOFF.md 규칙에 "잔여 없는 작업은 절 자체 삭제(표+done 링크로 충분)" 명문화.

# 세션 32 — 오디오 피처 유효성 3중 렌즈 분석: Spotify 벤치마크 + 우리 샘플 교차검증 (2026-07-08, analysis/audio-feats · main 미머지)

EMOI-MAP 프록시가 "장르 구분에 유용한 종류의 신호인가"를 큰 공개 데이터로 교차검증 → **단·이·다변량 3중 렌즈** 방법을 확립하고 우리 로컬 샘플에 이식. 2회+ 분석·종결로 research 승격. **EMOI-MAP 소스 미변경**(축 개편은 전곡 재검증 후 별도 세션). 깊은 서사·수치·그림은 논문 [../research/feature-validity-extraction.md](../research/feature-validity-extraction.md).

## Phase 1 — Spotify Tracks Dataset(side-project) 3중 렌즈
- **단변량**(장르별 ANOVA η², [report-genre_audio_features.md](../../side-project/spotify-tracks-dataset/report-genre_audio_features.md)): 합성 변수(`acousticness` 0.488·`energy`·`instrumentalness`·`loudness`)가 장르 구분 상위, `key`/`mode`/`time_signature`는 무관.
- **이변량**(변수쌍 Pearson r, [report-pairwise_scatter.md](../../side-project/spotify-tracks-dataset/report-pairwise_scatter.md)): `loudness`↔`energy` r=+0.762(중복 정황) · `popularity`는 오디오와 무상관 · `loudness`↔`danceability` 등 여러 쌍에서 장르별 부호반전 = 집계 역설(Simpson's paradox).
- **다변량**(VIF+RF+permutation importance, [report-feature_validity.md](../../side-project/spotify-tracks-dataset/report-feature_validity.md)): `energy`/`loudness` 다변량 기여도 급락(중복→저평가) · `popularity` 다변량 1위 반전(비오디오·이식 불가) · `acousticness`/`instrumentalness`는 고유 정보 유지. RF 파라미터 과대(300트리·max_depth=None → 37분 미완)를 규제(150트리·depth15·leaf10)로 해결.

## Phase 2 — 우리 샘플 285곡 교차검증
- 로컬 프록시(genre-features)에 동일 다변량 방법 적용(`src/tools/cluster/genre_features_validity_rf.py`, 표본 20↑ 6밴드·270곡): 프록시+원재료 동시 투입 시 VIF=inf(정확한 선형결합) → 원본 12피처만 검증. 스펙트럼 형태 지표군(`centroid`/`rolloff`/`zcr`/`flatness`) VIF 9~52 상호중복 → PI 최하위(Spotify `loudness`↔`energy` 패턴 재현). `contrast`/`rms`/`harmonic_ratio`/`flux`가 고유 상위. `energy_proxy` 3성분(rms+contrast+flux)이 상위권과 일치 = 성분 선택 사후 검증. 상세 [report/genre-features/README.md](report/genre-features/README.md).

## Phase 3 — research 승격
- [../research/feature-validity-extraction.md](../research/feature-validity-extraction.md)(3중 렌즈 종합 논문, Spotify+우리 샘플) + 그림 `featval_fig1~7`(신규 slope·VIF-PI 산점 2종). `../research/README.md` 등재.

## 결정
- 프록시 우선순위: **`harmonic_ratio`(acousticness 축) 확정 → `energy_proxy` 3성분 유지 → `instrumentalness`는 Demucs 측정 개선 후 재판단.** `popularity`류 비오디오 변수 제외.
- 최종 축 개편은 전곡 660 캐시로 3중 렌즈 재검증 후 별도 결정(작업 6 진행 중).

## 파일
- side-project: `report-{genre_audio_features,pairwise_scatter,feature_validity}.md` · `{scatter_pairwise,feature_validity_rf}.py` · `fig/{scatter-pairwise,feature-validity}/`
- 로컬: `src/tools/cluster/genre_features_validity_rf.py` · `report/genre-features/{README.md,feature_validity_*.csv}`
- research: `feature-validity-extraction.md` · `figures/featval_fig1~7`
- 커밋(analysis/audio-feats): 21f6631 · 77986f9 · c268a31 · 2189bc7 · 3f9145b

# 세션 33 — 오디오 피처 유효성: 전곡 660·13밴드 3중 렌즈 재검증 (2026-07-08, analysis/audio-feats · main 미머지)

세션 32 부분 캐시(285곡·10밴드, 다변량 6밴드) 잠정 결론을, 전곡 오디오(660곡·13밴드)를 보유한 이 로컬에서 재검증. **부분 캐시 3대 결론이 메탈/전자 밴드 포함 전곡에서 유지되는지** 확인이 목표. EMOI-MAP 소스 미변경. 상세 수치는 [report/genre-features/README.md](report/genre-features/README.md) "전곡 660 재검증" 절 · 논문 §8.

## 환경·절차
- **`hummingbird` env 불필요**: 이 로컬 base(`C:/Users/User/miniconda3`)에 librosa·soundfile·numpy·pandas·scipy·sklearn·matplotlib·yt_dlp 전부 설치 확인 → 4단계(sample→extract→analyze→validity_rf) 전부 base python으로 실행.
- **오디오 이미 로컬 확보**(`audio_full` 660): `--download` 미사용. 스테일 285행 `song_features.csv`는 제거(git 이력에 보존)하고 빈 상태에서 extract append/resume 시작.
- **게이트 먼저**(사용자 결정): N=15 밴드 균등 샘플(13밴드·157곡, seed=42) → `analyze` η²·프록시로 판정 → 통과 후 `extract --all`로 전곡 660 확장(resume append). 스냅샷 `band_anova_summary_sample15.csv`·`song_features_with_proxies_sample15.csv`.
- 주의: `validity_rf.py` `MIN_BAND_N=20`이라 N=15 균등 샘플에선 전 밴드 탈락 → 다변량은 전곡 단계 전용(게이트는 단변량 η² 중심 — 명세와 일치).

## 게이트(N=15 균등 13밴드) — 통과
- η² 상위군(`rms`·`contrast`·`harmonic_ratio`·`flux`) 유지, `tempo_excerpt` 비유의(p=0.61). 밴드별 `acousticness_proxy`: morfonica 최고(+1.83, 바이올린)·raise_a_suilen 최저(−1.20, 전자) → 가설 방향 확인(roselia는 심포닉메탈이라 중간 +0.14).

## 전곡 660·13밴드 결과 — 3대 결론 확증·강화
- **단변량 η²**(13밴드): `rms` 0.314·`harmonic_ratio` 0.287·`contrast` 0.284가 top-3(세 데이터셋 공통 안정). η² 절대값은 밴드↑·표본↑로 하락(정상). **`tempo_excerpt` 비유의**(p=0.15) → 강등(새 발견).
- **다변량**(VIF+RF PI, 10밴드·653곡, test acc 0.439 = chance 0.10의 4.4배): ① 스펙트럼 형태 지표군(`centroid` VIF48.8·`rolloff` 25.3·`zcr` 16.3·`flatness` 12.3) 상호중복 → PI가 0 근처/음수로 **붕괴**(부분 캐시보다 더 선명; `rolloff`만 RAS 극단 밝기로 +0.034 살짝 양수). ② `energy_proxy` 3성분(`contrast` 0.102·`rms` 0.058·`flux` 0.038) 전부 PI 상위 4위 안. ③ `acousticness_proxy`는 `harmonic_ratio`(0.082) 주도, `flatness`(−0.011) 기여 0.
- **메탈/전자 대비 등장**: `acousticness_proxy` morfonica +1.87 … roselia −0.08 … mugendai −0.60 … raise_a_suilen −1.03. RAS 음의 끝은 `flatness`(노이즈) 극단이 구동(harmonic 저하 아님).

## 결정·다음
- **프록시 우선순위(harmonic_ratio·energy_proxy 3성분)는 데이터로 확증.** 단 EMOI-MAP 축/시각화 실제 개편은 여전히 별도 결정.
- **다음 = EMOI-MAP 시각화 실험**: Idea A(곡별 대표 파형 — harmonic→acoustic wave·밝기→sawtooth·flux→busy) 채택(사용자, flux는 pop도 잡아 "electric" 명명 재고). + Demucs 스템 펄스(킥 1·3박/스네어 2·4박 분리 시도, 멜로디밴드[other]는 정박 에너지를 미약 파동으로, 베이스는 애매하면 skip). **리스크 작은 순서대로 각각 브랜치 만들어 UX 비교.**

## 데이터 검증
- 게이트 추출 157곡·13밴드 균등(실패 0). 전곡 추출 660곡·13밴드(밴드별 수 = 오디오 파일 수와 일치, 실패 0). validity_rf kept_bands 10(roselia·poppin_party·raise_a_suilen 포함), dropped {various_artists 5·millsage 1·ikka_dumb_rock 1}.

## 파일
- 재생성(전곡 660): `report/genre-features/{song_features.csv, song_features_with_proxies.csv, band_anova_summary.csv, *_violin.png, feature_validity_{vif,importance}.csv, feature_validity_run_summary.txt, sample_manifest.csv}`
- 신규 스냅샷: `band_anova_summary_sample15.csv` · `song_features_with_proxies_sample15.csv`(N=15 게이트)
- 산문: `report/genre-features/README.md`(전곡 재검증 절) · `research/feature-validity-extraction.md`(§8) · `HANDOFF.md`(작업 6·마커) · `done.md`(본 항목)
