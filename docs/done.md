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
- **디자인**: `docs/bandori-song-sorter-mockup.html`을 주 디자인으로 채택. 검증된 조각(밴드 아이콘, YT IFrame API, 롱프레스 350ms, domtoimage, fixPath) + 모바일 반응형 + localStorage 결합.
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
