# RSS→클러스터→반영 자동화 파이프라인 — 설계 spec

> **이 파일 = "신곡 감지 → 음원맵 좌표 산출 → 라이브 반영"을 Actions 크론으로 자동화할 때 볼 유일한 설계 문서.**
> 상태: **DESIGN(미구현)**. 논의 출처 = [../../idea/260702.md](../../idea/260702.md). 전곡 확대(스케일업)는 [audio-map-fullscale.md](audio-map-fullscale.md), 축 설계는 [audio-map-axes.md](audio-map-axes.md) 참조 — 여기는 **자동화 배선**만 다룸.

마지막 갱신: **2026-07-02**

---

## 1. 목표

RSS 신곡 수집 → cluster 분석 → main 반영을 **하나의 크론 파이프라인**으로. handoff 백로그의 **Phase 1.5(build+deploy 자동) + Phase 2(auto-merge)** 를 묶는 것.

- **"API화" ≠ HTTP 백엔드.** 이 레포는 백엔드 서버 없는 정적 사이트(GitHub Pages가 루트 서빙). 크론은 러너에서 **스크립트를 직접 실행**할 뿐. 필요한 건 API 제작이 아니라 **모듈 배선**.
- **`actions/` 오케스트레이터**: 새 폴더에 메인 스크립트를 두고 **기존 파일은 이동하지 않고** 각 기능을 모듈처럼 `import`/호출. 기존 스크립트는 이미 `--propose`/`main(argv)` 등 CLI 엔트리포인트 보유.

---

## 2. 현재 크론 단계 분해 (`rss.yml` → `youtube_rss.py --propose`)

**워크플로우 레이어(rss.yml, 6 step):** 트리거(cron 04:00 KST + `workflow_dispatch`) → checkout(`fetch-depth: 0`) → setup-python → `pip install pyyaml` → git identity → `run: youtube_rss.py --propose`.

**스크립트 레이어(7단계):**

| 단계 | 함수 | 성격 | 하는 일 |
|------|------|------|---------|
| 1 원장 읽기 | `gh_pr_states()` | 조회 | `rss/<id>` PR 상태(=이미 다룬 곡) |
| 2 기존 로드 | `load_existing()` | 순수 | songs/*.yaml → known id/name |
| 3 후보 산출 | `collect_candidates()` | 네트워크·순수 | 밴드별 Topic RSS + 필터 + 길이컷 → candidates/drops/health |
| 4 스테이징 | `open_pr()` | 쓰기 | 곡당 브랜치·yaml 수술삽입·commit·push·`gh pr create` |
| 5 이벤트 로깅 | `append_events()` | 쓰기 | staged/dropped/anomaly → rss_events.jsonl |
| 6 헬스 알람 | `open_health_issue()` | 쓰기 | 파싱 이상 시 gh issue |
| 7 로그 커밋 | `commit_log()` | 쓰기 | rss_events.jsonl만 main에 `[skip ci]` push |

**모듈 경계**: **1–3 = 판단/데이터(부수효과 없음)** / **4–7 = 행동/기록(git·gh 쓰기)**. 오케스트레이터 모듈 경계가 여기 대응. **cluster 모듈의 입력 접점 = 3단계 산출 candidates(band·name·url).**

---

## 3. `actions/` 오케스트레이터 방향

- 얇은 래퍼로 기존 모듈 호출: `collect`(1–3, candidates 리턴) → `cluster`(신곡 좌표 산출) → `stage/push`(4–7 또는 반영).
- 각 스테이지는 **독립 실패 격리**(한 스테이지 실패가 뒤를 안 죽임) — 특히 cluster는 fail-soft(아래 §4).
- 파일 이동 금지(기존 경로 유지). `actions/`는 배선 전용.

---

## 4. 오디오 캐시 마련 전략 (확정 2026-07-02)

**로컬 벌크 + CI 소량 + fail-soft**로 이원화. 오디오는 저작물 → **분석 후 폐기**, 커밋되는 건 파생 수치(좌표)뿐.

- **벌크(전곡, 일회성)**: 로컬(집 IP)에서 yt-dlp 스로틀 수집 → 분석 → 폐기. **CI 봇차단을 원천 회피.** 실행 순서·비용은 [audio-map-fullscale.md](audio-map-fullscale.md).
- **신곡(월 <5곡, 상시)**: Actions에서 감지 곡만 임시 캐시 → 분석 → 폐기. 소량이라 rate 리스크 낮음.
- **fail-soft 필수**: 다운로드 실패 곡은 스킵, 크론은 죽지 않고 다음 실행에서 재시도. RSS의 "seen 원장 없이 매번 재계산(idempotent recompute)" 철학 계승 → 신뢰성을 하드→소프트 요구로 낮춤.

### 다운로드 신뢰성 — 대응 카드 (약→강)
1. **yt-dlp 항상 최신**(대부분 breakage는 며칠 내 커뮤니티 패치로 흡수) — 1순위, 가장 싸다.
2. 재시도/백오프(`--retries`/`--sleep-requests`, 429용) · 클라이언트 로테이션(`player_client`).
3. **버너(일회용) 계정 쿠키**(`--cookies`) — "봇 확인"에 직접적. **본계정 금지**(정지 리스크).
4. PO token / 레지덴셜 프록시(유료·회색지대, 취미 규모엔 과함).
5. 근본 회피: **셀프호스티드 러너(레지덴셜 IP)** 또는 로컬 추출 후 좌표만 커밋.

> **실증**: handoff 백로그에 "CI에선 길이 스크랩 막힘(consent wall)" 기록 = YouTube가 이미 CI IP에서 watch 페이지 차단 중. yt-dlp 오디오도 같은 벽 → **fail-soft가 옳은 판단**.
> **불변**: 자동 다운로드 자체가 YouTube ToS 위반(로컬·CI 동일). 방어선 = 버너로 계정 리스크 격리 + 산출물이 저작물 아닌 파생 수치.

### 구멍(yt-dlp breakage) 알람
별도 알람 시스템으로 대응 예정 → **현 단계 스킵**. (구축 시 RSS 헬스알람 패턴 = 연속 실패 시 `gh issue` 재사용 권장. 맵은 파생 시각화라 breakage=graceful degradation, 심각도 낮음.)

---

## 5. ⭐ 증분 병합 — 폐기 모델을 z-score 좌표와 양립시키기 (핵심)

좌표(`audio_map.json`)는 **모집단 mean/std로 z-score**된 값(`build_perceptual_map.py` `zscale()`). 오디오를 폐기하고도 CI 신곡을 **전체 재다운로드 없이** 얹으려면:

- **전곡 빌드 시 정규화 파라미터를 `audio_map.json`에 저장**: contrast·mode 각각의 **mean·std** + `x_shift`/`y_shift` + `BAND_OVERRIDES`. (현재는 매번 전체 캐시에서 재계산할 뿐 저장 안 함 → **이 저장이 증분의 선결 조건.** fullscale 빌드 시 함께 남길 것.)
- **CI 신곡 경로**: `신곡 오디오 1개 → raw contrast/mode 추출 → 저장된 mean/std로 z변환·shift·override → songs[]에 append`(오디오 즉시 폐기).
- 월 <5곡이면 **재z-score 없이 "동결 스케일 append"** 로 충분 — 기존 좌표를 다시 안 흔듦(신곡 몇 개로 mean/std 재계산해봐야 드리프트 무시 가능).

---

## 6. y_shift/overrides 동결 타이밍

특정 밴드(morfonica 등)는 feature로 지각을 못 잡아 **큐레이션으로만 보정** → 상시 재튜닝 불필요(사용자 판단). 단:

- 97→660 스케일업 시 `zscale`의 mean/std가 새 모집단으로 재계산돼 **전 좌표가 이동** → **"전곡 벌크 빌드 결과를 육안 승인한 직후"에 상수를 확정·동결**하고, 그 다음부터 오디오 폐기.
- 즉 **전곡 빌드 = 마지막 튜닝 순간**. 그 시점에 §5의 정규화 파라미터도 함께 확정·저장.

---

## 7. Phase 매핑 · 트레이드오프

- **Phase 1.5** = songs/*.yaml이 main에 반영되면 `build.py` 자동 실행 → index.html 자동 커밋. **가치 최고·리스크 최저**(API 불필요, 저작권 무관, 게이트 유지). 자동화 착수 시 1순위 권장.
- **Phase 2** = 고신뢰 곡 auto-merge. 현재 RSS는 human-in-the-loop(PR 머지=승인). auto-merge는 **이 게이트를 자동화로 대체하는 트레이드오프** — 오탐이 검수 없이 라이브. precision 축적 후 결정.
- **Phase 3(idea 3번)** = cluster까지 포함해 main push. Phase 1.5/2가 선행.

---

## 8. 미결 · TODO
- [ ] `build_perceptual_map.py`: 정규화 파라미터 `audio_map.json` 저장(§5) — fullscale 빌드와 함께.
- [ ] cluster **증분 append 경로**(신곡 1곡 → 동결 스케일 → append) 구현.
- [ ] `actions/` 오케스트레이터 배선(§2 모듈 경계 기준).
- [ ] CI 신곡 오디오 다운로드 fail-soft + (필요시) 버너 쿠키/셀프호스티드.
- [ ] Phase 2/3 human-in-the-loop 대체 여부 결정.
