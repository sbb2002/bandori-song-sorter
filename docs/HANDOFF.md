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
- ⚠️ **실브라우저 클릭 확인 보류 (사용자가 직접 검토 후 결과 회신 예정)**:
  1. **유튜브 실제 재생** — YT IFrame 연동(헤드리스+무네트워크라 미확인)
  2. **Download PNG 생성** — dom-to-image 캡처(클릭 + CDN 필요)
  3. **링크 복사** — clipboard(사용자 제스처 + secure context 필요; file://은 fallback 동작)
  - → `index.html`을 실제 브라우저로 열어 위 3가지를 확인 필요. 사용자가 자세히 검토 예정.

## Notes
- 원본 보존: `backup/main-before-redesign` 브랜치.
- 빌드/테스트: `python build.py` / `npm test`(=`node --test`).
- 데이터 수정 시 `data/*.yaml` 편집 후 `python build.py` 재실행.
