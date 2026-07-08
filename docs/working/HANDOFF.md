# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`. 작성 규칙은 [readme.md](readme.md).

마지막 갱신: **2026-07-08(세션 31)** — **작업 1·2·3·5 done 이관·HANDOFF 슬림화 + EMOI-MAP minor fix**: 네 작업 본류 완료 확인 → 작업 절을 요약+링크로 축약(선택 잔여는 § 보류·백로그로 이동, 구 '병렬 실행 계획' 제거). **+minor fix(fix/emoi-map-labels-pulse)**: 축 라벨 '음색이 거친/부드러운'·'발랄한/진지한 느낌', 재생 HUD를 밴드 평균점 대비 편차 기준으로, 펄스 16분 주석 비활성(CL_DYN_MAX=1 유지) + research 작성 규칙(README 양식·승격기준). done 31 참조.
이전: **2026-07-07(세션 30)** — 작업 5(EMOI-MAP 좌표계 고찰) 완료·main 머지(`172684e` · done 30): Phase A(맵 정직화) 라이브 + B0·C 정서축 연구 = **timbre×valence 확정, arousal 독립축 불가**("실질 1.x차원"). 결정: x=timbre·y=valence 유지. 논문 [emotion-axes-extraction.md](../research/emotion-axes-extraction.md).
이전: **2026-07-07(세션 29)** — 작업 4(EMOI-MAP 딥스페이스/별 시각화) 완료·main 머지(`104e709` · done 29): 곡 에너지 글로우 별 + canvas 별밭 + 밴드 성운 + Ave Mujica 전용 색.
이전: (세션 28) 작업 3 반자동 파이프라인 운영화·라이브(done 28): 5분 폴러 폐지→단일 23:00 크론 통합 + `src/tools/semiauto-loader/` 통합 + run_local 결과 Telegram 통지.
이전: (2026-07-06 세션 26~27) 작업 3 인프라 구축 + CI 다운로드 봇월 확정(E2E 3회) → 반자동(다운로드만 로컬 IP) 전환. done 26~27.
이전: (2026-07-05 세션 25) 음원맵 클러스터링/재생펄스 완결·main 머지: 660곡 좌표·펄스 + lazy-fetch + 동적 subdivision + 볼륨 프리셋. done 24~25 · [report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md).

---

## 시작 전 체크 (다른 로컬·세션)
> 1. `git pull origin main`(660곡). 작업은 **feature 브랜치**에서(작업 5 = `feature/emoi-map-starfield`).
> 2. `.env`의 `YOUTUBE_API_KEY` = **장치별·비커밋**(gitignore) — 백필/지역락 점검 시 재추가(없으면 `insert_backfill.py`·`check_embeddable.py` 즉시 중단).
> 3. **node 필수**(yt-dlp nsig 서명해독 → 없으면 오디오 수집 403 다발 · `node --check` · `npm test`). 설치 = `conda install -c conda-forge nodejs`.
> 4. 가사 원문 `assets/lyrics/<band>.md` = 로컬 전용(gitignore). 커밋된 `wordcloud/<band>.yaml`로 검수·렌더는 가능하나 `build_keywords.py` **재생성은 원문 .md 필요**.
> 5. 로컬 브랜치(2026-06-30 정리): `main` + 백업 3(`backup/main-20260620·22·30`) + `feature/ux-02-opt-a`(옵션A 유일본, 미머지·원격없음 — 삭제 금지).

---

## 현황
- **레이아웃 확정 + 정적파일 분할 완료**(done 22, main 반영): 편집 시 CSS=`common/desktop/mobile.css`·JS=`static/js/functions/01~19-*.js` **분할 파일 직접 수정**(참조식 → 리빌드 불필요), 템플릿 변경만 `python src/build.py`.
- **밴드 시각화 본류 = 일단락**(작업 1·2·3·4·5 완료). 남은 것은 전부 선택·백로그(§ 보류·백로그).

## 우선순위
| 작업 | 상태 | 상세 |
|------|------|------|
| 1. 워드클라우드 | ✅ **완전 완료**(품질+배치 D · done 20·22) | § 작업 1 |
| 2. 음원맵 전곡 확대 | ✅ **완결·동결**(659곡·norm · done 23) | § 작업 2 |
| 3. 자동화 파이프라인 | ✅ **반자동 운영화 완료·라이브**(done 26·27·28) | § 작업 3 · [spec](spec/pipeline-automation.md) |
| 4. EMOI-MAP 딥스페이스/별 시각화 | ✅ **완료·main 머지**(104e709 · done 29) | [done 29](done.md) |
| 5. EMOI-MAP 좌표계 고찰 | ✅ **A·B0·C 완료**(172684e · done 30) — timbre×valence 확정 | § 작업 5 · [논문](../research/emotion-axes-extraction.md) |
| 보류 · 백로그 | 후순위 | § 보류·백로그 |

원칙: **밴드 시각화 마무리 → 후속 확장.** 보류·백로그는 별도 결정 사안.

> 작업 2·3의 **과거 실행 상세**(오디오 수집 659/660·전곡 빌드·`norm` 동결·반자동 배선·CI 봇월 실증)는 done 23·26·27·28에 있음. (구 '병렬 실행 계획' 블록은 완료되어 제거.)

---

## 작업 1. 워드클라우드 — ✅ 완전 완료 (done 20·22)
품질(2-c A·B·C + 키워드 색상) + (D) 배치(음원맵 슬롯 세로 분할 좌=음원맵/우=워드클라우드, 대안 B, 상시 렌더). **잔여 없음.** 재생성 명령·큐레이션 주의(`weight:0`은 렌더 `||1`로 부활 → 제거는 yaml 줄 삭제 / `ko`는 재생성 시 덮어써짐)는 memory `wordcloud_quality_plan.md`·done 17·20.

## 작업 2. 음원맵 전곡 확대 — ✅ 완결·동결 (done 23)
**채택 축**: x=contrast(거칢↔매끄러움 r−0.81) · y=mode(밝음↔어두움 r+0.51). 전곡 659곡/13밴드 빌드·동결·main 머지 완료(+ `norm` 파라미터). 렌더 = `16-audiomap.js _clDraw`(+HUD·펄스). 근거·상세 = fullscale §4·§6 · pipeline §5 · [spec/audio-map-axes.md](spec/audio-map-axes.md).
- **잔여(선택 → § 보류·백로그)**: 구 미사용 폐기(`keywords_2d.json`·`build_embeddings.py`·`build_audio_map.py`) · DRM `roselia 競宴Red×Violet` 1곡(작업 3 증분 대상).

## 작업 3. 자동화 파이프라인 — 신곡 로더 — ✅ 반자동 운영화 완료·라이브 (done 26·27·28)
**상세 구현·배선·CI 봇월 실증 = done 26·27·28.** 설계 = [spec/pipeline-automation.md](spec/pipeline-automation.md).
- **결론(2026-07-06 실증)**: CI(데이터센터 IP) YouTube 다운로드는 봇월로 불가(클라이언트 로테이션·PO토큰까지 소진, 벽은 IP 평판). 다운로드 이후(demucs·pulse·좌표·커밋·배포)는 네트워크 게이트 없음 → **다운로드만 집 IP로 빼는 반자동** 채택.
- **아키텍처(라이브)**: (Actions 매일 23:00 KST 단일 크론) Telegram 명령 처리 → 감지 → 결과 Telegram 1건. (Local) `run_local.py` 원커맨드 = 전용 클론에서 다운로드→분석→좌표 append→push→`deploy.yml` 자동 배포 + 결과 Telegram. 명령 봇 `/help`·`/status`·`/pause`·`/resume`(`pipeline.yml` 크론 맨 앞에서 처리). 코드 전부 `src/tools/semiauto-loader/`.
- 로컬 사용: `python src/tools/semiauto-loader/run_local.py` (`--dry` 검증 / `--test-band X --test-video Y` E2E 1곡). 사전조건·상세 = 폴더 README.
- **잔여(선택 → § 보류·백로그)**: **분석-only 로컬 스크립트**(사용자 요청·미구현 — 다운로드/분석 역할 분리) · DRM 1곡 수동 · 영구실패 재시도 상한 가드 · index.html `git rm --cached` · 옛 프로토타입 잔재 삭제.

## 작업 5. EMOI-MAP 좌표계 고찰 — ✅ Phase A·B0·C 완료 (done 30 · timbre×valence 확정, arousal 독립축 불가)
정서축(Russell/Thayer V-A) 관점 재해석·검증. **결정: x=timbre(contrast)·y=valence(mode) 유지, arousal 새 축 도입 안 함**("실질 1.x차원": contrast가 rough·energy·tempo·valence 4라벨 지배, 측정 템포≠지각 템포 r=0.087). Millsage·Ikka n=1은 Phase A override가 최종.
- **상세 = done 30**(Phase A 맵 정직화 라이브 · B0 onset 스크리닝 전멸 · C 정식 오디오 18feature 검증). 방법·수치 논문 = [emotion-axes-extraction.md](../research/emotion-axes-extraction.md). 데이터 = report/[cluster-energy-axis](report/cluster-energy-axis/README.md)(B0 660)·[emotion-axes](report/emotion-axes/)(C 30).
- **데이터 보관(사용자 요청)**: onset_features.csv(660)·phasec_features.csv(30) 커밋 보존 · `audio_full`(660·15GB) 로컬 보존(gitignore).
- **잔여(모두 optional → § 보류·백로그)**: 전곡 660 정식 feature 부기(~46분) · 라벨 확대 재검 · 장르 밖 대조군. Phase B(y 토글)는 arousal 부재라 불요.
- 편집 규칙: `16-audiomap.js`·`desktop.css` 직접수정(리빌드 ✗) · `audio_map.json` 변경만 `python src/build.py`.

---

## 열린 결정 (사용자)
- ✅ ~~(레이아웃 — 묶어서 결정)~~ **해소(done 22)**: 유튜브 컬럼 하단 슬롯을 세로 분할 → **좌=음원맵 / 우=워드클라우드(대안 B)** + 유튜브 16:9 + 우패널 히스토그램·히트맵 동시표시 + 곡리스트 30%↓·긴곡명 마퀴 + 모바일 세로 스택.
- **(기능)** 진행률 링 70% 하드게이트: 현재 70% Green은 링 색상일 뿐, "70%↑만 최애밴드 자격" 게이트 미도입(현재는 스코어링 수축 `w(n)`만). 도입 여부 별도 결정(ux-02.md #2).

## 보류 · 백로그
- **(작업 3 — 사용자 요청·미구현) 분석-only 로컬 스크립트**: 다운로드는 다른 로컬/수단으로 받고 분석~push만 하는 별도 파일. 일부 로컬은 분석 라이브러리(torch/demucs 등) 구동 불가 → 다운로드/분석 역할 분리 필요. **현재 `run_local.py`(다운로드+분석 일체형)는 유지**하고 추가.
- **(작업 3) 기타 정리**: DRM `roselia 競宴Red×Violet` 수동 · 영구실패 재시도 상한 가드 · index.html `git rm --cached`(Option A 완전화) · 옛 프로토타입 잔재(`rss_seen.json`·`rss_inbox.csv`·`verify_cache.json`) 삭제.
- **(작업 2) 구 미사용 폐기**: `keywords_2d.json` · `build_embeddings.py` · `build_audio_map.py`.
- **(작업 5) 정서축 후속(optional)**: 전곡 660 정식 feature 부기(축 아님, 파생 보관용, ~46분 `phasec_features.py --full`) · 라벨 확대 확정검정 · 장르 밖 대조군.
- **(보류) 백필 1-c namedup 403**: 기존 곡 url을 Topic 음원으로 교체(품질 개선, 새 곡 아님). 후순위. (1-b 커버 135곡은 완료 — done 18.)
- **(보류) 진행도 Save/Load** (ux-02.md #4): 진행 json 백업/공유. ⚠️ Load = 기존 진행 덮어쓰기 → 손실 위험, 자동 백업·복구 경로 선설계 필수. 코멘트(`bandori-song-comments-v1`) 직렬화 포함 여부 확정 필요.
- **✅ (완료, done 24~25) 재생 이퀄라이저 = 음원맵 재생 펄스** — 전곡 660 pulse + 렌더 lazy-fetch + 에너지 기반 동적 subdivision(음량→박/8분) + 볼륨 프리셋 4단계. 상세 = [report/emoi-cluster-pulse](report/emoi-cluster-pulse/README.md). 롤백 = `16-audiomap.js` `CL_PULSE_BPM=false`. **(보류)** 방안 B(구간 tempo period) 프로토타입만(`section_pulse_proto.py`) · mugendai/난곡 예외 큐레이션(`CL_ONSET_DEFDIV`). 원안 = [spec/equalizer-animation.md](spec/equalizer-animation.md).

---

## 참고 (TODO 아님)

### ⏪ 롤백 지점
`backup/main-20260630-emoicloud`(local·origin) = emoi-cloud(워드클라우드 색·품질) 머지 **직전 main = `cebbce4`**. 문제 시 `git reset --hard cebbce4`(+force-push) 또는 `git revert -m 1 961ab93 && git push origin main`(라이브 안전·권장). 이전 백업 `backup/main-20260630` = `d586ffb`(1-b 커버 머지 직전).

### 지역락 — 정책 확립 (done 15·16, 절차만 재사용)
- **감지**: `check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `new_songs.csv` 대상 동일 로직.
- **정책(2026-06-29)**: 지역락 = 앱 데이터(`songs/*.yaml`)에서 삭제, 곡 정보는 `invalid_url.csv` 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **parked 4곡**(끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 대체 음원 재등록 완료 — done 19.) 워크시트 `region_blocked.csv`, 대체 URL은 **제목 대조 검증 필수**(세션 19 오입력 1건 적발).
