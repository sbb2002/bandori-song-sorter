# 밴드별 오디오 피처 재정의 — 로컬 285곡 분포 관찰

> 출처: [side-project/spotify-tracks-dataset/report-genre_audio_features.md](../../../../side-project/spotify-tracks-dataset/report-genre_audio_features.md) 결론 3.
> Spotify `acousticness`/`instrumentalness`/`energy`가 장르 구분력이 가장 강했으나 블랙박스라 값을 이식할 수 없어,
> 우리 파이프라인의 신호처리 산출물로 유사 개념을 재정의해 로컬 오디오에서 분포부터 확인한다.
> **EMOI-MAP 축에는 아직 적용하지 않음** — 분포 관찰 단계.

## 목적
장르 라벨이 없는 우리 코퍼스에서는 **밴드**를 장르/편성의 대리 변수로 쓴다(사용자 관찰: 대체로 J-rock이지만
바이올린을 채용하는 밴드·헤비메탈·일렉트로 믹스가 섞여 있음). Spotify 분석에서 장르 구분력이 가장 강했던
acousticness·instrumentalness·energy를 **우리 손으로 재정의**해, 밴드별로 실제 값이 갈리는지 확인한다.

## 방법
- **데이터**: 로컬 캐시 `src/content/cluster/audio_full`(48kHz WAV) 전량 — **285곡·10밴드**
  (afterglow 65 · hello_happy_world 65 · morfonica 50 · mygo 41 · ave_mujica 26 · mugendai_mutype 23 ·
  pastel_palettes 8 · various_artists 5 · millsage 1 · ikka_dumb_rock 1). 전곡 660 중 로컬에 있는 부분 캐시.
- **추출**(`src/tools/cluster/genre_features_extract.py`, hummingbird env — librosa/soundfile):
  전 곡 **중앙 45초 excerpt**(phasec_features.py의 harmonic_ratio 검증 패턴을 전체 feature로 확장,
  전체 로드 대비 ~5-6배 빠름)에서 `harmonic_ratio`(HPSS) · `flatness`·`contrast`·`flux`·`zcr`·`rms`·
  `centroid`·`rolloff`·`tempo_excerpt`(timbre 재사용) · `mode_score`·`key` · `voiced_frac_mix`(pyin, 보컬
  분리 없이 믹스에서 직접 — Demucs/torch 미설치로 대체).
- **프록시 합성**(`src/tools/cluster/genre_features_analyze.py`, base env — pandas/matplotlib/scipy):
  코퍼스 전체 z-score 기준으로
  - `acousticness_proxy = z(harmonic_ratio) − z(flatness)` (harmonic 성분 많고 노이즈 적을수록 ↑)
  - `instrumentalness_proxy = −z(voiced_frac_mix)` (믹스에서 유성음 검출 적을수록 ↑ — **약한 프록시**, 아래 한계 참고)
  - `energy_proxy = z(rms) + z(contrast) + z(flux)` (`docs/ref/audio_features_candidate.md`의 RMS+엔트로피+거칢 결합 힌트 반영)
- **검정**: 밴드 10그룹 one-way ANOVA(`scipy.stats.f_oneway`) + η²(SS_between/SS_total). 바이올린 플롯은
  밴드 중앙값 기준 정렬해 `*_violin.png`로 저장.

## 결과

η² 정렬(밴드 구분력, `band_anova_summary.csv`):

| feature | η² |
|---|---:|
| `rms` | 0.453 |
| `harmonic_ratio` | 0.452 |
| `contrast` | 0.330 |
| `flux` | 0.316 |
| **`acousticness_proxy`** | **0.291** |
| `zcr` | 0.286 |
| `centroid` | 0.214 |
| **`energy_proxy`** | **0.211** |
| `rolloff` | 0.198 |
| **`instrumentalness_proxy`** | **0.149** |
| `voiced_frac_mix` | 0.149 |
| `flatness` | 0.140 |
| `mode_score` | 0.130 |
| `tempo_excerpt` | 0.064 |

밴드별 평균(`song_features_with_proxies.csv`에서 집계):

| band | n | acousticness_proxy | harmonic_ratio | instrumentalness_proxy | energy_proxy |
|---|---:|---:|---:|---:|---:|
| morfonica | 50 | **+1.334** | **0.823** | −0.270 | +0.225 |
| mygo | 41 | +0.930 | 0.765 | −0.436 | +0.164 |
| ave_mujica | 26 | +0.497 | 0.764 | −0.060 | +0.177 |
| various_artists | 5 | +0.275 | 0.753 | +0.199 | **+0.962** |
| millsage | 1 | +0.013 | 0.705 | +1.411 | −0.860 |
| afterglow | 65 | −0.544 | 0.688 | −0.171 | −0.898 |
| hello_happy_world | 65 | −0.732 | 0.683 | +0.227 | +0.691 |
| mugendai_mutype | 23 | −1.002 | 0.716 | +0.902 | −0.514 |
| pastel_palettes | 8 | −1.420 | 0.712 | +0.754 | −0.140 |
| ikka_dumb_rock | 1 | −1.779 | 0.696 | +0.098 | −0.157 |

**해석**
- **acousticness_proxy에서 morfonica가 전체 최상위**(η²=0.291 전체 검정에서도 acousticness_proxy가 5위) —
  사용자가 언급한 "바이올린 채용 밴드" 가설과 방향이 일치한다. `harmonic_ratio` 단독으로도 morfonica가
  가장 높음(0.823), 즉 HPSS 기반 프록시가 실제 편성 차이를 잡아낸다는 정황.
- 원본 feature 중에서는 오히려 `rms`·`harmonic_ratio`·`contrast`·`flux`가 합성 프록시보다 η²이 높음 —
  Spotify 쪽 결과(합성 변수가 원본보다 강함)와 반대 방향. 표본이 작고(밴드당 1~65곡, 불균형) 프록시 조합
  가중치가 임의(균등 z-합)라 최적화되지 않았다는 점을 감안해야 한다.
- **instrumentalness_proxy는 가장 약함**(η²=0.149, `voiced_frac_mix`와 정확히 동일 — 당연히 부호만 반전된
  값이라 통계적으로 같은 정보). millsage/ikka_dumb_rock(n=1)은 표본 1곡이라 밴드 평균이 곧 그 곡 자체의
  값 — 통계적으로 신뢰 불가, 참고만.
- `energy_proxy`는 방향이 band마다 들쭉날쭉(afterglow −0.898 vs various_artists +0.962) — 헤비메탈 계열
  밴드(Roselia 등)가 이 로컬 캐시에는 없어서(부분 캐시, 660곡 중 285곡만) "일렉트로/메탈 vs 어쿠스틱" 대비가
  이 10밴드 안에서는 뚜렷하게 나타나지 않을 수 있음.

## 한계
- **표본 불균형**: 밴드당 1~65곡(millsage·ikka_dumb_rock은 n=1) — ANOVA/η²이 큰 밴드에 좌우됨.
- **부분 캐시**: 전곡 660 중 285곡(10밴드)만 로컬에 존재. 헤비메탈 계열 밴드가 빠져 있어 "메탈 vs 어쿠스틱"
  대비를 온전히 볼 수 없음.
- **instrumentalness_proxy는 약한 대체재**: Demucs/torch가 이 로컬에 미설치라 보컬 분리 없이 믹스에서 직접
  pyin으로 유성음 비율을 쟀다 — 리드 악기(기타 솔로 등)에 오염될 수 있음(`perceptual_features.py` 주석에도
  명시된 한계). 정확한 instrumentalness를 원하면 Demucs 설치 후 vocal/mix 에너지 비율로 재정의 필요.
- **z-score 합성 가중치는 균등(1:1)** — Spotify처럼 학습된 가중치가 아니라 임의 결합이므로, 프록시의 η²이
  개별 원본 feature보다 낮게 나온 것은 가중치 미최적화 탓일 수 있다.

## 다변량 검증 (VIF + RandomForest + Permutation Importance)

> 방법 출처: [side-project/spotify-tracks-dataset/report-feature_validity.md](../../../../side-project/spotify-tracks-dataset/report-feature_validity.md) —
> Spotify 114,000행에 적용한 것과 동일한 방법론을 로컬 285곡에 그대로 적용.
> 위 §결과(η², 단변량)만으로는 프록시가 원본 신호와 겹치는 정보인지 고유 정보인지 알 수 없어서,
> 다변량 관점(VIF로 중복도 확인 + RF permutation importance로 실제 기여도 확인)을 추가한다.

**방법**(`src/tools/cluster/genre_features_validity_rf.py`, base env):
- 표본수 20 미만인 밴드(pastel_palettes=8·various_artists=5·millsage=1·ikka_dumb_rock=1)는 stratified
  split이 불가능해 제외 → **6밴드·270곡**(afterglow·hello_happy_world·morfonica·mygo·ave_mujica·mugendai_mutype).
- 프록시(`acousticness_proxy`=z(harmonic_ratio)−z(flatness) 등)는 원본 피처의 **정확한 선형결합**이라
  원본과 함께 넣으면 설계행렬이 완전 특이(rank-deficient)해져 VIF가 전부 `inf`로 나온다(실제로 확인함) —
  "중복"이 아니라 산술적으로 당연한 결과라 해석에 쓸모가 없어, **원본 신호처리 피처 12개만**을 검증 대상으로 삼는다.
- RandomForest는 표본이 작아(Spotify 대비 1/400) 처음부터 가볍게 규제(`n_estimators=200, max_depth=6,
  min_samples_leaf=5`) — Spotify 분석에서 과규제 없이 돌렸다가 실행이 37분 넘게 걸렸던 교훈 반영.

**결과**:

| 피처 | VIF | perm. importance |
|---|---:|---:|
| `centroid` | **51.65** | 0.017 |
| `rolloff` | 27.61 | 0.021 |
| `zcr` | 16.35 | 0.019 |
| `flatness` | 9.16 | 0.022 |
| `harmonic_ratio` | 3.89 | **0.148** |
| `contrast` | 2.71 | **0.179** |
| `flux` | 1.99 | **0.068** |
| `rms` | 1.69 | **0.154** |
| `voiced_frac_mix` | 1.55 | 0.035 |
| `duration_s` | 1.20 | 0.012 |
| `mode_score` | 1.15 | 0.023 |
| `tempo_excerpt` | 1.09 | 0.008 |

- 클래스 수(밴드) 6 · chance-level 0.1667 · **test accuracy 0.7206**(n_train=202, n_test=68) — chance 대비 약 4.3배.
- **스펙트럼 형태 지표군(`centroid`·`rolloff`·`zcr`·`flatness`)은 VIF 9~52로 서로 강하게 겹치고, permutation
  importance는 전부 최하위권(0.017~0.022)** — 넷 중 하나만 있어도 나머지를 대신 쓸 수 있어 개별 기여도가
  작게 나온다. Spotify 리포트의 `loudness`↔`energy` 패턴(다중공선성 → 다변량 기여도 저평가)이 로컬 데이터에서도
  그대로 재현됐다.
- **`contrast`(0.179)·`rms`(0.154)·`harmonic_ratio`(0.148)·`flux`(0.068)는 VIF가 낮고 permutation importance도
  압도적으로 높다** — 밴드 판별에 중복 없이 고유하게 기여하는 핵심 4개 피처.
- **`energy_proxy = z(rms)+z(contrast)+z(flux)`의 세 구성 요소가 정확히 이 상위 4개 중 3개(rms·contrast·flux)와
  일치한다** — 임의로 고른 조합이 아니라 실제로 밴드 판별력이 가장 높은 원본 신호를 결합했다는 뜻으로,
  README 앞부분에서 "가중치가 임의(균등 z-합)"라고 지적했던 한계와 별개로 **구성 성분 선택 자체는 사후적으로
  타당했음**이 확인된다.
- **`acousticness_proxy = z(harmonic_ratio)−z(flatness)`는 두 성분의 기여도가 크게 비대칭**(harmonic_ratio
  0.148 vs flatness 0.022) — 이 프록시의 밴드 판별력은 사실상 `harmonic_ratio` 단독이 이끌고 있고, `flatness`
  항은 (acousticness 개념상으로는 타당해도) 밴드 분류 관점에서는 거의 정보를 더하지 않는다.
- `instrumentalness_proxy`의 원재료인 `voiced_frac_mix`(0.035)는 중간 수준 — README 한계 절에서 이미 지적한
  "약한 프록시"라는 평가와 방향이 일치한다.

**해석 — Spotify 분석과의 차이점 한 가지**: Spotify에서는 다중공선성이 `loudness`↔`energy` 단 한 쌍(VIF 3~4대)
에 국한됐지만, 로컬에서는 스펙트럼 형태 지표 4개가 한꺼번에 얽혀 있다(VIF 최대 51.65). 이는 `centroid`·`rolloff`·
`zcr`·`flatness`가 전부 "스펙트럼이 얼마나 밝고 납작한가"라는 같은 물리량을 서로 다른 방식으로 측정한 지표라서
— 신호처리 관점에서는 자연스러운 결과이지만, 넷을 전부 후속 분석(예: 새 프록시 설계)에 투입하는 건 비효율적이라는
실용적 시사점을 준다.

**표본 크기에 대한 주의**: n_test=68(6클래스, 클래스당 ~11곡)은 Spotify(n_test≈22,800)에 비해 매우 작아
permutation importance의 표준편차가 상대적으로 크다(`feature_validity_importance.csv` 참고). 순위 자체보다는
"상위 4개 vs 하위 8개"처럼 큰 격차가 있는 구간 구분 정도로만 신뢰하는 것이 안전하다.

## 다음 (제안, 미실행)
- 전곡 660 중 나머지(로컬에 없는 밴드, 특히 Roselia 등 하드록/메탈 계열) 오디오 확보 후 동일 스크립트 재실행 —
  "메탈 vs 바이올린 vs 일렉트로" 대비를 온전한 밴드 세트로 재검증. 밴드 수·표본이 늘면 다변량 검증(VIF/RF/PI)도
  함께 재실행해 이번 결과(특히 스펙트럼 형태 지표군 중복)가 유지되는지 확인.
- `centroid`·`rolloff`·`zcr` 중 일부는 새 프록시 설계 시 굳이 전부 포함할 필요가 없어 보임(중복 정보) —
  `flatness`(acousticness_proxy 성분) 정도만 유지하고 나머지는 후순위로.
- instrumentalness_proxy는 Demucs 설치 후 vocal 에너지 비율로 교체 재정의.
- 여기까지는 분포 관찰이며, **EMOI-MAP 축 변경 여부는 별도 결정**(필요 시 손라벨 상관검정으로 확정).

## 산출물
- `song_features.csv` — 285곡 원본 추출값 (band, idx, song, harmonic_ratio, flatness, contrast, flux, zcr,
  rms, centroid, rolloff, tempo_excerpt, mode_score, key, voiced_frac_mix)
- `song_features_with_proxies.csv` — 위 + acousticness/instrumentalness/energy proxy
- `band_anova_summary.csv` — feature별 η²/F/p
- `*_violin.png` — feature별 밴드 바이올린 플롯(밴드 중앙값 순 정렬)
- `feature_validity_vif.csv` — 원본 12피처 VIF(다변량 검증, 6밴드·270곡)
- `feature_validity_importance.csv` — permutation importance·RF impurity importance
- `feature_validity_run_summary.txt` — 분류기 성능 요약(밴드 필터링·test accuracy 등)
- 도구: `src/tools/cluster/genre_features_extract.py`(hummingbird env) ·
  `src/tools/cluster/genre_features_analyze.py`(base env) ·
  `src/tools/cluster/genre_features_validity_rf.py`(base env)

## 전곡 660·13밴드 재검증 결과 (2026-07-08, 세션 33)

> [../../../research/feature-validity-extraction.md](../../../research/feature-validity-extraction.md) §5 "최종 결정 유보"를 실행. 전곡 캐시(660곡·13밴드, 부분 캐시에 없던 **roselia·raise_a_suilen·poppin_party** = 하드록/전자/대형유닛 포함)를 보유한 로컬에서 동일 파이프라인 재실행 — 부분 캐시(285곡·10밴드, 다변량 6밴드) 3대 결론이 **메탈 포함 전곡에서 유지되는지** 검증.
> **절차**: N=15 밴드 균등 샘플(13밴드·157곡) 게이트 → 통과 후 전곡 660 확장. base env(librosa/soundfile/sklearn 전부 설치)로 4단계 전부 실행(별도 hummingbird env 불필요).

### 단변량 η² — 상위 핵심 안정, tempo 탈락

| feature | 부분 285(6→10밴드) | 균등 157(13밴드) | 전곡 660(13밴드) |
|---|---:|---:|---:|
| `rms` | 0.453 | 0.433 | **0.314** |
| `harmonic_ratio` | 0.452 | 0.313 | 0.287 |
| `contrast` | 0.330 | 0.338 | 0.284 |
| `flux` | 0.316 | 0.286 | 0.217 |
| `acousticness_proxy` | 0.291 | 0.258 | 0.228 |
| `energy_proxy` | 0.211 | 0.259 | 0.229 |
| `tempo_excerpt` | 0.064(유의) | 0.065(p=0.61) | 0.026(p=0.15) |

- `rms`·`harmonic_ratio`·`contrast` = 세 데이터셋 모두 top-3(순위 안정). η² 절대값은 밴드↑·표본↑로 하락(정상 — 클래스가 늘고 표본이 균형화되면 그룹내 분산↑).
- **`tempo_excerpt`는 균등·전곡에서 비유의**(p>0.05). 부분 캐시의 "약하지만 유의(0.064)"는 표본 불균형 산물이었음 — 새 발견, 강등.

### 다변량 (VIF + RF permutation importance) — 10밴드·653곡, test acc 0.439(chance 0.10의 4.4배)

| feature | VIF | perm. importance | 판정 |
|---|---:|---:|---|
| `centroid` | 48.8 | 0.000 | 중복(스펙트럼 형태) |
| `rolloff` | 25.3 | 0.034 | 중복(단 전자밴드로 약간 고유) |
| `zcr` | 16.3 | −0.013 | 중복 |
| `flatness` | 12.3 | −0.011 | 중복 |
| `contrast` | 2.71 | **0.102** | 고유(1위) |
| `harmonic_ratio` | 2.70 | **0.082** | 고유(2위) |
| `flux` | 1.82 | 0.038 | 고유 |
| `rms` | 1.46 | **0.058** | 고유 |

**부분 캐시 3대 결론 = 전부 확증·강화:**
1. **스펙트럼 형태 지표군(`centroid`/`rolloff`/`zcr`/`flatness`) 중복 → 저평가**: VIF 12~49로 여전히 강한 상호중복, PI가 부분 캐시(0.017~0.022)보다 더 내려가 **0 근처/음수로 붕괴**(표본↑로 고유기여 소멸이 더 선명). `rolloff`만 전자밴드(RAS의 극단적 rolloff) 덕에 PI +0.034로 살짝 양수 — 밝기군 중 유일하게 약간의 고유 신호.
2. **`energy_proxy` 3성분(`rms`+`contrast`+`flux`)**: 셋 다 PI 상위 4위 안(`contrast` 0.102·`rms` 0.058·`flux` 0.038) — 성분 선택 사후검증 유지.
3. **`acousticness_proxy` ≈ `harmonic_ratio` 주도**: `harmonic_ratio` PI 0.082 vs `flatness` PI −0.011 — 비대칭이 부분 캐시(0.148 vs 0.022)보다 더 극단. `flatness`는 밴드 분류에 기여 없음(음수).

### 메탈/전자 대비 — 이제 보임(부분 캐시엔 없던 축의 음의 끝)

밴드별 `acousticness_proxy` 평균(전곡): morfonica **+1.87**(최고, 바이올린) · mygo +1.30 · ave_mujica +0.80 · poppin_party +0.05 · **roselia −0.08**(심포닉메탈, 중간 — 오케스트라 하모닉) · afterglow −0.27 · hello_happy_world −0.44 · pastel_palettes −0.48 · mugendai_mutype −0.60 · **raise_a_suilen −1.03**(최저, 전자/하드) · ikka_dumb_rock −1.37(n=1). RAS의 낮은 acousticness는 `harmonic_ratio`(중간 0.72)가 아니라 **`flatness`(노이즈) 극단**이 구동 — morfonica는 하모닉이 많아서, RAS는 노이즈가 많아서 축 양끝에 서며 **다른 성분이 각 끝을 만든다.**

**결론**: 부분 캐시 3대 결론이 메탈 포함 전곡에서 유지·강화됨 → EMOI-MAP 프록시 우선순위(`harmonic_ratio`·`energy_proxy` 3성분)는 **데이터로 확증**. **단 EMOI-MAP 축/시각화의 실제 개편은 여전히 별도 결정** — 세션 33 이후 재생 펄스의 음색 시그니처 표현(Idea A 등) 시각화 실험으로 진행.

### 추가 산출물
- `band_anova_summary_sample15.csv` · `song_features_with_proxies_sample15.csv` — N=15 밴드 균등 샘플 게이트 스냅샷(13밴드·157곡).
- 이전 부분 캐시(285곡·10밴드) `song_features*.csv`는 git 이력(세션 32 커밋)에 보존 — 재생성 전 별도 백업 파일은 남기지 않음.
