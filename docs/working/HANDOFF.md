# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`. 작성 규칙은 [readme.md](readme.md).

마지막 갱신: **2026-07-08(세션 33)** — **오디오 피처 유효성: 전곡 660·13밴드 3중 렌즈 재검증 완료**(`analysis/audio-feats`, main 미머지): 전곡 캐시 로컬에서 N=15 밴드 균등 게이트(통과) → 전곡 660 확장 재실행. **부분 캐시 3대 결론(스펙트럼 형태 지표군 중복→PI 붕괴 · `energy_proxy` 3성분 · `acousticness`=`harmonic_ratio` 주도) 전부 확증·강화**, `tempo_excerpt`는 비유의로 강등, 메탈/전자(roselia·RAS) 포함으로 "메탈 vs 어쿠스틱" 대비 확인. 이후 = **EMOI-MAP 시각화 실험**(재생 펄스 음색 시그니처 = Idea A 등, 리스크순 브랜치 비교). done 33 · 작업 6 참조.
이전: **2026-07-08(세션 32)** — **오디오 피처 유효성 3중 렌즈 분석(단·이·다변량) + 우리 샘플 교차검증**(Spotify 114,000곡 side-project + 로컬 285/660곡, `analysis/audio-feats`, main 미머지): acousticness_proxy가 morfonica(바이올린 밴드) 최고치로 가설 일치 + 다변량(VIF+RF)에서 loudness↔energy 중복·popularity 반전 확인, energy_proxy 3성분 사후 검증. research 승격([feature-validity-extraction.md](../research/feature-validity-extraction.md)). 전곡 확대는 다른 로컬. done 32 · 작업 6 참조.
이전: **2026-07-08(세션 31)** — **작업 1·2·3·5 done 이관·HANDOFF 슬림화 + EMOI-MAP minor fix**: 네 작업 본류 완료 확인 → 작업 절을 요약+링크로 축약(선택 잔여는 § 보류·백로그로 이동, 구 '병렬 실행 계획' 제거). **+minor fix(fix/emoi-map-labels-pulse)**: 축 라벨 '음색이 거친/부드러운'·'발랄한/진지한 느낌', 재생 HUD를 밴드 평균점 대비 편차 기준으로, 펄스 16분 주석 비활성(CL_DYN_MAX=1 유지) + research 작성 규칙(README 양식·승격기준). done 31 참조.
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
| 1. 워드클라우드 | ✅ **완전 완료**(품질+배치 D) | [done 20·22](done.md) |
| 2. 음원맵 전곡 확대 | ✅ **완결·동결**(659곡·norm) | [done 23](done.md) · [spec](spec/audio-map-axes.md) |
| 3. 자동화 파이프라인 | ✅ **반자동 운영화 완료·라이브** | [done 26·27·28](done.md) · [spec](spec/pipeline-automation.md) |
| 4. EMOI-MAP 딥스페이스/별 시각화 | ✅ **완료·main 머지**(104e709) | [done 29](done.md) |
| 5. EMOI-MAP 좌표계 고찰 | ✅ **A·B0·C 완료**(172684e) — timbre×valence 확정 | [done 30](done.md) · [논문](../research/emotion-axes-extraction.md) |
| 6. 장르(밴드) 오디오 피처 재정의 | ✅ **전곡 660·13밴드 3중 렌즈 재검증 완료**(3대 결론 확증) · 시각화 개편은 별도(진행 예정) | [done 32·33](done.md) · [논문](../research/feature-validity-extraction.md) · [report/genre-features](report/genre-features/README.md) |
| 보류 · 백로그 | 후순위 | § 보류·백로그 |

원칙: **밴드 시각화 마무리 → 후속 확장.** 보류·백로그는 별도 결정 사안.

> 작업 1·2·3·5의 **완료 상세**(품질·배치·오디오 수집 659/660·전곡 빌드·`norm` 동결·반자동 배선·CI 봇월 실증·좌표계 연구)는 전부 done.md(17·20·22·23·26·27·28·30)로 이관 완료. 잔여 작업은 전부 § 보류·백로그.

---

## 작업 6 — 장르(밴드) 오디오 피처 재정의

Spotify Tracks Dataset(side-project)에서 `acousticness`·`energy`·`instrumentalness` 같은 합성 변수가
장르 구분력이 가장 강함을 확인했으나 블랙박스라 값을 이식할 수 없음 → 자체 신호처리(harmonic_ratio/HPSS·
flatness·voiced_frac 등)로 유사 개념을 재정의해 로컬 오디오(부분 캐시 285/660곡, 10밴드)에서 밴드별 분포를
검증. **acousticness_proxy가 morfonica(바이올린 채용 밴드)에서 전체 최고치**로 가설과 일치. 이어 **단·이·다변량
3중 렌즈**(VIF+RF+permutation importance)를 Spotify·로컬 양쪽에 적용 → loudness↔energy 중복이 다변량에서
저평가되는 패턴을 두 데이터셋에서 확인, `energy_proxy` 3성분(rms+contrast+flux) 사후 검증. 종합 논문
[../research/feature-validity-extraction.md](../research/feature-validity-extraction.md) · 로컬 상세
[report/genre-features/README.md](report/genre-features/README.md) · Spotify 3보고서
[단변량](../../side-project/spotify-tracks-dataset/report-genre_audio_features.md)·[이변량](../../side-project/spotify-tracks-dataset/report-pairwise_scatter.md)·[다변량](../../side-project/spotify-tracks-dataset/report-feature_validity.md).

**다른 로컬에서 이어받는 법**(전곡 660을 한 번에 처리하지 말고 **밴드별 N곡 샘플링으로 먼저 유효성 검증** →
유효하면 그때 전곡 확대 — 사용자 결정, 2026-07-08. **그 로컬은 오디오 660곡 전곡이 이미 로컬에 확보돼
있어 다운로드 불필요** — `--download` 플래그 쓰지 말 것):
1. `git fetch && git checkout analysis/audio-feats`
2. **0단계(샘플링, manifest만 생성)**: `python src/tools/cluster/genre_features_sample.py --n 15`
   — songs_full.csv **13개 밴드 전체**(이 로컬엔 없던 roselia·poppin_party·raise_a_suilen 하드록/대형유닛
   포함)에서 밴드당 최대 15곡 랜덤 샘플링(seed=42, 재현 가능) → `sample_manifest.csv`에 목록만 기록(오디오는
   이미 있으니 다운로드 안 함, 존재 여부만 확인). 부족한 밴드(ikka_dumb_rock·millsage=1곡, various_artists=5곡)는 전량.
3. 추출(hummingbird env — librosa/soundfile, pandas/matplotlib 불필요, 체크포인트 재개):
   `python src/tools/cluster/genre_features_extract.py` — **`sample_manifest.csv`가 있으면 그 목록만 자동
   처리**(전곡 660 중 샘플된 것만, `--all`로 전곡 강제 가능)
4. 분석(base env — pandas/matplotlib/scipy, librosa 불필요): `python src/tools/cluster/genre_features_analyze.py`
5. 결과는 `docs/working/report/genre-features/`에 갱신(같은 파일 덮어씀)
6. **13밴드·샘플 규모에서 프록시가 여전히 유효(η² 유지·특히 roselia 등 메탈 밴드에서 acousticness_proxy가
   낮게 나오는지)하면 그때** `genre_features_extract.py --all`로 전곡 660 확장(오디오가 이미 있으니 샘플링
   단계 없이 바로 가능).

**유효했던 변수 — 모두 계속 분석**(사용자 확인: 일부만 추리지 말고 유의했던 변수는 전부 유지):
14개 전부 p<0.05(밴드 간 유의)였고, 효과크기(η²)는 아래 순서로 갈렸다 — 샘플 검증 때도 이 순서가
유지되는지 그대로 확인.
- 강함(η²>0.19): `rms`(0.453)·`harmonic_ratio`(0.452)·`contrast`(0.330)·`flux`(0.316)·`acousticness_proxy`(0.291)·`zcr`(0.286)·`centroid`(0.214)·`energy_proxy`(0.211)·`rolloff`(0.198)
- 중간(0.13~0.15): `instrumentalness_proxy`/`voiced_frac_mix`(0.149)·`flatness`(0.140)·`mode_score`(0.130)
- 약함(그래도 유의): `tempo_excerpt`(0.064)
- 위 순서가 표본 불균형(당시 밴드당 1~65곡) 때문이었는지, 13밴드 균등 샘플(N=15)에서 재확인 필요.

**알려진 한계**: instrumentalness_proxy는 Demucs 보컬분리 없이 믹스 pyin으로 근사한 약한 프록시(Demucs
설치 후 vocal/mix 에너지비로 재정의 권장). 헤비메탈 계열 밴드(Roselia 등)가 이 로컬 캐시에 없어 "메탈 vs
어쿠스틱" 대비가 아직 안 보임 — 전곡 확보로 해소될 것.

**다음 단계**: ✅ 전곡 660·13밴드 재검증 완료(세션 33, done 33) — 3대 결론(스펙트럼 형태 지표 중복 ·
`energy_proxy` 3성분 · `acousticness`=`harmonic_ratio` 주도) 전부 확증·강화, `tempo_excerpt`는 비유의로
강등. **이후 = EMOI-MAP 시각화 실험**(재생 펄스에 음색 시그니처 표현 — Idea A[곡별 대표 파형] 채택 +
Demucs 스템 펄스[킥/스네어·멜로디밴드 미약파동] 검토, **리스크 작은 순서대로 각각 브랜치 만들어 비교**).
손라벨 상관검정·EMOI-MAP 축 실제 개편은 그 이후 별도 결정(아직 미적용).

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

### 편집 규칙 — EMOI-MAP
`16-audiomap.js`·`desktop/mobile.css` **직접수정**(참조식 → 리빌드 불필요) · `audio_map.json` 변경 시에만 `python src/build.py`.

### 지역락 — 정책 확립 (done 15·16, 절차만 재사용)
- **감지**: `check_embeddable.py`(Data API `regionRestriction` + 한국 IP `playabilityStatus` 2신호). 신규 백필은 `new_songs.csv` 대상 동일 로직.
- **정책(2026-06-29)**: 지역락 = 앱 데이터(`songs/*.yaml`)에서 삭제, 곡 정보는 `invalid_url.csv` 보존(가드: 그 vid는 재실행으로 부활 안 함).
- **parked 4곡**(끝까지 지역락): poppin `千本桜` · RAS `DAYBREAK FRONTLINE`·`DEAD HEAT BEAT` · roselia `Our Carol`. (나머지 지역락 20곡은 대체 음원 재등록 완료 — done 19.) 워크시트 `region_blocked.csv`, 대체 URL은 **제목 대조 검증 필수**(세션 19 오입력 1건 적발).
