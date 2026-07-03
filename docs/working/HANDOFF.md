# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`.

마지막 갱신: **2026-07-03** — 작업 2·3 **병렬 실행 계획** 확정 + 오디오 수집기 `fetch_audio.py` 추가(브랜치 `feature/emoi-cluster-v3a`).

---

## 시작 전 체크 (다른 로컬·세션)
> 1. `git pull origin main`(660곡). 작업은 **새 feature 브랜치**에서.
> 2. `.env`의 `YOUTUBE_API_KEY` = **장치별·비커밋**(gitignore) — 백필/지역락 점검 시 재추가(없으면 `insert_backfill.py`·`check_embeddable.py` 즉시 중단).
> 3. `npm test`(=`node --test`)용 **node 설치 확인**(직전 장치엔 없어 미실행).
> 4. 가사 원문 `assets/lyrics/<band>.md` = 로컬 전용(gitignore). 커밋된 `wordcloud/<band>.yaml`로 검수·렌더는 가능하나 `build_keywords.py` **재생성은 원문 .md 필요**.
> 5. 로컬 브랜치(2026-06-30 정리): `main` + 백업 3(`backup/main-20260620·22·30`) + `feature/ux-02-opt-a`(옵션A 유일본, 미머지·원격없음 — 삭제 금지).

---

## 현황
- 데이터 **677 트랙 / 화면 660곡(dedup) / 13밴드**. 워드클라우드 **라이브**, 백필(1-a/1-b)·지역락 처리 완료(done 14~20, 화면 526→660). 
- **다음 본류 = 음원맵 전곡 확대**(작업 2). 클러스터 v2+v3는 미머지 브랜치 `feature/emoi-cluster-v2`.

## 우선순위
| 작업 | 상태 | 상세 |
|------|------|------|
| 1. 워드클라우드 | ✅ 완료 — (D) 배치만 | § 작업 1 · 열린 결정 |
| 2. 음원맵 전곡 확대 | 🔜 **본류** | → [spec/audio-map-fullscale.md](spec/audio-map-fullscale.md) |
| 3. 자동화 파이프라인 | 🔜 후속(2 이후) | → [spec/pipeline-automation.md](spec/pipeline-automation.md) |
| 보류 · 백로그 | 후순위 | § 보류·백로그 |

원칙: **밴드 시각화 마무리 → 후속 확장.** 보류·백로그는 별도 결정 사안.

---

## 병렬 실행 계획 (작업 2·3 — 2026-07-03 확정, 이 순서로 진행)

> 오늘 작업 브랜치 = **`feature/emoi-cluster-v3a`**. 크리티컬 패스는 하나뿐: **범위 → 오디오 수집 → 전곡 빌드·동결 → 증분 append.** 나머지는 오디오 무관 → **오디오 수집 대기시간(로컬 ~30~90분 무인)에 병렬**로 굴린다.
>
> **⏸ 중단 시 재개(다른 로컬·세션)**: 각 페이즈/트랙은 독립 커밋 → `git push` 하면 다른 로컬이 이어받는다. **단 오디오 wav 캐시는 gitignore = 장치 전용** — 다른 로컬로 옮겨도 wav 는 안 따라온다(현재 이 장치엔 wav 0개). 다운로드를 다른 로컬에서 이어가면 그 장치 기준으로 재수집하되, `fetch_audio.py` 의 **skip-existing 으로 장치 내 재개는 보장**(끊겨도 같은 명령 재실행 = 남은 곡만).

**Phase 0 — 결정 + 빌드 준비 (동시)**
- **[사용자 게이트]** ① 범위(660 / 캡 N~300 / 97 유지 — fullscale §1) = 오디오 물량 확정 · ② 레이아웃 묶음(아래 **열린 결정**) = 2.5 최종·작업1(D) 확정.
- **[A·코드]** `build_perceptual_map.py`에 `--manifest` 인자 + 매니페스트 생성(`songs/*.yaml`→`band,idx,song,url`, dedup=vid, 캡N) + **정규화 파라미터 저장(contrast·mode의 mean/std + shift + overrides, pipeline §5)**. 셋 다 audio 없이 현행으로 스모크 가능. ⚠️ 이 저장 코드가 **다운로드 착수 전에** 들어가 있어야 전곡 빌드가 파라미터를 남긴다(안 남기면 나중에 전곡 재수집).

**Phase 1 — 대기시간 병렬 (핵심 구간)**
- **[A]** **오디오 수집 착수**: `python src/tools/cluster/build_manifest.py`(→ `songs_full.csv` 660곡, 생성 완료) → `python src/tools/cluster/fetch_audio.py --cache audio_full`. 재개 가능·fail-soft·10%마다 진행률/예상종료·일시중지(429 재시도소진 / 17시+ETA≥5h). 안티봇 5원칙 = `docs/idea/260703.md`. ← 도는 동안 ↓ 병렬.
  > 🟡 **현재 상태(2026-07-03 오전) = 도구 준비 완료·미착수.** 착수 선결: ① `pip install yt-dlp imageio-ffmpeg`(이 장치 conda base 미설치) · ② 쿠키 방식 결정(**권장 `--no-cookies`** — 본계정 쿠키는 pipeline §4 '본계정 금지' 정지 리스크, 봇월 감지 시 버너로 승격) · ③ 실행. 660곡 ≈ 곡간 30–60s 대기 지배로 **~10–13h** → 17시 조건2)로 중간 일시중지 후 다른 로컬 이어받기 예상. 진행상태 = `src/content/cluster/fetch_progress.json`.
- **[B]** 렌더 최적화(ECharts `large`/`largeThreshold`/`progressive` + 줌/팬 + ALL z-order) + UX(센트로이드 클릭 비활성 + opacity 0.3). `static/js/script.js`만 → 리빌드 불필요. 현행 97곡/목업으로 개발.
- **[C]** 구 파일 폐기(`keywords_2d.json`·`build_embeddings.py`·`build_audio_map.py` + untracked `rss_seen/inbox/verify_cache`) + `actions/` 오케스트레이터 골격(collect[1–3]→cluster[**stub**]→stage[4–7]) + Phase 1.5 워크플로우.

**Phase 2 — 합류 (오디오 완료 후, 직렬)**
- **[A]** 전곡 빌드 `build_perceptual_map.py --cache audio_full` → `audio_map.json` + **파라미터 동결·저장**. `BAND_OVERRIDES`(morfonica)·`y_shift` 육안 재점검 → **여기서 상수 확정·동결**(= 마지막 튜닝 순간, fullscale §4 · pipeline §6) → 이후 오디오 폐기. `python src/build.py`.

**Phase 3 — 통합**
- B(렌더) ↔ A(전곡 `audio_map.json`) 머지 → 브라우저 실검수(`http.server` · 모바일 320px).
- C의 cluster stub → **동결 파라미터 기반 증분 append** 완성(pipeline §5).
- 레이아웃 결정 반영(작업 1-D + 음원맵 게시).
- 머지 경로: `feature/emoi-cluster-v2` → `feature/emoi-cluster` → `main`.

**트랙 충돌면**: A=`build_perceptual_map.py`+`audio_map.json` / B=`script.js` / C=신규·삭제 → 거의 무충돌. 공유물 `audio_map.json`(A 재생성, B 읽음)은 Phase 3에서 B를 A 결과 위로 정리.

---

## 작업 1. 워드클라우드 — (D) 배치만 남음
품질(2-c A·B·C + 키워드 색상) **완료**(done 20). 재생성 명령·큐레이션 주의(`weight:0`은 렌더 `||1`로 부활 → 제거는 yaml 줄 삭제 / `ko`는 재생성 시 덮어써짐)는 memory `wordcloud_quality_plan.md`·done 17·20.
- **남은 것 = (D) 배치 재결정** → 클러스터 게시 위치와 함께 결정 (아래 **열린 결정**).

## 작업 2. 음원맵 전곡 확대 [본류]
**채택 축**: x = spectral contrast(거칢↔매끄러움, r−0.81) · y = mode(밝음↔어두움, r+0.51). 파이프라인 `build_perceptual_map.py` → `audio_map.json` → `script.js _clDraw`. 현재 TOP10×10 97곡 라이브. v2·v3 완료(done 21).
- ⚠️ **구현 시 [spec/audio-map-fullscale.md](spec/audio-map-fullscale.md) 필독** — 범위(전체660/캡N/유지)·매니페스트+`--manifest`·yt-dlp→`audio_full`·수백 점 렌더 최적화·비용·불균형까지 정리됨.
- 축 설계 근거 = [spec/audio-map-axes.md](spec/audio-map-axes.md) + `report/cluster-correlation/README.md`.
- ⭐ 전곡 빌드 시 **정규화 파라미터(contrast·mode의 mean·std + shift + overrides)를 `audio_map.json`에 저장** — 자동화 증분의 선결(fullscale §4 / pipeline-automation §5). 오디오는 폐기되므로 지금 안 남기면 나중에 전곡 재수집.

### 2-잔여 (확대와 병행 가능, 우선순위 낮음)
- **브라우저 실검수**: `python -m http.server` → 유튜브 하단 음원맵 · 모바일(320px). (node 미설치로 미확인)
- **머지 경로**: `feature/emoi-cluster-v2` → `feature/emoi-cluster` → `main`(라이브 sbb2002.github.io).
- **UX**: 센트로이드는 **클릭 비활성화 + 반투명(opacity 0.3)** — 근접 데이터포인트 클릭난 해소(UX 평가 지적).
- (선택) 구 미사용 폐기: `keywords_2d.json` · `build_embeddings.py` · `build_audio_map.py`.

## 작업 3. 자동화 파이프라인 (RSS → cluster → main 반영)
RSS 수집 → cluster 분석 → 라이브 반영을 `actions/` 오케스트레이터 크론으로. **설계 = [spec/pipeline-automation.md](spec/pipeline-automation.md)** (착수 전 필독).
- 백로그의 **Phase 1.5(build+deploy 자동) + Phase 2(auto-merge)** 통합. Phase 1.5 = 가치·리스크 최선 → 1순위. 상세 done 13.
- **작업 2에 의존**: 전곡 빌드 + 정규화 파라미터 저장(§5)이 증분 반영의 선결.
- 오디오 = 로컬 벌크 + CI 소량 + fail-soft. CI는 이미 consent-wall로 length 스크랩 차단됨(`length_s=null`) = 다운로드 신뢰성 리스크 실증.
- (정리) 옛 프로토타입 untracked 잔재 `rss_seen.json`·`rss_inbox.csv`·`verify_cache.json` 삭제 가능.

---

## 열린 결정 (사용자)
- **(레이아웃 — 묶어서 결정)** 워드클라우드 배치(1-D) + 음원맵 게시 위치 + 분할 비율(yt:음원맵). 우패널 탭이 좁아 워드클라우드 부적합 → 후보: 유튜브 프레임 가로 2분할(아래=클라우드) / 전용 모달 / 하단 넓은 영역. 전곡 음원맵도 넓은 영역 필요(fullscale §5) → **셋을 함께 결정.**
- **(기능)** 진행률 링 70% 하드게이트: 현재 70% Green은 링 색상일 뿐, "70%↑만 최애밴드 자격" 게이트 미도입(현재는 스코어링 수축 `w(n)`만). 도입 여부 별도 결정(ux-02.md #2).

## 보류 · 백로그
- **(보류) 백필 1-c namedup 403**: 기존 곡 url을 Topic 음원으로 교체(품질 개선, 새 곡 아님). 후순위. (1-b 커버 135곡은 완료 — done 18.)
- **(보류) 진행도 Save/Load** (ux-02.md #4): 진행 json 백업/공유. ⚠️ Load = 기존 진행 덮어쓰기 → 손실 위험, 자동 백업·복구 경로 선설계 필수. 코멘트(`bandori-song-comments-v1`) 직렬화 포함 여부 확정 필요.
- **(백로그) 재생 이퀄라이저 애니메이션** — 후순위. 제약(실시간 실제소리·LFS 불가)·방안(A+ 절차생성 권장 / B lazy 사전계산) 상세 = [spec/equalizer-animation.md](spec/equalizer-animation.md).

---

## 참고 (TODO 아님)

### ⏪ 롤백 지점
`backup/main-20260630-emoicloud`(local·origin) = emoi-cloud(워드클라우드 색·품질) 머지 **직전 main = `cebbce4`**. 문제 시 `git reset --hard cebbce4`(+force-push) 또는 `git revert -m 1 961ab93 && git push origin main`(라이브 안전·권장). 이전 백업 `backup/main-20260630` = `d586ffb`(1-b 커버 머지 직전).

### 지역락 — 정책 확립 (done 15·16, 절차만 재사용)
- **감지**: `check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `new_songs.csv` 대상 동일 로직.
- **정책(2026-06-29)**: 지역락 = 앱 데이터(`songs/*.yaml`)에서 삭제, 곡 정보는 `invalid_url.csv` 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **parked 4곡**(끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 대체 음원 재등록 완료 — done 19.) 워크시트 `region_blocked.csv`, 대체 URL은 **제목 대조 검증 필수**(세션 19 오입력 1건 적발).
