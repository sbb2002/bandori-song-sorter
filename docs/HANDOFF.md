# HANDOFF: bandori-song-sorter — 남은 작업

해야 할 것·남은 것만 담습니다. **완료된 작업 기록은 [done.md](done.md)** 참조.
(참고 사실 — v2 표시 범위, 라이브/원격 URL, 환경 등 — 도 done.md 상단에 정리.)

마지막 갱신: #1 youtube_rss 자동화 **설계 확정**(곡당 PR·멱등 재계산·로깅·포맷감시) — Phase 1 착수 대기, 브랜치 `feature/youtube-rss-autoloader` (2026-06-24)

> **ux-02.md 1·2·3·6·7번 완료**: 1·2(히트맵 셀렉터순 / 최애 스코어링) 세션 8·9, **7(재생 중 곡 강조) 세션 10**, **6(밴드 셀렉터 진행률 링) 세션 11**(SVG stroke 채택, conic은 `feature/ux-02-ring-conic` 백업), **3(티어 팝업 코멘트 + 링크복사 동반) 세션 12**(코멘트는 별도 키 `bandori-song-comments-v1`). 상세는 [done.md](done.md). 옵션 A(랭크순)는 `feature/ux-02-opt-a` 백업.
> 아래는 남은 4건을 **구현 난이도 낮고 기존 기능을 덜 해치는 순**으로 유지.

---

## 작업 순서 (쉽고 안전 → 어렵고 위험)

| 순 | 작업 | 난이도 | 기존기능 리스크 |
|----|------|--------|-----------------|
| 1 | youtube_rss 자동화 | 중 | 낮음(앱 런타임과 분리) |
| 2 | 데이터 품질 검수 | 중(수작업) | 중(곡 데이터 변경→회귀) |
| 3 | 진행도 Save/Load | 중~높 | 높음(진행 덮어쓰기→손실) |
| 4 | 한국 지역락 대응 | 높(불확실) | 중(감지·대체 미정) |

원칙: **앱과 분리된 인프라(1) → 곡 데이터 변경(2) → 저장 덮어쓰기(3) → 방안 불확실(4).**

---

> ⚠️ **진행률 링(완료, 세션 11)에서 보류된 열린 결정**: 70% Green은 **링 색상일 뿐**이고, "70% 이상만 최애밴드 표시 자격" **하드게이트는 미도입**. 현 최애밴드는 스코어링 수축(`w(n)`)으로만 선정. 게이트 도입 여부는 별도 결정 사안으로 남김(ux-02.md #2 "최애밴드 표시 자격 조건"과 연결).

### 1. 자동화 — youtube_rss GitHub Actions (설계 확정 · Phase 1 착수 대기) — 난이도 중 · 리스크 낮음
`tools/youtube_rss.py`(프로토타입 존재)를 Actions 크론으로 → 신곡을 **곡당 PR**로 올림. 앱 런타임과 분리돼 기존 기능 무영향. 작업 브랜치 **`feature/youtube-rss-autoloader`**.

**스케줄/실행**: `schedule: '0 19 * * *'`(UTC = 04:00 KST · 정각 보장 X·지연 무관) + `workflow_dispatch`(수동 재실행 버튼). public repo라 Actions 분 사실상 무제한(13밴드 RSS ~1분).

**핵심 설계 — 멱등 재계산 (seen 영속화 폐기)**
- 후보 = 13밴드 Topic RSS − `known_ids`(data/*.yaml에서 매 실행 추출) − closed-unmerged PR(=거절분).
- 머지된 곡은 yaml에 들어가 `known_ids`가 자동 제외. ⇒ `rss_seen.json` **불필요(폐기, `.gitignore`에서도 제거)**, `ignore` 파일도 **불필요**.

**곡당 PR + GitHub 상태 = 원장** (사람 동선 최소화)
- **1곡 = 1 PR**, 브랜치 `rss/<video_id>`.
- **승인(TP)** = PR 머지 → yaml 반영, 이후 `known_ids`가 제외.
- **거절(FP)** = PR **닫기, 끝**. 봇이 매 실행 시 video_id로 closed-unmerged PR 조회 → 재제시 안 함. (별도 명령·파일 X.)
- **편집** = GitHub에서 PR 직접 수정 후 머지(선택). 봇의 앨범 배치 오류는 **앱 무해**(표시 그룹만 다름) → 정확한 재분류는 #2로 미뤄도 됨 ⇒ 대부분 "그냥 머지".

**yaml append (회귀 차단)**
- **전체 재직렬화 금지**(560곡 재포맷·따옴표/멀티라인 손상 위험). **외과적 텍스트 삽입**: 대상 앨범 블록 탐색 → 그 `tracks:` 끝에 4-space track 블록만 삽입. 비커버→`numbering:'Single'`, 커버→`numbering:'Cover'`, 없으면 새 앨범 블록 추가. ⇒ diff = 추가 줄만.
- track 형식: `track_number`=발매일, `name`=피드 제목, `url`=`https://youtu.be/<id>`.

**2-게이트 구조 (data ≠ 라이브)**
- `index.html`은 git 커밋된 정적 파일(Pages가 서빙). data 변경은 **`python build.py` → index.html 커밋**해야 라이브 반영.
- 게이트1 = PR 머지(data), 게이트2 = build+commit(라이브). FP는 두 관문을 다 통과해야 앱 도달.
- **Phase 1.5(옵션)**: main에 data 머지 시 build+deploy 자동 워크플로 → 수동 build 잡일 제거(개발 안정화 후 도입).

**auto-merge 전환 정책 — 수동 게이트로 시작하는 이유 (중요)**
- ⚠️ **auto-merge로 시작하면 안 됨**: 모든 후보가 머지되어 **FP가 한 번도 관측 안 됨** → precision이 항상 100%로 보여 **측정 자체가 불가(self-defeating)**. **사람의 머지/거절이 곧 TP/FP 라벨링** = precision 데이터 수집 기구. auto-merge로 모은 로그로는 auto-merge 가부를 판단할 수 없음.
- 신곡 ≈ **50곡/년 ≈ 주 1클릭**. 연속 **무-FP 30건(소프트 ON)~50건(안심)** 누적 후 → **고신뢰 티어**(`variant==""` + 길이 정상범위 + 임계 비근접)만 auto-merge 전환. 모니터링 유지·FP 뜨면 즉시 OFF·가역 전제.
- 근거(Rule of Three): 무-FP n건 → FP율 95% 상한 ≈ 3/n. 30→~10%, 50→~6%, 100→~3%, 300→~1%(과함·수년 소요). N=20(~15%)이 현실 바닥.
- 🔁 **자동-우선 탈출구(사용자 결정)**: gate-first는 *측정을 위한* 권장안일 뿐 강제 아님. **PR 요구가 과해 번거로우면 언제든 자동-우선(Actions가 main에 직접 push)으로 전환 가능** — 단 그 순간부터 precision 측정은 중단됨을 감수. 사용자 예상상 **FN은 거의 발생 안 함** → deferred FN 툴 우선순위 낮음.

**로깅/모니터링 (tools/ 전용, git 추적 · 앱 미포함)**
- `tools/rss_events.jsonl`(append-only): 매 실행 모든 RSS 아이템 판정 = `{ts, band, video_id, title, published, length_s, decision: staged|dropped, drop_reason, pr}`.
- `--report`: PR 상태(`gh pr list`)와 join → **precision = TP/(TP+FP)**, 태그 카운트, 사유별 drop, feed health 요약. = 사용자 대시보드.
- 태그: **TP**=staged→merged, **FP**=staged→closed, **TN**=dropped(곡 아님/기존/변종), **FN**=**자동 검출 불가**(봇이 신곡인 줄 알았으면 안 버림) → 사후 감사 대상. recall은 측정 불가.
- `--audit`: 휴리스틱 drop(`variant`·`length_short`)만 출력 → **FN이 숨는 곳** 주기 점검(known_id/known_name drop은 FN 아님·안전).
- **[deferred] FN 수동 등록+로깅 툴(`--add` 류) = 나중 별도 논의.** FN은 사용자 불편으로 즉시 체감 → 곡 수동 추가 + 그 사건을 FN으로 로그에 남겨 통계 정직성 유지. 희박하나 대비 툴 필요(Phase 1 범위 밖).

**정밀도(FP↓) — 길이필터 Phase 1 포함**
- watch 페이지 `lengthSeconds` 스크랩 → `variant_tag`가 못 거른 짧은 버전을 길이로 2차 컷 + PR 표에 길이 표기.
- `variant_tag` 패턴 보강: `movie/anime ver·edit·medley·remix·nightcore`.
- Topic 채널은 Art Track(곡)만 → FP 주 원천은 "길이 줄인 버전" 하나 → 길이필터가 직격. (#2 데이터품질과 길이/oEmbed 로직 공유.)

**포맷 변경 감시 (파싱 레이어만 · 오탐 억제)**
- **레이어 분리**: 알람은 *파싱 레이어*(fetch 실패 / XML 예외 / 유효 videoId+title entry **0개**)만. *스테이징 레이어*(entry는 정상인데 변종·기존곡 필터로 **신곡 0개**)는 **정상 = 알람 X**. (이 혼동이 가짜 알람의 원인이었음.)
- **하드 알람**(이슈 자동생성, 동일 이슈 열려있으면 재생성 X): **여러 밴드가 동시에** 파싱 0건 = 전역 포맷 변경 신호.
- **소프트 로그**: 단일 밴드만 0/실패(채널 개명·삭제 가능) → 2회 연속 지속 시 하드로 승격.
- **fetch 실패**: 일시적 503/타임아웃 흡수 위해 **연속 retry > 3회**일 때만 알람.
- 🔔 **유지보수자/다른 세션 주의 — 포맷 변경 대응 절차**: 사용자가 이 알람/이슈를 목격하면 → **진상파악(피드 원문 ↔ 파서 비교) → 파서 수정 → 사용자가 Actions "Run workflow"(`workflow_dispatch`)로 수동 재실행.** 복구 경로 = 파서 패치 후 수동 트리거.

**워크플로 구현 메모**
- 3rd-party 액션 없이 러너 기본 **`gh` CLI**(공급망 표면 최소화). 권한 `contents:write`·`pull-requests:write`·`issues:write`(기본 `GITHUB_TOKEN`).
- 의존성: stdlib + `pip install pyyaml` 1개.
- 검증: Python 테스트 관례 없음 → `--dry`로 로컬 확인 + 변경 후 `python build.py`·`npm test`(JS 27건) 회귀 확인.

**Phase 구성**: **Phase 1**(곡당 PR + 길이필터 + 로깅 `--report`/`--audit` + 포맷 health/이슈) → **Phase 1.5**(build+deploy 자동) → **Phase 2**(precision 실측 후 고신뢰 auto-merge). FN 수동툴 = deferred.

### 2. 데이터 품질 검수 (사용자 직접 진행 예정) — 난이도 중(수작업) · 리스크 중(회귀)
각 밴드 yaml의 `numbering/album_title: 'undefined'` **더미 앨범**(다른 앨범 곡의 중복본 + `url:` 빈 트랙) + 각 곡 `url`이 **올바른 영상·풀버전(Full-size)** 인지 검수.
- **사용자 방침**: 현재로선 곡을 하나씩 열어 *맞는 곡인지·풀버전인지* 손수 검증할 계획. 검수 자동화/툴은 아이디어 미정이라 고민 중.
- 정리 시 곡 수·중복 변동 → `npm test`로 회귀 확인 필요. `url:` 빈 트랙(앱에서 ♪ 표시·재생 불가) 유지/제거 정책 결정 필요.
- **추천 툴(미구현) `tools/verify_links.py`**: 전 yaml `url`을 **oEmbed(무API키, `youtube.com/oembed`)** 로 점검 → ① 404/401=삭제·비공개(1순위) ② oEmbed가 준 실제 영상 제목 ↔ yaml 곡명 대조(매핑오류 의심) ③ watch 페이지 `lengthSeconds` 스크랩→짧으면 TV Size/Short 의심(=풀버전 판별) ④ 빈 `url`·중복 `video_id` 리스트업. **출력=의심 항목만 표** → 560곡 전수 대신 플래그분만 집중 검수.

### 3. 진행도 Save/Load (ux-02.md #4) — 난이도 중~높 · 리스크 높음 · 후순위
내 진행상황을 **json으로 백업/공유**. Load 시 즉시 로딩 아니라 **Mine/Others 선택**(Mine=내 것 즉시 로드, Others=타인 것 로드 대화창). 내 진행은 항상 백업. 공유는 디씨 등 커뮤니티 첨부 상정.
- ⚠️ **Load = 기존 진행 덮어쓰기 → 데이터 손실 위험**. 로드 전 현재 진행 자동 백업·복구 경로 선설계 필수.
- **후순위**: 디씨 json 첨부가 금기/헤비하면 이 기능 반려 가능. 구현성·안정성·커뮤니티 배포가능성 선검토 필요. (코멘트는 세션 12에서 별도 키 `bandori-song-comments-v1`로 구현됨 → Save/Load 직렬화 범위에 `ranks`와 함께 코멘트를 포함할지 확정 필요.)

### 4. 한국 지역락 노래 대응 (ux-02.md #5) — 난이도 높(불확실) · 리스크 중
일부 곡이 한국 지역락일 수 있음 → 대응책 필요.
- 미정 영역: 지역락 **감지 방법**(클라이언트에서 판별 난해), **대체 링크/표기** 정책. 방안 구상부터 필요. #2 데이터 품질 검수와 oEmbed 점검 로직 일부 공유 가능.
