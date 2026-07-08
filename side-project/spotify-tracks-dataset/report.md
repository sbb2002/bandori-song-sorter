# Spotify Tracks Dataset — 장르별 오디오 피처 분석 리포트

## 1. 방법 (Method)

**데이터셋**: [Spotify Tracks Dataset](data/dataset.csv) — 114,000행 · 114개 장르 · 21컬럼. 컬럼 설명은 [metadata.md](data/metadata.md) 참고.

**전처리**: `distribution.py`의 `cleanse_dataset()` — 결측치 행, `duration_ms == 0`인 행 제거.

**변수 3분류**: 오디오 분석 파이프라인 관점에서 컬럼을 아래처럼 분류했다(근거는 [metadata.md](data/metadata.md) 하단 참고).

| 그룹 | 변수 | 설명 |
|---|---|---|
| 1. 저수준(low-level) | `duration_ms`, `key`, `mode`, `loudness`, `tempo`, `time_signature` | 신호처리로 파형에서 직접 측정 |
| 2. 합성(composite/고수준) | `danceability`, `energy`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence` | 저수준 값들을 조합한 서술적 지표 |
| 3. 모델 예측 | `popularity`, `track_genre` | 오디오 특성이 아닌 별도 알고리즘/모델 산출값 |

**분석**: `violin_genre_vs_audiofeats.py` — 위 14개 변수(장르 자체·메타데이터 제외) 각각에 대해:
1. `track_genre`로 그룹핑 → 그룹 중앙값 기준 오름차순 정렬
2. 바이올린 플롯을 `fig/violin-genre_vs_audiofeats/`에 변수별로 저장
3. `scipy.stats.f_oneway`로 114개 장르 그룹 간 one-way ANOVA 수행
4. η²(= SS_between / SS_total)로 "장르가 이 변수의 분산을 얼마나 설명하는가"를 정량화

결과는 `fig/violin-genre_vs_audiofeats/_genre_anova_summary.csv`에 저장.

## 2. 결과 (Results)

η² 기준 정렬(장르 구분력이 강한 순):

| 변수 | 그룹 | η² |
|---|---|---:|
| `acousticness` | composite | 0.488 |
| `energy` | composite | 0.455 |
| `instrumentalness` | composite | 0.452 |
| `loudness` | low-level | 0.451 |
| `speechiness` | composite | 0.442 |
| `danceability` | composite | 0.415 |
| `valence` | composite | 0.304 |
| `popularity` | model | 0.254 |
| `duration_ms` | low-level | 0.165 |
| `liveness` | composite | 0.152 |
| `tempo` | low-level | 0.085 |
| `time_signature` | low-level | 0.067 |
| `mode` | low-level | 0.063 |
| `key` | low-level | 0.005 |

모든 변수의 ANOVA p-value는 사실상 0(극도로 유의)이지만, 장르가 실제로 설명하는 분산의 크기(η²)는 변수별로 크게 다르다.

**해석 포인트**
- 상위 6개 중 5개가 **합성(composite) 변수** — 저수준 원본 신호값보다 장르 구분에 훨씬 유리하다. 애초에 danceability/energy 등이 장르 판별에 쓰이도록 설계된 지표라는 점과 일치.
- `loudness`만 저수준인데도 상위권(energy와 유사한 패턴) — 사실상 energy의 raw 대응물로 보인다.
- `key`(0.005)·`mode`(0.063)·`time_signature`(0.067)는 장르와 거의 무관 — 조성이나 박자는 장르를 가르는 신호가 아니다.
- `popularity`(비-오디오 변수, η²=0.254)도 장르별로 꽤 갈린다 — 특정 장르가 구조적으로 재생수가 높게 몰려있을 가능성.
- `duration_ms`(0.165)·`tempo`(0.085)는 예상보다 구분력이 약함 — 장르별 곡 길이·템포 분포가 서로 많이 겹친다.

## 3. 결론 및 제안 (Conclusion & Proposal)

**결론**: 장르(≈편성/스타일)를 가장 잘 가르는 축은 "질감/음향적 특성을 조합한 합성 변수"(`acousticness`·`energy`·`instrumentalness`류)다. 이는 우리 EMOI-MAP 프로젝트의 코퍼스(대체로 J-rock이지만 바이올린을 채용하는 밴드, 헤비메탈, 일렉트로 계열 믹스가 섞여 있음)에서 아직 시도하지 않은 "편성/음색 다양성" 축 가설과 맞닿아 있다.

다만 Spotify의 `acousticness`/`energy`/`instrumentalness`는 **블랙박스 ML 모델 출력**이라 값 자체를 그대로 이식할 수 없다(`metadata.md`에도 산출 공식 힌트가 없음). 대신 EMOI-MAP이 이미 갖고 있는 자체 신호처리 도구로 유사 개념을 우리 손으로 재정의해야 한다.

**제안(다음 단계 — 이번 문서에는 계획만, 실제 추출은 별도 작업)**

1. Spotify 변수를 그대로 가져오지 않고, 우리 파이프라인의 실제 신호처리 산출물로 유사 개념을 재정의:
   - **acousticness-proxy** 후보 = `harmonic_ratio`(HPSS 기반, `src/tools/cluster/phasec_features.py`) + `flatness`(낮을수록 tonal/acoustic) 조합
   - **instrumentalness-proxy** 후보 = Demucs 보컬분리 기반 vocal/mix 에너지 비율 또는 `voiced_frac`(`src/tools/cluster/perceptual_features.py`)
   - **energy-proxy**는 이미 존재(`rms`·`rms_std`·`crest`·`onset_rate`, Phase C에서 arousal 후보로 다룸) — 장르 구분 용도로는 별개 목적이니 재검토 가치 있음(단, arousal 독립축으로는 이미 기각됨: [emotion-axes-extraction.md](../../docs/research/emotion-axes-extraction.md))
2. EMOI-MAP 축 변경 전에, 먼저 이 프록시들을 우리 로컬 오디오(현재 로컬 샘플 ≈30곡, 분포 테스트용으로 충분)에 적용해 **분포만 관찰** — 바이올린 밴드 vs 헤비메탈 vs 일렉트로 믹스에서 실제로 값이 갈리는지 확인한다. `phasec_features.py`의 `compute()`가 새 컬럼을 추가할 자연스러운 위치이며, `harmonic_ratio`의 HPSS-45s-excerpt 패턴을 acousticness proxy 템플릿으로 재사용할 수 있다.
3. 분포가 의미 있게 갈리면 그 다음에야 손라벨 상관검정(`phasec_correlate.py` 방식) 또는 새 축 도입 여부를 별도로 판단한다.

이번 사이드 프로젝트 분석은 여기까지 — EMOI-MAP 소스에는 변경을 가하지 않았다.
