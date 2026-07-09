# Spotify Tracks Dataset — 변수 그룹 간 상관관계(산점도) 분석 리포트

> 선행 문서: [report-genre_audio_features.md](report-genre_audio_features.md) — 장르별 분산 설명력(η²) 분석.
> 이번 분석은 "장르가 각 변수를 얼마나 가르는가"가 아니라, **변수끼리(특히 저수준·합성·모델예측 그룹 사이) 서로 얼마나 연관되는가**를 본다.

## 1. 방법 (Method)

**데이터셋 · 전처리**: [report-genre_audio_features.md](report-genre_audio_features.md)와 동일 — `dataset.csv` 114,000행, `distribution.py`의 `cleanse_dataset()`으로 결측치·`duration_ms==0` 행 제거 (n=113,999).

**변수 3분류**: [metadata.md](data/metadata.md) 하단 분류를 그대로 사용.

| 그룹 | 변수 |
|---|---|
| 1. 저수준 | `duration_ms`, `key`, `mode`, `loudness`, `tempo`, `time_signature` |
| 2. 합성 | `danceability`, `energy`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence` |
| 3. 모델 예측 | `popularity` (`track_genre`는 범주형이라 산점도 대상에서 제외, 그룹핑 변수로만 사용) |

**짝짓기**: 서로 다른 두 그룹에서 변수를 하나씩 뽑아 짝을 만든다(같은 그룹 내부 짝은 제외 — 그룹 분류 자체의 목적이 "저수준 vs 합성 vs 모델예측" 간 관계를 보는 것이므로).
- 1×2 = 6×7 = 42쌍, 1×3 = 6×1 = 6쌍, 2×3 = 7×1 = 7쌍 → **총 55쌍**

**분석**(`scatter_pairwise.py`):
1. **전체(overall)**: 각 쌍에 대해 114,000개 전체 점을 hexbin(로그 스케일 카운트)으로 산점도화하고 Pearson r·p 계산 → `fig/scatter-pairwise/{group}_{x}_vs_{y}_overall.png`
2. **장르별**: `track_genre`(114개)로 그룹핑해 그룹별 Pearson r을 계산하고, r 오름차순으로 정렬한 막대그래프(점선=전체 r) → `fig/scatter-pairwise/{group}_{x}_vs_{y}_by_genre.png`
   - 표본 5개 미만이거나 분산이 0인 장르는 제외
3. 요약 통계 2종 저장:
   - `_overall_correlation_summary.csv` — 55쌍 전체 r·p, |r| 내림차순
   - `_genre_correlation_variability_summary.csv` — 55쌍의 장르별 r 평균·표준편차·최소/최대(해당 장르)·부호반전 장르 수, 표준편차 내림차순

## 2. 결과 (Results)

### 2-1. 전체 상관관계 (|r| 상위 10, `_overall_correlation_summary.csv` 전체 참고)

| 그룹 | x | y | r | 해석 |
|---|---|---|---:|---|
| 1×2 | `loudness` | `energy` | **+0.762** | 가장 강한 상관 — 사실상 서로의 raw/합성 대응물 |
| 1×2 | `loudness` | `acousticness` | −0.590 | 조용할수록 어쿠스틱하다고 판단됨 |
| 1×2 | `loudness` | `instrumentalness` | −0.433 | 조용할수록 보컬 없을 가능성 높게 판단됨 |
| 1×2 | `loudness` | `valence` | +0.280 | |
| 1×2 | `loudness` | `danceability` | +0.259 | |
| 1×2 | `tempo` | `energy` | +0.248 | |
| 1×2 | `tempo` | `acousticness` | −0.208 | |
| 1×2 | `time_signature` | `danceability` | +0.207 | |
| 1×2 | `time_signature` | `energy` | +0.187 | |
| 1×2 | `time_signature` | `acousticness` | −0.176 | |

**1×3, 2×3(= popularity와의 관계)은 전부 약함** — 가장 강한 것도 `instrumentalness` vs `popularity` r=−0.095, `loudness` vs `popularity` r=+0.050. `energy` vs `popularity`는 r=0.001(p=0.72)로 사실상 무상관. → **popularity는 어떤 저수준/합성 오디오 변수와도 뚜렷한 선형관계가 없다.** [report-genre_audio_features.md](report-genre_audio_features.md)에서 이미 지적한 "popularity는 오디오 신호가 아니라 재생 이력 기반 알고리즘 산출값"이라는 결론과 정확히 일치한다.

### 2-2. 장르별 상관관계 변동성 (표준편차 상위 8, `_genre_correlation_variability_summary.csv` 전체 참고)

| x | y | overall r | 장르별 r 범위 (최소~최대) | 부호반전 장르 수/114 |
|---|---|---:|---|---:|
| `loudness` | `acousticness` | −0.590 | piano −0.797 ~ happy +0.085 | 3 |
| `loudness` | `instrumentalness` | −0.433 | piano −0.874 ~ power-pop +0.109 | 5 |
| `loudness` | `danceability` | +0.259 | dub −0.351 ~ german +0.668 | **39** |
| `tempo` | `danceability` | −0.050 | hardcore −0.427 ~ sleep +0.484 | **20** |
| `duration_ms` | `instrumentalness` | +0.124 | anime −0.450 ~ techno +0.542 | **43** |
| `loudness` | `valence` | +0.280 | dub −0.309 ~ german +0.538 | 10 |
| `loudness` | `popularity` | +0.050 | sleep −0.406 ~ world-music +0.456 | 50 |
| `duration_ms` | `danceability` | −0.073 | groove −0.388 ~ hardcore +0.356 | 22 |

## 3. 해석

- **`loudness`↔`energy`는 전체·장르 구분 모두에서 가장 견고한 관계**(r=0.762, 앞선 리포트에서도 둘 다 η² 상위권) — "라우드니스가 곧 에너지 판단의 핵심 원료"라는 가설을 뒷받침한다. 이 관계는 아마 장르별로도 안정적일 것(변동성 표에 top8에 없음 = 표준편차가 작다).
- **`loudness`↔`acousticness`/`instrumentalness`는 방향은 항상 일관(음수)되지만 세기가 장르마다 크게 다르다**(피아노 장르에서 가장 강함 −0.80/−0.87, happy/power-pop 장르에서 거의 0). 피아노처럼 편성이 단순하고 다이나믹 레인지가 곧 어쿠스틱함을 대변하는 장르에서는 이 관계가 물리적으로 타당하지만, 혼합 편성 장르에서는 loudness만으로 acousticness/instrumentalness를 추정하기 어렵다는 뜻.
- **`loudness`↔`danceability`, `tempo`↔`danceability`, `duration_ms`↔`instrumentalness`는 전체 상관은 약한데 장르별로는 부호가 자주 뒤집힌다**(각각 114개 중 39·20·43개 장르에서 부호 반전). 이는 전형적인 **집계 역설(Simpson's paradox류)** 패턴 — 전체 데이터를 뭉치면 신호가 상쇄되어 "거의 무관"으로 보이지만, 장르 안에서는 뚜렷한(때로는 반대 방향의) 관계가 존재한다. 예: `tempo`↔`danceability`는 hardcore에서는 "빠를수록 춤추기 어렵다"(−0.43)이지만 sleep에서는 "빠를수록 춤추기 쉽다고 평가됨"(+0.48) — 장르 자체의 정의(예: sleep 장르는 애초에 느린 곡이 대부분이라 그 안에서의 상대적 템포 차이가 다른 의미를 가짐)에 좌우될 수 있다.
- **`popularity`는 어느 그룹과도 전체 상관이 약하지만(§2-1), 장르별로 보면 편차가 크다**(`loudness`↔`popularity`: sleep −0.41 ~ world-music +0.46). 즉 "무엇이 인기곡을 만드는가"는 전체 데이터셋 수준에서는 오디오 특성으로 설명되지 않지만, 특정 장르 내부에서는 라우드니스가 인기와 연관될 수도 있다는 정황 — 다만 표본 불균형(장르당 곡수 상이) 가능성도 배제 못 함.

## 4. 결론 및 제안 (Conclusion & Proposal)

**결론**:
1. 그룹 간 관계에서 가장 강하고 일관된 신호는 **`loudness`↔`energy`**(및 `loudness`↔`acousticness`/`instrumentalness`의 부호 일관성)다 — 저수준 변수 하나(loudness)가 여러 합성 변수의 핵심 원료로 쓰였을 가능성을 시사한다.
2. **`popularity`(모델예측 그룹)는 오디오 저수준/합성 변수 어느 것과도 전체 수준에서 유의미한 선형관계가 없다** — 오디오 분석만으로는 인기도를 설명할 수 없다는 점이 이번 분석에서도 재확인됐다.
3. **여러 쌍(loudness-danceability, tempo-danceability, duration-instrumentalness 등)은 전체 상관이 약해 보이지만 장르 내부에서는 방향이 자주 뒤집힌다** — "전체 상관이 약하다"는 결론만으로 두 변수가 무관하다고 단정하면 안 된다는 방법론적 시사점.

**우리 프로젝트(EMOI-MAP)에 대한 제안(적용은 아직 하지 않음)**:
- [report-genre_audio_features.md](report-genre_audio_features.md)의 제안대로 `acousticness_proxy`/`instrumentalness_proxy`/`energy_proxy`를 재정의해 [side-project/genre-features/](../genre-features/README.md)에서 이미 밴드별 분포를 관찰했다. 이번 분석은 거기 더해, **"밴드(장르 대리) 단위로 상관관계를 볼 때 전체 상관과 다르게 나올 수 있다"**는 점을 명심할 필요가 있음을 보여준다 — 예컨대 우리 프록시 코퍼스에서 `rms`(loudness 대응)와 `acousticness_proxy`의 전체 상관이 약하게 나오더라도, 밴드별로 쪼개보면 (morfonica처럼 바이올린이 뚜렷한 밴드에서) 훨씬 강한 관계가 숨어있을 수 있다.
- 다음에 밴드별 프록시 상관을 다시 볼 때는 **전체 상관 하나만 보지 말고, 이 스크립트처럼 밴드별로 쪼갠 상관계수도 함께 확인**하는 것을 권장한다(방법은 이미 검증됨 — `scatter_pairwise.py`의 `genre_correlation_bar()` 로직을 밴드 단위로 그대로 재사용 가능).
- 여전히 EMOI-MAP 축(x=timbre/contrast, y=valence/mode) 자체에는 이번 분석으로도 변경을 제안하지 않는다 — 손라벨 상관검정 이전 단계의 분포/관계 관찰일 뿐.

## 5. 산출물

- `scatter_pairwise.py` — 분석 스크립트(pandas/matplotlib/scipy, base env)
- `fig/scatter-pairwise/*_overall.png` — 55쌍 전체 hexbin 산점도
- `fig/scatter-pairwise/*_by_genre.png` — 55쌍 장르별 상관계수 막대그래프(장르는 r 기준 정렬, 점선=전체 r)
- `fig/scatter-pairwise/_overall_correlation_summary.csv` — 55쌍 전체 r/p, |r| 내림차순
- `fig/scatter-pairwise/_genre_correlation_variability_summary.csv` — 55쌍 장르별 r 평균/표준편차/최소·최대/부호반전 수, 표준편차 내림차순
