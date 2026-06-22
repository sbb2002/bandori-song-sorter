# HANDOFF: bandori-song-sorter — 남은 작업

해야 할 것·남은 것만 담습니다. **완료된 작업 기록은 [done.md](done.md)** 참조.
(참고 사실 — v2 표시 범위, 라이브/원격 URL, 환경 등 — 도 done.md 상단에 정리.)

마지막 갱신: 세션 6 종료 시점 (2026-06-22)

---

## 남은 작업

### 1. 데이터 품질 검수 (사용자 직접 진행 예정)
각 밴드 yaml의 `numbering/album_title: 'undefined'` **더미 앨범**(다른 앨범 곡의 중복본 + `url:` 빈 트랙) + 각 곡 `url`이 **올바른 영상·풀버전(Full-size)** 인지 검수.
- **사용자 방침**: 현재로선 곡을 하나씩 열어 *맞는 곡인지·풀버전인지* 손수 검증할 계획. 검수 자동화/툴은 아이디어 미정이라 고민 중.
- 정리 시 곡 수·중복 변동 → `npm test`로 회귀 확인 필요. `url:` 빈 트랙(앱에서 ♪ 표시·재생 불가) 유지/제거 정책 결정 필요.
- **추천 툴(미구현) `tools/verify_links.py`**: 전 yaml `url`을 **oEmbed(무API키, `youtube.com/oembed`)** 로 점검 → ① 404/401=삭제·비공개(1순위) ② oEmbed가 준 실제 영상 제목 ↔ yaml 곡명 대조(매핑오류 의심) ③ watch 페이지 `lengthSeconds` 스크랩→짧으면 TV Size/Short 의심(=풀버전 판별) ④ 빈 `url`·중복 `video_id` 리스트업. **출력=의심 항목만 표** → 560곡 전수 대신 플래그분만 집중 검수.

### 2. 자동화 — youtube_rss GitHub Actions 크론 (미구현)
`tools/youtube_rss.py`를 GitHub Actions 크론으로 → 신곡을 **검토용 PR**로 올리기.
- **사용자 방침**: Actions 한도 확인 후 문제없으면 **매일 AM 04:00(KST) 1회**. 크론이 뽑은 후보가 *진짜 신곡/풀버전인지* 판별(false positive)이 과제 — 검증 아이디어 필요.
  - 참고: 이 repo는 **public이라 Actions 분 무료·사실상 무제한**(매일 13밴드 RSS는 ~1분). cron은 UTC 기준이라 04:00 KST = `0 19 * * *`. GitHub 스케줄은 정각 보장 안 됨(고부하 시 수십 분 지연).
- 현재 판별(이미 구현): 영상ID(`known_ids`+`rss_seen.json`) · 정규화 곡명(`norm_name`, 괄호·구두점 제거) · `variant_tag`(TV Size/Short/live/instrumental 제외) 3중 + 곡명당 1개 collapse + inbox 검토 게이트.
- **추천(미구현)**:
  - **제시=PR**: Actions가 신곡을 yaml에 append한 단일 브랜치+PR 자동생성 → 사람이 diff·링크·길이 보고 머지/기각. 검증이 PR 리뷰로 흡수(자동 반영 금지).
  - **상태 영속화**: `rss_seen.json`이 현재 `.gitignore` → Actions는 매 실행 깨끗한 체크아웃이라 seen 없음 → 같은 후보 매일 재생성. seen(+사람이 기각한 `ignore` 목록)을 **git 추적으로 전환**해야 "한 번 기각=재제시 안 함" 성립.
  - **풀버전 신뢰도**: youtube_rss에 영상 길이(watch `lengthSeconds`) 추가 → `variant_tag`가 못 거른 짧은 버전을 길이로 2차 필터, 후보 표에 길이 표기. `variant_tag`에 `movie/anime ver·edit·medley` 패턴 보강.
  - ※ 데이터품질 툴과 oEmbed·길이 스크랩 로직 공유 가능 → 공통 유틸로 묶기.
