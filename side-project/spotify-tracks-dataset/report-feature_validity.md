# Spotify Tracks Dataset — 피처 유효성(다변량) 분석 리포트

> 선행 문서: [report-genre_audio_features.md](report-genre_audio_features.md)(장르별 η², 단변량), [report-pairwise_scatter.md](report-pairwise_scatter.md)(변수쌍 상관, 이변량).
> 이번 분석은 "변수 하나 혹은 둘"이 아니라, **14개 변수를 한꺼번에 넣었을 때 각 변수가 실제로 고유하게 기여하는 정보량**을 본다 — 앞선 두 리포트에서 계속 등장한 `loudness`↔`energy` 중복 신호가 다변량 관점에서는 어떻게 나타나는지 확인하는 것이 핵심 동기.

## 1. 방법 (Method)

**데이터셋 · 전처리 · 변수 3분류**: 앞선 두 리포트와 동일 — `dataset.csv` 113,999행, [metadata.md](data/metadata.md) 분류 그대로 사용.

**분석**(`feature_validity_rf.py`):
1. **VIF**(분산팽창지수, `statsmodels` 미설치로 직접 계산: `VIF_i = 1/(1-R²_i)`, R²_i = 나머지 13개 피처로 피처 i를 회귀했을 때 결정계수) — 피처 간 다중공선성(중복 신호) 사전 확인.
2. **RandomForestClassifier**(`track_genre` ~ 14개 피처)로 상호작용까지 반영한 분류기 학습 후 test accuracy·top-5 accuracy 확인.
3. **permutation_importance**(test set, accuracy 하락폭 기준)로 "이 피처를 무작위로 섞으면 정확도가 얼마나 떨어지는가" 측정 — impurity 기반 중요도(`feature_importances_`)보다 편향이 적어 해석 신뢰도가 높음. 두 값을 함께 표에 병기.

**VIF와 permutation importance를 함께 보는 이유**: 두 피처가 서로 강하게 얽혀 있으면(예: `loudness`-`energy`) 모델이 둘 중 하나만 있어도 나머지 정보를 대신 쓸 수 있어, 그 피처의 permutation importance가 실제 정보량보다 낮게 나올 수 있다. 이건 "무효"가 아니라 "중복"이라는 뜻이며, VIF가 그 구분을 제공한다.

**파라미터 규제(이번 실행에서 조정)**: 최초 시도는 `n_estimators=300, max_depth=None`(완전 성장) + `permutation_importance(n_repeats=10, n_jobs=1)`로 돌렸는데, 37분이 지나도 끝나지 않았다. 목적은 "최고 성능 분류기"가 아니라 "데이터 구조를 대변하는 정도의 모델"이므로, 완전 성장 트리는 114개 클래스에 대해 불필요하게 깊어져(과적합 위험 + 느린 학습/예측) 목적에 맞지 않다고 판단해 `n_estimators=150, max_depth=15, min_samples_leaf=10`으로 규제하고, `permutation_importance`도 `n_repeats=5, n_jobs=-1`로 조정했다. 규제 후 수 분 내 완료.

## 2. 결과 (Results)

### 2-1. VIF (다중공선성, 높을수록 다른 피처들로 설명 가능 = 중복)

| 피처 | 그룹 | R²(다른 피처로 예측) | VIF |
|---|---|---:|---:|
| `energy` | composite | 0.753 | **4.05** |
| `loudness` | low-level | 0.676 | **3.09** |
| `acousticness` | composite | 0.560 | 2.28 |
| `valence` | composite | 0.332 | 1.50 |
| `danceability` | composite | 0.309 | 1.45 |
| `instrumentalness` | composite | 0.301 | 1.43 |
| `liveness` | composite | 0.121 | 1.14 |
| `speechiness` | composite | 0.117 | 1.13 |
| `tempo` | low-level | 0.083 | 1.09 |
| `time_signature` | low-level | 0.071 | 1.08 |
| `duration_ms` | low-level | 0.052 | 1.05 |
| `mode` | low-level | 0.040 | 1.04 |
| `key` | low-level | 0.021 | 1.02 |
| `popularity` | model | 0.020 | 1.02 |

`energy`·`loudness`만 VIF 3~4대로 눈에 띄게 높다(둘이 서로를 상당 부분 설명). 나머지는 VIF < 2.3으로 다중공선성 문제가 크지 않다. `popularity`는 VIF가 가장 낮다(1.02) — 어떤 오디오 변수로도 거의 설명되지 않는다는 뜻([report-pairwise_scatter.md](report-pairwise_scatter.md) §2-1의 "popularity는 오디오 변수와 선형관계 없음" 결론과 일치).

### 2-2. RandomForestClassifier(`track_genre` ~ 14 features)

- 클래스 수(장르): 114 · chance-level(1/n): 0.0088
- **Test accuracy: 0.3234 · Test top-5 accuracy: 0.6749**

chance 대비 약 37배 — 14개 변수만으로도 장르를 상당히 잘 가른다. 다만 top-1과 top-5의 격차(0.32 vs 0.67)는 장르 경계가 실제로는 흐릿해(예: 인접한 무드/스타일 장르끼리) 모델이 "정답 후보군"까지는 잘 좁히지만 최종 하나를 못 집는 경우가 많다는 뜻.

### 2-3. Permutation Importance (test accuracy 하락폭, 내림차순)

| 피처 | 그룹 | perm. importance | RF impurity importance |
|---|---|---:|---:|
| `popularity` | model | **0.183** | 0.197 |
| `instrumentalness` | composite | 0.068 | 0.073 |
| `acousticness` | composite | 0.058 | 0.098 |
| `duration_ms` | low-level | 0.044 | 0.092 |
| `danceability` | composite | 0.044 | 0.090 |
| `valence` | composite | 0.034 | 0.080 |
| `energy` | composite | 0.029 | 0.069 |
| `speechiness` | composite | 0.026 | 0.085 |
| `loudness` | low-level | 0.025 | 0.075 |
| `tempo` | low-level | 0.022 | 0.069 |
| `liveness` | composite | 0.005 | 0.041 |
| `mode` | low-level | 0.004 | 0.010 |
| `time_signature` | low-level | 0.001 | 0.004 |
| `key` | low-level | 0.0005 | 0.015 |

## 3. 해석

- **`energy`·`loudness`는 단변량(ANOVA η²) 관점과 다변량(permutation importance) 관점에서 순위가 크게 갈린다.** 단변량에서는 각각 2위(0.455)·4위(0.451)였지만, 다변량에서는 7위(0.029)·9위(0.025)로 밀려난다. §2-1의 VIF(4.05/3.09)로 이미 확인한 대로, 둘이 서로 상당 부분 중복 정보라 모델이 하나로 나머지를 대신 쓸 수 있기 때문 — **"무효"가 아니라 "중복"**이라는 스크립트 설계 의도가 정확히 재현됐다.
- **`acousticness`·`instrumentalness`는 VIF가 낮고(2.28/1.43) permutation importance도 상위(3위·2위) 유지** — 다른 피처로 대체되지 않는 고유 정보를 갖는다는 뜻. `energy`/`loudness`와 달리 이 둘은 "중복 없는 진짜 신호"에 가깝다.
- **`popularity`가 permutation importance 1위(0.183)로, 단변량 순위(η²=0.254, 8위)·이변량 상관(어느 오디오 변수와도 |r|<0.1)과 전혀 다른 결과를 보인다.** 오디오 변수들과 선형·개별 관계는 없지만, 장르별로 비선형적인 인기도 분포 패턴이 있어 다변량 모델에서는 가장 유용한 판별 정보로 쓰인다는 뜻.
  - **다만 이 결과는 그리 놀랍지 않다.** `popularity`는 오디오 신호가 아니라 대중성 — 즉 시대적 트렌드·수요에 따른 산출물이므로, 애초에 다른 오디오 변수들과 공선성이 가장 낮으리라는 것은 사전에 예측 가능했다(실제로 VIF도 전체 최저인 1.02). "오디오 변수들로 설명 안 되는 고유 정보"라는 지위 자체는 새롭지 않고, 다만 그 고유 정보가 (RF가 학습한) 장르 판별에는 크게 쓸모 있다는 점만 이번에 정량적으로 확인됐다.
  - 그리고 이 지위와 별개로, **`popularity`는 우리 프로젝트(EMOI-MAP)에 실질적 쓸모가 없다.** 우리가 다루는 것은 로컬 오디오 파일이고, Spotify식 재생 이력 기반 인기도 같은 데이터는 우리 코퍼스에 애초에 존재하지 않으며 만들 수도 없다(오디오 신호에서 유도되는 값이 아니므로). 즉 이번 분석에서 가장 눈에 띄는 피처지만, 프록시화 대상에서는 자연히 제외된다.

## 4. 결론 및 제안 (Conclusion & Proposal)

**결론**:
1. `energy`/`loudness`는 서로 중복 신호라 다변량 관점에서는 개별 기여도가 단변량보다 훨씬 작다 — 장르 판별에 새 정보를 더하는 폭이 좁다.
2. `acousticness`/`instrumentalness`는 VIF가 낮고 다변량 permutation importance도 상위권 — 중복 없는 고유 정보를 갖는 피처다.
3. `popularity`는 다변량 관점에서 가장 유용한 판별 변수지만, 오디오 신호가 아니라 트렌드/수요 기반 산출물이라 애초에 다른 변수와 무관하리라 예측 가능했던 결과이고, 우리 프로젝트에 이식할 수도 없어 실질적 관심 대상은 아니다.

**EMOI-MAP에 대한 제안(적용은 아직 하지 않음)**:
- [report-genre_audio_features.md](report-genre_audio_features.md)에서 제안한 `acousticness_proxy`/`instrumentalness_proxy` 우선순위가 이번 다변량 분석으로 한 번 더 뒷받침된다 — 이 둘은 다른 피처로 대체되지 않는 고유 정보를 갖는 반면, `energy_proxy`는 `loudness`(≈`rms`) 계열과 상당 부분 중복되므로 "장르(≈편성) 구분" 목적에서는 추가 투자 대비 얻는 정보가 상대적으로 적다.
- 다음 단계로 이 검증 방법(VIF + RF + permutation importance)을 **우리 로컬 오디오 프록시 피처**(`rms`/`crest`/`onset_rate`, `harmonic_ratio`+`flatness`, `voiced_frac` 등)에도 그대로 적용해본다. 목표는 Spotify 데이터에서와 마찬가지로: (1) 우리 프록시들 사이에 `loudness`-`energy`급 중복이 있는지 VIF로 먼저 확인하고, (2) 밴드(장르 대리) 분류기에서 어떤 프록시가 고유하게 기여하는지 permutation importance로 본다. 다만 로컬 표본 수(≈30~수백곡 규모)가 Spotify(114,000행)보다 훨씬 작으므로, RF 파라미터는 이번에 배운 대로 처음부터 더 가볍게(`n_estimators`↓, `max_depth`↓, `min_samples_leaf`↑) 잡아 과적합을 피한다.
- `popularity`류 비오디오 변수는 우리 프록시 세트에 포함하지 않는다.

## 5. 로컬 교차검증 종합 (Spotify × 로컬 285곡)

이 방법(VIF + RF + permutation importance)을 [docs/working/report/genre-features/README.md](../../docs/working/report/genre-features/README.md)의 로컬 285곡(6밴드·270곡, `src/tools/cluster/genre_features_validity_rf.py`)에도 그대로 적용했다. 두 데이터셋·두 관점(단변량/다변량)을 겹쳐 최종 후보를 다음 세 그룹으로 정리한다.

**① 양쪽에서 모두 강한 신호 — 가장 신뢰할 후보**
- **`acousticness`(실 신호: `harmonic_ratio`)**: Spotify 단변량 η²=0.488(1위)·다변량 permutation importance 0.058(3위, VIF 2.28로 낮음) / 로컬 `harmonic_ratio` permutation importance 0.148(3위, VIF 3.89로 낮음) — 두 데이터셋·두 방법 전부에서 일관되게 상위권인 유일한 후보. 단, 로컬에서 `acousticness_proxy`의 두 성분(harmonic_ratio − flatness) 중 flatness는 기여가 거의 없어(perm. importance 0.022, 최하위권) **harmonic_ratio 단독을 핵심 신호로, flatness는 보조/재검토 대상으로** 낮춰야 한다.
- **`energy` — 단, "합쳐진 하나의 지표"가 아니라 "분해된 성분"으로**: Spotify에서는 `energy`가 `loudness`와 다중공선(VIF 4.05/3.09, r=0.762)이라 다변량 기여도가 낮다(7위, 0.029) — "라우드니스 하나로 뭉친 에너지" 개념 자체는 정보가 얇다는 뜻. 로컬에서는 그 대신 `rms`·`contrast`·`flux`(=`energy_proxy`의 세 성분)가 서로 VIF 1.7~2.7로 낮으면서 permutation importance 1·2·4위를 독식했다 — 세 성분이 서로 겹치지 않는 독립적 정보를 각각 나른다는 뜻. 종합하면 **`energy_proxy`는 지금처럼 rms+contrast+flux 3성분을 유지하는 게 근거 있는 설계**이고, 단일 loudness/rms 스칼라로 축소하면 안 된다.

**② 개념은 유망하지만 지금 측정이 약한 후보**
- **`instrumentalness`**: Spotify에서는 permutation importance 2위(0.068, VIF 1.43로 고유 정보)로 강했지만, 로컬 프록시 원재료 `voiced_frac_mix`는 중간 수준(0.035, 5위)에 그친다. 이 차이는 개념이 약해서가 아니라 **로컬 프록시 측정 방법 자체가 약해서**일 가능성이 크다(Demucs 미설치로 보컬분리 없이 믹스에서 직접 측정 → 리드 악기에 오염, [genre-features README](../../docs/working/report/genre-features/README.md) 한계 절 참고). 기각하지 말고 **Demucs 도입 후 재검증이 필요한 후보**로 남겨둔다.

**③ 양쪽에서 일관되게 약한 후보 — 우선순위 낮음**
- 스펙트럼 형태 지표군(`centroid`/`rolloff`/`zcr`/`flatness`): 로컬에서 서로 VIF 9~52로 심하게 겹치고 4개 다 permutation importance 최하위권 — 새 프록시 설계에 넷을 다 넣을 필요 없음.
- `duration`: Spotify(다변량 0.044, 4위)와 로컬(0.012, 최하위권)이 서로 어긋나 신호가 일관되지 않음 — 후보에서 제외.
- `popularity`: §3-§4에서 이미 확정한 대로 오디오 신호가 아니라 이식 불가 — 후보 자체가 아님.
- `tempo`/`key`/`mode`/`time_signature`류: 두 데이터셋 모두(Spotify 단변량·다변량, 로컬 `tempo_excerpt`·`mode_score`) 하위권 — 배제.

**다음 단계 우선순위**: ① `harmonic_ratio`(acousticness 축) 확정 사용 → ② `rms`+`contrast`+`flux`(energy_proxy) 3성분 유지 → ③ `instrumentalness`는 Demucs로 측정 방법부터 개선 후 재판단.

> **주의**: 이 결론은 로컬 285곡(전곡 660 중 부분 캐시, 10밴드 중 6밴드만 표본 충분)을 기준으로 한 잠정 결론이다. **최종 검증은 다른 로컬·세션에서 전곡(660곡) 오디오 캐시로 동일 방법(VIF+RF+permutation importance)을 재실행한 뒤** 이번 결론(특히 스펙트럼 형태 지표 중복·energy_proxy 3성분 구성)이 유지되는지 확인하고, 그 결과가 타당하면 **EMOI-MAP 축/프록시 설계를 개편**한다. 지금 단계에서는 EMOI-MAP 소스 변경을 하지 않는다.

## 6. 산출물

- `feature_validity_rf.py` — 분석 스크립트(pandas/scikit-learn, base env)
- `fig/feature-validity/vif_summary.csv` — 14개 피처 VIF, 내림차순
- `fig/feature-validity/feature_importance_summary.csv` — permutation importance·RF impurity importance, 내림차순
- `fig/feature-validity/run_summary.txt` — 분류기 성능 요약(n_classes, chance-level, test accuracy, top-5 accuracy, train/test 크기)
- `src/tools/cluster/genre_features_validity_rf.py` · `docs/working/report/genre-features/feature_validity_{vif,importance}.csv`, `feature_validity_run_summary.txt` — 로컬 교차검증 산출물
- 종합 그림·서사: [docs/research/feature-validity-extraction.md](../../docs/research/feature-validity-extraction.md)
