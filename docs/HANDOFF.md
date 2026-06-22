# HANDOFF: bandori-song-sorter — 남은 작업

해야 할 것·남은 것만 담습니다. **완료된 작업 기록은 [done.md](done.md)** 참조.
(참고 사실 — v2 표시 범위, 라이브/원격 URL, 환경 등 — 도 done.md 상단에 정리.)

마지막 갱신: 세션 6 종료 시점 (2026-06-22)

---

## 남은 작업

### 1. 데이터 품질 (선택 · 사용자 보류 중)
각 밴드 yaml의 `numbering: undefined / album_title: undefined` **더미 앨범** = 다른 앨범 곡의 중복본 + `url:` 빈 트랙. 현재 클라이언트 중복제거(core.js)에 의존.
- 정리 시 곡 수·중복 변동 → `npm test`로 회귀 확인 필요.
- `url:` 빈 트랙(앱에서 ♪ 표시·재생 불가) 유지/제거 정책 결정 필요.

### 2. 자동화 (미구현 · 로컬 우선 결정)
`tools/youtube_rss.py`를 GitHub Actions 크론으로 → 신곡을 검토용 PR로 올리기(검토 후 푸시).
