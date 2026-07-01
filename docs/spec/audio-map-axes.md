# 음원맵 축 재정의 (v3) — 지각 기반 좌표축

> 상태: **설계 확정, 미구현**. 다음 세션이 이 문서대로 구현. 상위 작업 목록은 [../HANDOFF.md](../HANDOFF.md) §2.
> 배경 실험(왜 가사로는 밴드가 안 갈리는지 등)은 [../report/cluster_experiment.md](../report/cluster_experiment.md).

## 0. 왜 재정의하나 (현 축의 괴리 진단)

현 `cluster/audio_map.json`의 x·y는 **두 겹**으로 되어 있고, 이게 사용자 체감과 어긋난다:

- **(A) 축 자체** = 밴드 중심점 13개를 71차원 librosa 특징공간에서 **가장 넓게 벌리는 PCA 방향** 2개. 추상적("밴드 최대분리")이라 "고음"·"거침" 같은 의미가 내재돼 있지 않음.
- **(B) 축 이름** = 사후에 `axis_labels()`가 5개 저수준 DSP 특징(tempo·centroid·energy·rolloff·zcr)과 상관 내서 **가장 상관 높은 단 하나**로 라벨링. 실측 x=rolloff(r=**−0.66**), y=zcr(r=**+0.61**) → **축의 40~56%는 그 라벨로 설명 안 됨**(라벨이 축을 과장).
- 게다가 feature 자체가 **전체 믹스 DSP 프록시**(rolloff=보컬 음고 아님·전체 스펙트럼 무게중심), **16kHz 로드로 8kHz 위 절단**, **60초 한 구간**이라 사람 귀(보컬 음역·정서)와 계통적으로 어긋남.
- 결과 예: hello_happy_world(x=+23, y=+15.6)·pastel_palettes(x=+12, y=+17.4)가 "저음·거침" 사분면에 위치 → 사용자 체감("고음·부드러움/밝음")과 정반대. (silhouette≈0 = 밴드가 실제로 겹쳐 있음도 원인.)
- 큰 원 = 그 밴드 곡들의 **중심점**(특징벡터 평균의 PCA 투영)은 맞음.

**해결 원칙 (사용자 확정)**: PCA 추상축이어도 상대 차이만 보이면 OK. **단, 축이 가리키는 값과 라벨 의미가 달라선 안 됨.** → PCA를 semantic 축에서 빼고 **축 자체를 지각 feature로 직접 계산**한다(x=음고합성, y=정서). 그러면 라벨=축이 정의상 성립(r=1.0). 기존 PCA 지도는 폐기하거나 "밴드 지문/식별" 별도 뷰로만 남기고 라벨을 약화한다.

---

## 1. 범위 (Scope) — 확정

- **1차: 밴드당 상한 ~40곡 샘플** (~300곡). 8개 실밴드가 이미 n≥40이라 중심점이 균형·신뢰성 확보(중심극한정리 n≥30 충족). 캐시 ~1.7GB. **축 재정의·검증은 여기서.**
- **2차: 전곡 660** (탐색 도구화). 이때 **렌더 최적화 동반**(660점은 빽빽·느림): ECharts `large:true`+`progressive`, 심볼 축소·투명도, 밴드 클릭 시에만 강조/나머지 흐리기, 줌 레벨별 다운샘플.
- 밴드별 고유 곡수(dedup, 실측 2026-07-01, 총 660):

  | 밴드 | 곡 | 밴드 | 곡 |
  |------|---:|------|---:|
  | poppin_party | 115 | morfonica | 57 |
  | roselia | 90 | mygo | 41 |
  | raise_a_suilen | 80 | ave_mujica | **29** |
  | pastel_palettes | 74 | mugendai_mutype | **23** |
  | afterglow | 72 | etc/ikka/millsage | 5/1/1 |
  | hello_happy_world | 72 | | |

  → 캡40 적용 시 8밴드=40곡, ave(29)·mugendai(23)는 전곡, **etc·ikka·millsage(≤5곡)는 중심점 생략·점만**.

---

## 2. X축 — [저음/고음 곡] : 확정

**보컬 음역 + 세션 밝기를 합성**. 가중합 **f0 70% + spectral centroid 20% + rolloff 10%**(상세 기준은 §4 부록 가이드라인).

구현 정제(확정):
1. **Peak f0 = 절대 최댓값이 아니라 유성음 f0의 상위 백분위(90~95p)** — 절대 max는 f0 추출 옥타브 오류에 취약. voicing 신뢰도 임계 + median filter로 옥타브 점프 제거.
2. BanG Dream은 사실상 **전곡 여성 보컬** → 남/여 임계 분기 불필요. 연속 f0를 **데이터셋 전체에서 정규화**(절대 Hz 임계 없이 상대 스프레드).
3. **70/20/10은 단위가 다르므로** f0·centroid·rolloff를 각각 **z-score 정규화 후 가중합** → x좌표.
4. (엣지) 순수 연주곡 = 보컬 f0 결측 → 70% 항 결측 → centroid/rolloff만으로 배치하거나 중립 처리.

파이프라인: **Demucs(보컬 분리) → CREPE 또는 pYIN(f0) → 95p** + 믹스 **centroid/rolloff** → 각 정규화 → 가중합.

⚠️ **현 오디오 캐시(60초·16kHz)로는 부족** → **48kHz 재추출 + 더 긴 구간(또는 후렴 탐지)** 필요. 16kHz는 나이퀴스트 8kHz라 centroid/rolloff 상단(가이드라인의 12~16kHz)이 잘리고, 60초 한 구간은 후렴 정점을 놓칠 수 있음. **현 캐시 폐기·재빌드 승인됨.**

---

## 3. Y축 — [정서/거칢] : 후보3 우선

세 후보는 **같은 축의 측정법이 아니라 서로 다른 y축**이다. 우선순위 확정: **후보3 → (폐기 시) 후보1·2**.

### 후보3 (우선) — 오디오 기반 정서(valence)
- 의미: **밝음/희망 ↔ 어두움/애절**(행복↔슬픔). 가사 없이 오디오만.
- 핵심 신호: **장/단조(mode)** (음악 정서의 최강 단일 단서) + 보조(예: 화성 밝기, 템포·에너지).
- 장점: **가사 수집 불필요**, x와 동질(둘 다 음향), 300·660 자동 스케일, 사용자가 원한 "정서" 유지.
- 리스크: mode(장·단조) 오디오 추정은 오류가 있음 → **§5 검증 필수**.

### 후보1 (후순위) — 가사 감성분석
- 의미: 가사 내용 긍정/부정을 연속값으로.
- **결정적 장애물(데이터)**: 곡별 감성 = 곡별 가사 필요. **이 장치엔 가사 0개**(`assets/lyrics/<band>.md`는 gitignore, 템플릿만 존재). 템플릿=TOP10뿐이라 **캡40(~300곡)은 ~200곡분 가사 수작업 수집** 선결. 밴드 합산 `wordcloud/<band>.yaml`로는 곡별 분해 불가.
- 자원: `tools/wordcloud/senti_lexicon.yaml`(키워드 극성 +2~−2, 122개, 한글 기준). 파이프라인 JP가사→명사→KO번역→사전 매칭(손실 있음). 연주곡 결측.
- 축 성격: x(음향)과 **이질**(음향×의미) — 대비 콘텐츠로는 오히려 흥미로울 수 있으나 데이터 장벽이 큼.

### 후보2 (후순위) — 음색 왜곡/노이즈
- 의미: 매끄러운 ↔ 거친 **소리 질감**(디스토션·노이즈).
- 측정: **spectral flux · inharmonicity · roughness(dissonance) · flatness**. 오디오만, 견고, 스케일 O. RAS류 잘 설명.
- 한계: "정서"가 아니라 "소리 거칢" — 사용자가 원한 것과 다른 축.
- (참고) 원래 사용자 가설이던 "음악적 긴장/복잡도(리듬 변칙+모드 어둠+코드 복잡)"는 mode/코드 추정 난도로 **후순위 보류**.

---

## 4. 부록 — X축 참고 가이드라인 (사용자 제공, 원문 보존)

```
# [Technical Reference] Audio Classification Guideline: Pitch & Brightness Spectrum

## 1. Overview
This document defines the criteria and methodologies for classifying music into a 1-dimensional spectrum ranging from **Low-pitched/Dark (저음 곡)** to **High-pitched/Bright (고음 곡)**. To ensure human-like perception accuracy, the LLM must synthesize both **Vocal Melodic Pitch (F0)** and **Instrumental Timbral Semantics (Spectral Features)**.

## 2. Key Analytical Dimensions & Metrics

### A. Vocal Fundamental Frequency (Peak f0) — Primary Metric (Weight: 70%)
Human listeners classify a song as "high-pitched" primarily based on the vocal climax.
*   Analysis Method: Extract the fundamental frequency (f0) sequence of the vocal track. Do not rely solely on the global average; isolate the **Peak f0 (Highest Note) during the chorus/climax**.
*   Thresholds (Standard Pop/Rock tuning):
    *   High-pitched (고음): Male vocals exceeding G4 (~392 Hz) or Female vocals exceeding D5 (~587 Hz).
    *   Low-pitched (저음): Male vocals remaining below C4 (~261 Hz) or Female vocals remaining below G4 (~392 Hz).

### B. Spectral Centroid (Timbral Brightness) — Secondary Metric (Weight: 20%)
Represents the "center of mass" of the power spectrum. Measures how bright/heavy the overall instrumentation is.
*   High Spectral Centroid: high density of high-frequency energy (hi-hats, sharp synths, bright J-Rock/Power Metal overtones). ~3 kHz–8 kHz+.
*   Low Spectral Centroid: heavy, dark, bass-driven (808 sub-bass, down-tuned 7-string, dark lo-fi). ~500 Hz–1.5 kHz.

### C. Spectral Roll-off (High-Frequency Boundary) — Auxiliary Metric (Weight: 10%)
Frequency below which ~85–95% of total spectral energy lies. Marks the upper boundary of the song's sonic space.
*   High Roll-off: cutoff extends deep into upper register (~12 kHz–16 kHz): crisp, airy, wide-open mix.
*   Low Roll-off: cutoff drops heavily (below 4 kHz): muted, warm, heavily low-passed.

## 3. Hybrid Classification Framework (Edge Cases)

| Vocal Pitch (f0) | Spectral Centroid / Roll-off | Final Spectrum Classification | Contextual Description & Examples |
| :--- | :--- | :--- | :--- |
| High (Climax Screaming/Belt) | High (Bright/Sharp) | Extreme High-pitched (초고음) | Fast J-Rock, Power Metal, High-tempo Synthpop with soaring vocals. |
| High (High-pitched Vocal) | Low (Heavy/Dark Bass) | Mid-High (Heavy High) | Dark Trap/Hip-hop or Djent Metal, high female/hyperpop vocal over massive sub-bass. |
| Low (Deep Baritone/Whisper) | High (Acoustic/Airy/Crisp) | Mid-Low (Bright Low) | Deep acoustic folk or bossa nova, crisp guitar plucking, bright shimmering percussion. |
| Low (Deep Vocal/Rap) | Low (Muffled/Warm) | Extreme Low-pitched (초저음) | Lo-Fi Hip-hop, Doom Metal, deep R&B with heavily filtered arrangements. |

## 4. LLM Reasoning Protocol
1.  Identify Vocal Peak: max vocal register (explicit indicators like "3옥타브" / peak notes).
2.  Evaluate Instrumentation/Genre: map genre's typical spectral signature (J-Rock=High Centroid, Lo-Fi=Low Roll-off).
3.  Synthesize into 1D Spectrum: place by tension between Vocal Pitch and Instrumental Brightness. If vocal high but instrumentation heavy, pull final coordinate toward center.
```

---

## 5. 검증 계획 (어느 y축이든 채택 전 선행)

feature 선택이 추측이 아니라 근거가 되도록, **사용자 손 라벨 대조**:
1. 사용자가 곡 20~30개에 **고음/저음**·**정서(밝음/어두움)**(또는 거침/부드러움)을 1~5 척도 또는 상대순위로 라벨.
2. 후보 feature들을 계산해 **손 라벨과 상관(피어슨/스피어만)** 확인.
3. 사용자 귀와 실제 맞는 feature만 축으로 채택. (후보3이 낮으면 후보1·2로.)

---

## 6. 다음 세션 체크리스트

1. **[준비]** 다른 로컬에서 시작 — `git pull`, `.env`(`YOUTUBE_API_KEY`)는 장치별 비커밋, node 설치 확인.
2. **[매니페스트]** `build_audio_map.py`에 `--manifest`/캡 인자 추가 → `data/*.yaml`에서 밴드당 40곡 샘플 생성(dedup=vid).
3. **[재추출]** 48kHz·긴 구간(또는 후렴 탐지)로 오디오 캐시 재빌드(현 60s·16kHz 폐기).
4. **[x축]** Demucs→f0(95p)+centroid/rolloff→정규화 가중합(70/20/10).
5. **[y축]** 후보3(오디오 정서/mode) 프로토타입 → §5 검증.
6. **[좌표]** PCA 대신 x·y = 지각 feature 직접(축=라벨). `audio_map.json` 스키마·`renderCluster` 라벨 갱신.
7. **[검증셋]** 사용자에게 20~30곡 손 라벨 요청.
8. (선택) 구 PCA/`keywords_2d.json`/`build_embeddings.py` 폐기 결정.
