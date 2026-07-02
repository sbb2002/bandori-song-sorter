## Fable-5 자문

- User
    '''
    [audio-map-fullscale.md 첨부]
    어제 어떤 프로젝트의 기능을 구현 중이었어. 이 문서에서 볼 수 있듯 음원 샘플을 활용해서 밴드 별 특성이 잘 나타나는 2d clustering map을 제작하려고 했어. 그러나 전체를 놓고 보았을 때 morfonica의 곡이 대체적으로 안맞는 경향이 보였어. 이 밴드의 특징으로는 기타, 베이스, 드럼, 보컬, 바이올린이 있는데, 그래서 그런지 음향학적 특징이 잘 안잡혔었던거 같아. mutype이라는 밴드도 morfonica 정도는 아니지만 일렉트로 사운드를 많이 쓰다보니 약간 안맞는 경향이 있었어.

    음향학적 특성을 2D로 분리했을 때 각 밴드의 특성이 잘 분리될 수 있도록 어울리는 음향학적 특성인 x, y축을 정의를 추천해줘.
    '''

- Fable-5
    '''
    핵심은 morfonica가 y 상단으로, mutype·RAS가 y 하단으로 **측정만으로** 분리된다는 것 — 잘 되면 `BAND_OVERRIDES` 큐레이션(morfonica dy+15)을 정량 근거로 대체하거나 축소할 수 있어요.

    ## 보조 후보 (feature bank)

    HPR 하나에 걸지 말고, 후보군을 만들어서 데이터로 고르는 걸 권합니다:

    | feature | 잡아내는 것 | morfonica | mutype | 비고 |
    |---|---|---|---|---|
    | HPR (log H/P 에너지비) | 지속음 vs 타격 | ↑ | ↓ | 1순위, contrast와 저상관 기대 |
    | 대역 한정 HPR (1.5–6kHz) | 바이올린 음역의 지속 토널 에너지 | ↑↑ | ↓ | 베이스·킥 간섭 배제, 바이올린 민감도↑ |
    | spectral flatness (2–8kHz) | 노이즈성 (신스·디스토션 ↑, 현악 ↓) | ↓ | ↑ | contrast와 상관 높을 위험 — 검증 필수 |
    | sub-bass ratio (<120Hz) | EDM 킥·신스베이스 비중 | ↓ | ↑ | mutype·RAS 전용 검출기 성격 |
    | onset 규칙성 / pulse clarity | 퀀타이즈된 전자 리듬 | 중 | ↑ | librosa onset envelope 자기상관 |
    | centroid 4–8Hz 변조 에너지 | 비브라토 (바이올린 시그니처) | ↑ | — | 구현 난이도 높음, 예비 후보 |

    ## 선정 프로토콜 — 감이 아니라 데이터로

    이미 97곡 캐시가 있으니 확대 전에 여기서 검증하는 게 순서상 좋아요:

    1. 97곡에 대해 위 feature 전부 계산 (기존 contrast, mode 포함)
    2. feature별 **밴드 간 분리력** 랭킹 — `scipy.stats.f_oneway`의 F값 (밴드 간 분산 / 밴드 내 분산)
    3. 상위 feature 중 곡 단위 상관 |r| < 0.4인 쌍을 후보 축으로 선정 (contrast × flatness처럼 겹치는 쌍 자동 배제)
    4. 후보 2D 각각에 대해 `silhouette_score(X_2d, band_labels)`로 최종 비교 — 현행 contrast × mode의 silhouette을 베이스라인으로 삼으면 개선 여부가 숫자로 나옴

    이러면 morfonica override 필요 여부, mode_score를 정말 버려도 되는지까지 한 번에 정량 확인됩니다.

    ## 구현 메모

    ```python
    import librosa, numpy as np

    S = np.abs(librosa.stft(y))
    H, P = librosa.decompose.hpss(S, margin=3.0)  # margin↑ = 분리 엄격
    # 전대역 HPR
    hpr = np.log10((H**2).sum() / ((P**2).sum() + 1e-10))
    # 대역 한정(1.5–6kHz) 버전
    freqs = librosa.fft_frequencies(sr=sr)
    band = (freqs >= 1500) & (freqs <= 6000)
    hpr_band = np.log10((H[band]**2).sum() / ((P[band]**2).sum() + 1e-10))
    ```

    전곡 통계라 60초 크롭 불필요한 건 기존과 동일하고, z-score 직접좌표 방식도 그대로 쓰면 돼요. `margin` 파라미터는 3.0 근처에서 시작해서 morfonica/RAS 극단 곡 몇 개로 튜닝하면 됩니다.

    주의할 점 두 가지. 첫째, mode_score를 y에서 내리면 "위=밝음/아래=어두움"이라는 현재 맵의 의미론이 "위=지속·토널/아래=타격·전자"로 바뀌므로 `_clDraw()`의 포커스 축선 라벨도 같이 수정해야 해요. 밝음 의미를 꼭 유지하고 싶다면 mode를 y에 남기고 x를 교체하는 조합도 프로토콜에서 같이 비교해볼 수 있는데, contrast(r=−0.81)를 버리는 비용이 커서 추천 순위는 낮습니다. 둘째, 이보다 더 공격적인 대안으로 밴드 라벨을 직접 쓰는 supervised LDA 2축도 있어요 — 밴드 분리는 수학적으로 최대화되지만 축 해석성이 떨어지고 신규 밴드 추가 시 재학습이 필요해서, "소리로 탐색하는 도구"라는 맵의 성격에는 해석 가능한 feature 축이 더 맞다고 봅니다.
    '''

---

## 검토 의견 (Claude, 2026-07-02) — fable-5 제안 vs 현행 축

> 검토 자료: 현행 채택본([audio-map-axes.md](audio-map-axes.md) §7.3, [../report/cluster-correlation/README.md](../report/cluster-correlation/README.md))
> + fable-5 핵심 주장을 **파일럿 28곡으로 직접 재검증**(기존 `axis_pilot_features.csv`).

### 전제 — 두 제안은 다른 목적을 최적화한다
- **현행 축**(x=contrast, y=mode)은 **지각 정렬**(사용자 손 라벨과의 상관, 밝음/거칢)로 검증·채택됨. v3에서 PCA(밴드 최대분리)를 **의도적으로 폐기**하고 "축=라벨 의미 일치" 원칙을 세운 결과다.
- **fable-5**는 오늘 "**밴드를 분리하는** 축"이라는 다른 질문에 답했고, `audio-map-fullscale.md`만 받아 **correlation 리포트(§7 mode 검정·독립성)를 못 본 상태**에서 조언했다. → "어느 쪽이 정확하냐"는 **목적에 따라 갈린다.**

### 결정적 사실 — fable-5의 1순위 HPR = 이미 계산된 `harmonic_ratio`
fable-5의 1순위 **HPR `log(H²/P²)`** 는 파일럿에서 이미 뽑은 `harmonic_ratio = H/(H+P)`(`tools/cluster/add_x_features.py:38`)와 **단조 변환 관계(동일 정보)**. 재추출 없이 28곡으로 주장 재검증:

**밴드별 harmonic_ratio 평균** (fable-5 예측: morfonica↑ / mutype·RAS↓)
```
0.803 morfonica ← 최상위 ✅  |  0.744 mutype  ← 중위 ❌ (예측 빗나감)
0.784 poppin    0.769 mygo  |  0.744 roselia    0.731 hello
0.768 ave                   |  0.713 RAS ← 하위2 △   0.702 pastel
                            |  0.648 afterglow ← 최하위(mutype 아님)
```
**밴드 분리력 F값**: contrast 4.31 · flatness 3.96 · **HPR 3.87** · centroid 3.74 · rolloff 3.72 · rms 2.89 · onset 2.60 · **mode 2.54** · tempo 1.16
**독립성**: r(HPR,contrast)=**+0.375**, r(mode,contrast)=+0.370(거의 동률·둘 다 임계선), r(HPR,mode)=+0.024(직교)

### 판정
| 기준 | 승자 | 근거 |
|------|------|------|
| **직관성**(사용자 체감) | **현행 mode** | "밝음↔어두움"은 즉시 이해·귀와 r=0.51 검증. HPR "지속·토널↔타격·전자"는 엔지니어 개념·지각 미검증 |
| **지각 정확도** | **현행 mode** | mode r=0.51 검증. full-band HPR≈harmonic_ratio는 valence +0.06 / acoustic −0.14로 이미 약함 |
| **밴드 분리력** | **fable-5 HPR** | F=3.87 > mode 2.54. 순수 분리력은 HPR 우위 |
| **morfonica override 대체** | **fable-5 HPR** | morfonica가 harmonic_ratio 최상위(0.803)로 **측정만으로 위로 뜸** → `BAND_OVERRIDES dy+15` 큐레이션을 실측으로 대체 가능 |
| **mutype 분리** | 둘 다 실패 | fable-5 "mutype↓" **데이터로 반증**(0.744 중위). HPR로도 안 풀림 |

**함정 2가지**: ① HPR은 contrast와 r=0.375로 mode(0.370)만큼밖에 독립적이지 않음 → y로 쓰면 F 상위(contrast·flatness·centroid·HPR)가 전부 같은 "밝기" 덩어리라 §7.1의 **1차원 붕괴 재발 위험**. contrast와 확실히 독립인 건 여전히 mode뿐. ② fable-5의 silhouette 프로토콜은 방법은 좋으나 **미실행 가설 단계**.

### 결론
1. **현행 축(x=contrast, y=mode) 유지** — 직관성·지각 검증·contrast 독립성 3면 우위, v3 원칙 부합.
2. **채택할 fable-5 조언 하나**: morfonica의 `BAND_OVERRIDES dy+15`(측정 아닌 큐레이션)를 **HPR 기반 실측 보정으로 격상**. morfonica harmonic_ratio 최상위(0.803)가 데이터로 확인됨 → y축을 안 바꾸고도 "morfonica 밝음" 근거를 큐레이션→실측으로 승격 가능. **지금 가장 실속 있는 개선.**
3. **y축을 HPR로 통째 교체는 비권장** — 직관성 상실 + mutype 미해결(예측 반증) + contrast와 1차원 붕괴 위험.
4. **미검정 유일 후보**: fable-5의 **band-limited HPR(1.5–6kHz, 바이올린 대역)** 은 full-band와 달리 아직 안 뽑아봄 → 이것만은 별도로 F값·독립성 확인할 가치 있음(morfonica 실측 보정의 후보로도).