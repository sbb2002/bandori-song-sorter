# EMOI-MAP 7항목 밴드별 분포 분석

세션 36 인계 작업(`docs/working/HANDOFF.md`). ave_mujica(고딕메탈)가 재생 펄스에서 acoustic
채널로 48%나 분류되는 걸 사용자가 육안으로 지적한 것을 계기로, EMOI-MAP이 쓰는 7항목(x축
`contrast`·y축 `mode_score`·`harmonic_ratio`·밝기군[`centroid`/`rolloff`/`zcr`/`flatness`]·
`flux`·`energy`·`bpm`, 실제 raw 컬럼 10개)의 밴드별 분포를 확인해, 같은 오작동이 다른 밴드에도
있는지 검증했다.

## 데이터·방법
**오디오 재추출 불필요** — 이미 레포에 커밋된 두 산출물만 사용:
- `side-project/genre-features/song_features_with_proxies.csv`(전곡 660, `contrast`·
  `mode_score`·`harmonic_ratio`·`centroid`·`rolloff`·`zcr`·`flatness`·`flux` 보유)
- `src/content/cluster/audio_map.json`(`energy`·`bpm`·펄스 `shape` — `add_energy.py`/
  `add_pulse_shape.py` 산출, `shape`는 세션 35에서 이미 계산된 채널 분류 결과를 그대로 재사용)

`songs_full.csv`의 (band,song)→idx로 두 소스를 조인(제목 중복 2쌍 대응, `add_pulse_shape.py`와
동일 방식). 660곡 전부 매칭. 스크립트: `analyze_features.py`(base env — pandas/matplotlib만
필요, librosa 불필요).

## 결과 — 밴드별 펄스 채널 분포(%, acoustic 내림차순)

| band | neutral | acoustic | bright | shimmer | n | 장르 성향(참고) |
|---|---:|---:|---:|---:|---:|---|
| morfonica | 7.0 | **84.2** | 8.8 | 0.0 | 57 | 바이올린/현악 편성 |
| mygo | 24.4 | **63.4** | 4.9 | 7.3 | 41 | 얼터너티브락 |
| ave_mujica | 31.0 | **48.3** | 10.3 | 10.3 | 29 | 고딕메탈 |
| roselia | 35.6 | 32.2 | 23.3 | 8.9 | 90 | 심포닉메탈/하드록 |
| poppin_party | 37.4 | 25.2 | 21.7 | 15.7 | 115 | 팝펑크 |
| various_artists | 40.0 | 20.0 | 0.0 | 40.0 | 5 | 혼성(장르 대리변수 아님) |
| pastel_palettes | 21.6 | 18.9 | 40.5 | 18.9 | 74 | 팝 |
| afterglow | 37.5 | 18.1 | 16.7 | 27.8 | 72 | 락 |
| hello_happy_world | 30.6 | 11.1 | 6.9 | 51.4 | 72 | 팝 |
| raise_a_suilen | 27.5 | 10.0 | **57.5** | 5.0 | 80 | 하드록/일렉트로닉 |
| mugendai_mutype | 17.4 | 8.7 | 26.1 | 47.8 | 23 | 팝 |
| millsage | 100.0 | 0.0 | 0.0 | 0.0 | 1 | 미상(n=1, 신뢰 불가) |
| ikka_dumb_rock | 0.0 | 0.0 | 100.0 | 0.0 | 1 | 락(n=1, 신뢰 불가) |

전체 그림: `fig/{contrast,mode_score,harmonic_ratio,centroid,rolloff,zcr,flatness,flux,energy,bpm}_violin.png`
(밴드 중앙값 기준 정렬 바이올린 플롯) · 원본 표 = `shape_distribution_by_band.csv`.

## 핵심 발견 — **ave_mujica보다 mygo가 더 심함**

**당초 발견한 ave_mujica(48.3%)보다 mygo(63.4%)가 실제로 더 극단적**이다. n=1 밴드 2곳을 빼면
밝기군 원시 중앙값 순위(낮을수록 "어두운 믹스"):

| band | harmonic_ratio | centroid | rolloff | zcr | flatness |
|---|---:|---:|---:|---:|---:|
| morfonica | 0.832 | 2780 | 5741 | 0.119 | 0.028 |
| **mygo** | 0.775 | **2450** | **5283** | **0.104** | **0.024** |
| ave_mujica | 0.746 | 2587 | 5307 | 0.117 | 0.030 |
| roselia | 0.719 | 2682 | 5636 | 0.125 | 0.033 |
| raise_a_suilen | 0.720 | 2890 | 6121 | 0.138 | 0.043 |

**mygo·ave_mujica 둘 다 밝기군(centroid/rolloff/zcr/flatness) 중앙값이 코퍼스에서 가장 낮은
축**에 속한다 — 즉 **믹스 자체가 어두운(저음 위주) 밴드는 장르와 무관하게 acoustic 채널로 쏠린다**는
게 세션 36 가설을 넘어 **일반적 패턴**임을 확인. 채널 판정이 `acoustic=z(harmonic_ratio)` vs
`bright=mean z(밝기군)` **상대 비교**라서, bright가 낮으면 harmonic_ratio가 특별히 높지 않아도
acoustic이 기본 승리하는 구조적 문제다(세션 36에서 세운 가설과 정확히 일치, mygo로 재확인).

## 양성 대조군(기대와 일치하는 사례)
- **raise_a_suilen 57.5% bright** — 하드록/일렉트로닉 성향과 정확히 일치. 밝기군 중앙값도
  코퍼스 상위권(centroid 2890·rolloff 6121·zcr 0.138·flatness 0.043 전부 최고 근접).
- **morfonica 84.2% acoustic** — 바이올린/현악 편성과 일치(가장 높은 harmonic_ratio 0.832).
- 채널 로직 자체가 "완전히 틀린" 건 아니고, **믹스 밝기가 왜곡 요인으로 강하게 개입**한다는 게 정확한 진단.

## 후속 실험 — Demucs other 스템 재측정(가설 기각)
"밝기군이 낮은 건 어두운 믹스가 화성악기 음색을 가려서다, other 스템(보컬·드럼·베이스 제외)만
측정하면 완화될 것"이라는 가설을 11곡(mygo 4·ave_mujica 4·morfonica 대조군 3)으로 직접 검증 —
**결과는 정반대**: other 스템에서 밝기군이 11곡 전부(대조군 포함) 오히려 하락, ave_mujica·mygo는
harmonic_ratio까지 더 올라 acoustic 쏠림이 완화가 아니라 **악화**됨. 드럼 심벌·보컬 치찰음이 믹스
고주파 에너지의 상당 부분을 차지하고 있었던 것으로 추정. 상세 = [report-other-stem-experiment.md](report-other-stem-experiment.md).

## 다음 결정(사용자 미확정)
`add_pulse_shape.py`의 채널 판정 규칙(z-score 최댓값, `docs/working/HANDOFF.md` 참조) 조정 여부:
- (a) 그대로 유지 — "완벽한 장르 판별기"가 아니라 "음색 시그니처 시각화"일 뿐이라 수용.
- (b) bright 그룹에 밴드 간 믹스 밝기 편차를 보정(예: 밴드별이 아니라 곡별 상대값 대신 절대
  임계치 병행, 또는 loudness-normalize 후 재계산).
- (c) neutral 판정 임계값(현재 최댓값−2등 <0.4)을 조정해 acoustic 과다분류 완화.
- (d) ~~other 스템 재측정~~ — **실험 결과 기각**(위 절 참조). vocals만 뺀 스템(drums+bass+other
  합성)은 미검증 후속 후보.

## 파일
- `analyze_features.py` — 7항목 밴드별 분포·펄스 채널 분포 재현 스크립트.
- `shape_distribution_by_band.csv` — 밴드별 채널 분포 원본 표.
- `fig/*.png` — 10개 원시 피처 바이올린 플롯.
- `extract_other_stem_features.py` · `compare_stem_vs_mix.py` · `plot_stem_comparison.py` ·
  `other_stem_features.csv` · `stem_vs_mix_comparison.csv` — other 스템 실험(위 절), 상세는
  [report-other-stem-experiment.md](report-other-stem-experiment.md).
