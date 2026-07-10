# HANDOFF: bandori-song-sorter — 남은 작업

**이 문서 = 앞으로 할 일의 인덱스.** 각 작업은 요약 + 상세 레퍼런스 링크로만 구성한다. 완료 기록은 [done.md](done.md), 워드클라우드 품질 단일 출처는 memory `wordcloud_quality_plan.md`. 작성 규칙은 [readme.md](readme.md).

마지막 갱신: **2026-07-10(세션 39)** — **신규 앱 setlist-maker 기획: PRD 작성**(`side-project/playlist-maker`, main 미머지): umami 실측(일 방문 0명)으로 기존 앱 고도화 중단을 결정, 축적된 660곡 피처를 재활용하는 **별개 신규 앱**(하모닉 믹싱 + 자연어 감성 세트리스트 메이커)으로 피벗. 사용자 초안 `side-project/setlist-maker/draft.md` → `PRD.md` 9절 작성: 파일럿 = 자연어→LLM 무드/에너지 분석→에너지 진행×Camelot 선곡→유튜브 iframe 순차 재생까지(저장/공유 OAuth는 이월), 정량 지표 5종(umami 커스텀 이벤트), 클린 아키텍처(LLM 포트/어댑터 격리) 명시, 기존 피처의 무드 매칭 적합성 재조사는 오픈 퀘스천. done 39 참조. **펄스 채널 판정 규칙 결정(a/b/c)은 계속 미확정 이월.**
이전: **2026-07-09(세션 38)** — **Demucs other 스템 실험(가설 기각) + docs/working/report 전체 재분류 이관**(`feature/emoi-pulse-signature`, main 미머지): 세션 37 가설("어두운 믹스가 밝기군을 가린다, other 스템만 재면 완화될 것")을 실측(mygo·ave_mujica·morfonica 대조군 11곡) → **정반대 결과**: other 스템에서 밝기군이 11곡 전부 오히려 하락(드럼 심벌·보컬 치찰음이 고주파 에너지원이었던 것으로 추정), ave_mujica·mygo는 harmonic_ratio까지 더 상승해 acoustic 쏠림이 **악화**됨 — 접근 폐기. 상세 = `side-project/band-audio-analysis/report-other-stem-experiment.md`. **+ `docs/working/report/`(5항목) 전체를 연구 주제별로 `side-project/`에 재분류 이관**(`emoi-map-axis-correlation`·`emoi-map-emotion-axes/{phase-b0,phase-c}`·`emoi-map-pulse`·`genre-features`), 코드 14개·문서 15개 경로 참조 전수 수정. done 38 참조. **다음 결정(사용자 미확정, 세션 37에서 이월)**: `add_pulse_shape.py` 채널 판정 규칙 (a)유지 (b)bright 보정 (c)neutral 임계값 조정.
이전: **2026-07-09(세션 37)** — **EMOI-MAP 7항목 밴드별 분포 분석 완료**(`feature/emoi-pulse-signature`, main 미머지): 오디오 재추출 없이(이미 커밋된 CSV·JSON만으로, "다른 로컬 필요"는 세션 36의 착오였음 — 정정) `side-project/band-audio-analysis/`에서 660곡 전부 분석. **ave_mujica(48.3%)보다 mygo(63.4% acoustic)가 더 극단**적임을 발견 — 원인은 장르가 아니라 **밝기군(centroid/rolloff/zcr/flatness) 중앙값이 낮은 밴드는 acoustic 채널로 구조적으로 쏠리는** 상대비교 구조(mygo·ave_mujica 둘 다 밝기군 최하위권으로 확인). raise_a_suilen(57.5% bright)·morfonica(84.2% acoustic)는 장르 기대와 일치(양성 대조군) — 채널 로직 자체는 안 틀렸고 믹스 밝기가 왜곡 요인. 상세 = `side-project/band-audio-analysis/README.md` · done 37.
이전: **2026-07-09(세션 36)** — **EMOI-MAP 밴드 네트워크 메시 추가 + 펄스 채널 이상 발견**(`feature/emoi-pulse-signature`, main 미머지): `quantum.html`(3D 뉴럴네트워크 데모)을 디자인 레퍼런스로 검토 → 풀 3D 전환은 보류(모바일 부담·UX 복잡도), "점선 네트워크 그래프"만 차용. 밴드 포커스 시에만(ALL 미표시) 곡별 k-최근접(`CL_MESH_K=3`) 점선 메시, 이후 가시성 요청으로 밝기 상향(opacity 0.22→0.55·lineWidth 1→1.4·`_clPulseColor` 밝기보정). **펄스 시그니처(세션 35) 점검 중 이상 발견**: ave_mujica(헤비메탈 성향)가 29곡 중 14곡(48%)이 acoustic 채널로 분류(전곡 평균 29.1%보다 훨씬 높음) — `harmonic_ratio`(HPSS 톤/타격비)는 높은데 `bright`(centroid/rolloff/zcr/flatness)가 극단적으로 낮아(z −2~−3대) 상대 비교에서 acoustic이 이김. done 36 참조.
이전: **2026-07-09(세션 35)** — **EMOI-MAP 재생펄스 음색 시그니처 4모양 Exp1 구현 완료**(`feature/emoi-pulse-signature`, main 미머지): 세션 34 데모 아티팩트를 사용자가 그대로 채택 확정 → `add_pulse_shape.py` 신규(전곡 660 채널 분류, neutral 29.1%/acoustic 29.1%/bright 23.6%/shimmer 18.2%, 데모 예고치와 일치) + `16-audiomap.js`의 `_clEmitPulse` 4분기 확장(색은 유지, 모양만 채널화). 데이터 흐름·geometry는 정적 검증 완료, 애니메이션 스크린샷은 headless 환경 한계로 실사용자 육안 확인 필요. done 35 참조.
이전: **2026-07-08(세션 34)** — **EMOI-MAP 재생펄스 음색 시그니처 시각화 설계·데모 아티팩트 발행**(아직 브랜치 미생성): Idea A(펄스 모양=음색) 채택 · Idea B(PCA) 기각 · 4모양(neutral/acoustic/bright/shimmer) 인터랙티브 데모 아티팩트 발행 · Exp1~4 리스크순 브랜치 플랜(Exp1·2 병행 확정). 단일 출처 memory `pulse_signature_shapes.md` · 작업 6 "다음 단계" 참조. ⚠️ 이 논의는 방향키 네비게이션으로 대화 분기가 유실됐다가 세션 jsonl에서 복구함.

---

## 시작 전 체크 (다른 로컬·세션)
> 1. `git pull origin main`(660곡). 작업은 **feature 브랜치**에서(작업 5 = `feature/emoi-map-starfield`).
> 2. `.env`의 `YOUTUBE_API_KEY` = **장치별·비커밋**(gitignore) — 백필/지역락 점검 시 재추가(없으면 `insert_backfill.py`·`check_embeddable.py` 즉시 중단).
> 3. **node 필수**(yt-dlp nsig 서명해독 → 없으면 오디오 수집 403 다발 · `node --check` · `npm test`). 설치 = `conda install -c conda-forge nodejs`.
> 4. 가사 원문 `assets/lyrics/<band>.md` = 로컬 전용(gitignore). 커밋된 `wordcloud/<band>.yaml`로 검수·렌더는 가능하나 `build_keywords.py` **재생성은 원문 .md 필요**.
> 5. 로컬 브랜치(2026-06-30 정리): `main` + 백업 3(`backup/main-20260620·22·30`) + `feature/ux-02-opt-a`(옵션A 유일본, 미머지·원격없음 — 삭제 금지).
> 6. **오디오 있는 로컬이면**: 세션 36의 "펄스 채널 이상 발견"(위 § 열린 결정) 참조 — EMOI-MAP 7항목 밴드별
>    분포 분석을 `side-project/band-audio-analysis/`에서 진행. `feature/emoi-pulse-signature` 브랜치에서 이어서.

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
| 6. 장르(밴드) 오디오 피처 재정의 | ✅ 3중 렌즈 재검증 완료 · **펄스 시그니처 Exp1 구현 완료**(main 미머지, 육안확인 대기) | [done 32·33·35](done.md) · [논문](../research/feature-validity-extraction.md) · [side-project/genre-features](../../side-project/genre-features/README.md) |
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
[side-project/genre-features/README.md](../../side-project/genre-features/README.md) · Spotify 3보고서
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
5. 결과는 `side-project/genre-features/`에 갱신(같은 파일 덮어씀)
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
강등. **이후 = EMOI-MAP 재생펄스 음색 시그니처 시각화**(단일 출처 memory `pulse_signature_shapes.md`):
- **Idea A 채택**(데이터 지지 71% 뚜렷·29% neutral) · **Idea B(PCA 지도) 기각**(silhouette −0.18).
- **펄스 4모양 데모 아티팩트 발행됨**(눈으로 비교용): `neutral` 매끈원 · `acoustic` 6엽 물결링(harmonic↑) ·
  `bright` 톱니링(밝기군↑) · `shimmer` 이중 명멸링(flux↑, "electric"→개명).
  → https://claude.ai/code/artifact/b177e3e3-5965-4b62-9070-bfd76f479005
- ✅ **(a)4모양 그대로 채택 확정**(사용자, 세션 35) → **Exp1(`feature/emoi-pulse-signature`) 구현 완료**:
  `add_pulse_shape.py`(채널 분류·audio_map.json patch) + `16-audiomap.js` `_clEmitPulse` 4분기. 상세 = done 35.
  아직 **main 미머지**(실사용자 육안 확인 대기 — headless 환경이라 애니메이션 스크린샷 자체 검증은 못 함,
  데이터/geometry 정적 검증만 완료). 확인되면 main 머지.
- **Exp2(`feature/emoi-pulse-drums`, 킥/스네어 대역분리)는 아직 미착수** — 기존 `audio_drums` 660 재사용·새
  Demucs 불필요·~15분, 프론트 `lv.kick`/`lv.snare` 훅 기존재. Exp3(`feature/emoi-pulse-melodic`, Demucs `other`)·
  Exp4(bass, 선택)도 미착수.
- 손라벨 상관검정·**EMOI-MAP 축 실제 개편은 그 이후 별도 결정**(이건 펄스 모양만, 축 무변경).
- ⚠️ 세션 34: 이 논의가 방향키 네비로 대화분기 유실→세션 jsonl에서 복구(done.md/HANDOFF에 3모양·아티팩트 없었음).
- **세션 36: 밴드 네트워크 메시 추가**(포커스 시 곡별 k-최근접 점선, `CL_MESH_K=3`) + 사용자 요청으로 밝기 상향.
  상세 = done 36.
- **✅ 세션 37: 7항목 밴드별 분포 분석 완료**(`side-project/band-audio-analysis/`) — 세션 36의
  "다른 로컬 필요"는 착오였음(오디오 재추출 불필요, 이미 커밋된 CSV·JSON으로 이 로컬에서 바로 가능했음).
  **ave_mujica(48.3%)보다 mygo(63.4% acoustic)가 더 극단적**임을 추가 발견. 원인은 장르가 아니라
  **밝기군(centroid/rolloff/zcr/flatness) 중앙값이 낮은 밴드는 acoustic으로 구조적으로 쏠리는**
  상대비교 구조(mygo·ave_mujica 둘 다 밝기군 최하위권 확인) — 세션 36 가설이 일반 패턴임을 확증.
  raise_a_suilen(57.5% bright)·morfonica(84.2% acoustic)는 장르 기대와 일치(양성 대조군).
  **다음 결정(사용자 미확정)**: `add_pulse_shape.py` 채널 판정 규칙 (a)유지 (b)bright 그룹 보정
  (c)neutral 임계값(현재 0.4) 조정 — 상세·수치 = `side-project/band-audio-analysis/README.md` · done 37.

---

## 열린 결정 (사용자)
- ✅ ~~(레이아웃 — 묶어서 결정)~~ **해소(done 22)**: 유튜브 컬럼 하단 슬롯을 세로 분할 → **좌=음원맵 / 우=워드클라우드(대안 B)** + 유튜브 16:9 + 우패널 히스토그램·히트맵 동시표시 + 곡리스트 30%↓·긴곡명 마퀴 + 모바일 세로 스택.
- **(기능)** 진행률 링 70% 하드게이트: 현재 70% Green은 링 색상일 뿐, "70%↑만 최애밴드 자격" 게이트 미도입(현재는 스코어링 수축 `w(n)`만). 도입 여부 별도 결정(ux-02.md #2).

## 보류 · 백로그
- **(세션 36, 보류 결정) EMOI-MAP 풀 3D(Three.js/WebGL) 전환 안 함**: `side-project/emoi-map-design-candidate/quantum.html`
  검토 결과, 시각·인터랙션은 마음에 들지만 (a) 기존 상호작용(곡클릭재생·밴드포커스줌·툴팁·펄스시그니처 등)을
  전부 3D로 재설계해야 하는 규모(830줄 `16-audiomap.js`가 ECharts API에 강결합) (b) 모바일에서 상시 블룸
  포스트프로세싱·additive blending 오버드로우로 배터리/발열 부담 — 대비 실익 낮음. **"점선 네트워크 메시"
  컨셉만 차용해 2D에 이식**(done 36). z축을 곡 arousal/에너지의 "3번째 지각축"으로 쓰는 것도 이미 기각
  (done 30, `research/emotion-axes-extraction.md` §3.2 — 통계적으로 독립축 아님). 재검토 시 이 항목부터 확인.
- **(작업 3 — 사용자 요청·미구현) 분석-only 로컬 스크립트**: 다운로드는 다른 로컬/수단으로 받고 분석~push만 하는 별도 파일. 일부 로컬은 분석 라이브러리(torch/demucs 등) 구동 불가 → 다운로드/분석 역할 분리 필요. **현재 `run_local.py`(다운로드+분석 일체형)는 유지**하고 추가.
- **(작업 3) 기타 정리**: DRM `roselia 競宴Red×Violet` 수동 · 영구실패 재시도 상한 가드 · index.html `git rm --cached`(Option A 완전화) · 옛 프로토타입 잔재(`rss_seen.json`·`rss_inbox.csv`·`verify_cache.json`) 삭제.
- **(작업 2) 구 미사용 폐기**: `keywords_2d.json` · `build_embeddings.py` · `build_audio_map.py`.
- **(작업 5) 정서축 후속(optional)**: 전곡 660 정식 feature 부기(축 아님, 파생 보관용, ~46분 `phasec_features.py --full`) · 라벨 확대 확정검정 · 장르 밖 대조군.
- **(보류) 백필 1-c namedup 403**: 기존 곡 url을 Topic 음원으로 교체(품질 개선, 새 곡 아님). 후순위. (1-b 커버 135곡은 완료 — done 18.)
- **(보류) 진행도 Save/Load** (ux-02.md #4): 진행 json 백업/공유. ⚠️ Load = 기존 진행 덮어쓰기 → 손실 위험, 자동 백업·복구 경로 선설계 필수. 코멘트(`bandori-song-comments-v1`) 직렬화 포함 여부 확정 필요.
- **✅ (완료, done 24~25) 재생 이퀄라이저 = 음원맵 재생 펄스** — 전곡 660 pulse + 렌더 lazy-fetch + 에너지 기반 동적 subdivision(음량→박/8분) + 볼륨 프리셋 4단계. 상세 = [side-project/emoi-map-pulse](../../side-project/emoi-map-pulse/README.md). 롤백 = `16-audiomap.js` `CL_PULSE_BPM=false`. **(보류)** 방안 B(구간 tempo period) 프로토타입만(`section_pulse_proto.py`) · mugendai/난곡 예외 큐레이션(`CL_ONSET_DEFDIV`). 원안 = [spec/equalizer-animation.md](spec/equalizer-animation.md).

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
