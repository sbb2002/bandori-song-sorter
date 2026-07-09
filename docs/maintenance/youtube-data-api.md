# YouTube Data API v3 (Google Cloud Console)

## 역할
YouTube의 공식 REST API. 이 저장소에서 세 갈래로 쓰인다:

| 용도 | 스크립트 | 빈도 |
|---|---|---|
| 밴드 채널 업로드 전체 조회(백필 — RSS의 최근 15개 한계를 넘는 과거 영상 탐색) | `src/tools/collect/backfill.py`, `insert_backfill.py` | 저빈도(수동 실행) |
| 재생불가/지역락 점검 | `src/tools/collect/check_embeddable.py` | 저빈도(수동 실행) |
| 신곡 감지 RSS 실패 시 **폴백**(세션 32 핫픽스, 2026-07-09) | `src/tools/collect/youtube_rss.py`의 `fetch_feed_with_fallback` | CI 매일 크론, 단 **RSS가 정상이면 호출 안 함**(RSS 우선) |

실제 API 호출은 `src/tools/collect/youtube_api.py` 한 곳에 모여 있다(`channels.list` →
업로드 재생목록 id, `playlistItems.list` → 업로드 전체 페이징, `videos.list` → 조회수).

## 필요한 키
`YOUTUBE_API_KEY` — 발급처: [Google Cloud Console](https://console.cloud.google.com/)
→ 프로젝트 선택/생성 → "API 및 서비스" → "라이브러리"에서 **YouTube Data API v3** 사용 설정 →
"사용자 인증 정보"에서 API 키 발급.

**저장 위치 2곳**(따로 관리, 하나 바꿨다고 다른 쪽에 자동 반영 안 됨):
1. 로컬 `.env`의 `YOUTUBE_API_KEY`(gitignore 대상, **장치별로 각자 설정**해야 함 — 새 로컬에서
   작업 시작 시 첫 체크리스트 항목).
2. GitHub Actions 저장소 시크릿(`gh secret list`로 존재 확인, 값 조회는 불가) — 2026-07-09 등록.

## 쿼터
무료 티어 **10,000 units/day**, 태평양 시간(PT) 자정 리셋. `channels.list`·`playlistItems.list`
(50개씩 페이징)·`videos.list`(50개 배치) 전부 **1 unit/call**. 현재 사용 패턴(저빈도 백필 + RSS
정상 시 미사용 폴백)으로는 하루 수십 unit 수준 — 여유 큼.

## 만료주기
API 키 자체는 **기본적으로 만료 없음**(Google이 강제 만료시키지 않음, 수동 삭제/재발급 전까지
영구). 다만:
- Google Cloud 프로젝트가 장기간 완전 미사용이면 정책상 정리 대상이 될 수 있음.
- 키에 HTTP 리퍼러/IP 제한이 안 걸려 있으면 노출 시 오남용 위험 — 주기적 재발급(rotate) 권장,
  특히 저장소가 public이므로 실수로 코드에 커밋하지 않도록 항상 `.env`/시크릿으로만 관리.

## 장애 시 확인
1. 쿼터 초과: HTTP 403 `quotaExceeded` — `youtube_api.py`의 `APIError`로 래핑돼 예외 메시지에
   그대로 노출됨. Cloud Console → "API 및 서비스" → "사용량"에서 확인.
2. 키 자체 문제(삭제/제한 초과): HTTP 400/403 `keyInvalid`류.
3. **엔드포인트 자체 문제가 아니라 RSS(무료·키 불필요 경로) 쪽 문제라면 이 문서가 아니라
   RSS 폴백 설계**(`docs/working/done.md` 세션 32)를 먼저 볼 것 — Data API와 legacy RSS
   (`youtube.com/feeds/videos.xml`)는 서로 다른 엔드포인트로, RSS 장애가 Data API에 영향 주지 않음
   (세션 32의 실제 사례가 이 구분의 근거).
