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
