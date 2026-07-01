# 음원맵 축 재정의(v3) — 후보 feature ↔ 사용자 손 라벨 상관분석 보고서

> spec [../../spec/audio-map-axes.md](../../spec/audio-map-axes.md) §5 "검증 계획"의 실행 결과.
> **후보 지각 feature가 사용자의 귀(주관 손 라벨)와 실제로 정렬되는지**를 상관으로 검증.
> 작성 2026-07-01 · 파일럿 브랜치 `feature/emoi-cluster-v2` · n=28곡.
>
> ⚠️ 라벨은 **사용자 1인의 주관 평가**(1~5 척도). 절대 기준이 아니라 "이 청자의 지각과
> 어떤 feature가 정렬되는가"를 본다. 판단은 |r|·부호·유의성(p)만 쓰고 과대해석하지 않는다.
>
> 📌 **1차(§0~6)에서 x축(f0)이 실패 → 2차 재검정([§7](#7-2차--x축-재정의-재검정))에서 확정.**
> **최종 채택 2D: x=spectral contrast(거칢↔매끄러움), y=mode(어두움↔밝음)** → `build_perceptual_map.py` 구현.

---

## 0. TL;DR

| 라벨 축 | spec 의도 feature | 결과 | 판정 |
|---------|-------------------|------|------|
| **pitch** (저↔고, x축) | 보컬 f0 95p + centroid + rolloff | **전부 r≈0** (f0_p95_semi r=+0.01) | ❌ **실패** |
| **valence** (어↔밝, y후보3) | mode_score(장/단조) | mode_score **r=+0.51** ✓, contrast +0.56 | ✅ **검증** |
| **rough** (매끄↔거침, y후보2) | flux/flatness/zcr/contrast | **contrast r=−0.81** ✓, flatness +0.59 | ✅ **강하게 검증** |

**핵심 3가지**
1. **x축(f0) 붕괴** — BanG Dream 전곡이 유사한 여성 보컬 음역(f0 median 64~71 semitone, ≈E4~B4)이라 **f0가 곡별 변별력이 없다.** 사용자의 "고음/저음" 지각은 보컬 기음과 무관.
2. **spec §2.1 "peak f0" 가설 반증** — 퍼센타일이 높을수록 상관이 **낮아짐**(median 0.37 > p90 0.23 > **p95 0.01**). 95p는 멜로디 정점이 아니라 샤우트·하모닉·옥타브오류를 포착.
3. **y축은 견고** — 특히 **spectral contrast**가 정서(밝음 +0.56)·거칢(−0.81) 양쪽을 지배. mode_score도 정서에서 유의(+0.51). spec이 불확실해하던 y축이 오히려 확정 가능.

> 요컨대 spec의 자신도가 **거꾸로**였다: 확신하던 x(f0)는 실패, 셋 중 고르라던 y는 강하게 성립.

---

## 1. 방법

- **표본**: `cluster/axis_labels_worksheet.csv`의 30곡(10밴드×3). 다운로드 실패 2곡(idx 11 ave_mujica『Ave Mujica』, 58 mygo『迷路日々』) 제외 → **n=28**.
- **손 라벨**(사용자, 1~5): `pitch_lo1_hi5`(저1↔고5) · `valence_dark1_bright5`(어1↔밝5) · `rough_smooth1_rough5`(매끄1↔거침5).
- **feature 추출**: `tools/cluster/perceptual_features.py`. **전곡**(60초 크롭 폐기, spec §2.1) 48kHz → **Demucs htdemucs 보컬분리** → 보컬 stem에서 pYIN f0(95p·90p·median), 믹스에서 mode(Krumhansl 장/단조)·centroid·rolloff·flatness·contrast·flux·zcr·rms·tempo.
- **상관**: `tools/cluster/axis_correlation.py` — 피어슨 r + 스피어만 ρ + p값, 라벨 축별 |r| 내림차순.
- **라벨 분산**(과소검정 주의): pitch sd**0.73**(2:2, 3:10, 4:14, 5:2 — 3~4에 집중) · valence sd0.99 · rough sd1.19. **pitch 라벨의 분산이 가장 좁아** x축 검정력이 근본적으로 약함(§5 한계).

### 선행 발견 — 믹스 f0는 못 쓴다 (Demucs 필요, spec §2 실증)
믹스에 pYIN을 걸면 보컬이 아니라 **베이스·기타에 락**된다(진단: median ≈110–115Hz, p95는 소수 이상치가 견인). 보컬분리 후에야 f0가 의미를 가짐:

| roselia『礎の花冠』 | p95 | median | voiced |
|---|---|---|---|
| mix f0 | 481Hz | ~110Hz (베이스) | 오염 |
| **vocal f0 (Demucs)** | 554Hz | **330Hz (E4)** | 76% (깨끗) |

→ 파일럿 28곡 전부 `f0_src=vocal`(분리 성공). 그럼에도 **아래 x축 결과는 실패** — 즉 f0 자체가 깨끗해도 이 코퍼스에선 변별력이 없다는 뜻(원인은 분리 품질이 아니라 음역 균질성).

---

## 2. 결과

### 2.1 pitch (x축) — ❌ 실패

| feature | pearson r | p | spearman ρ | p |
|---|---:|---:|---:|---:|
| mix_f0_p95_hz | +0.400 | 0.035 | +0.371 | 0.052 |
| f0_med_hz | +0.374 | 0.050 | +0.312 | 0.107 |
| f0_med_semi | +0.361 | 0.059 | +0.312 | 0.107 |
| f0_p90_hz | +0.234 | 0.231 | +0.165 | 0.400 |
| ★ centroid | −0.079 | 0.690 | −0.103 | 0.601 |
| ★ rolloff | −0.027 | 0.892 | −0.123 | 0.534 |
| ★ x_f0_cent_roll(합성) | −0.016 | 0.934 | −0.001 | 0.995 |
| ★ **f0_p95_semi** | **+0.008** | 0.966 | −0.003 | 0.988 |

(★ = spec 지정 후보) **어떤 것도 |r|≥0.5에 못 미침.** spec이 설계한 x축(f0 95p + centroid + rolloff 합성)은 **정확히 0 상관**.

**진단 — f0가 곡별로 평평하다** (pitch 라벨 오름차순):

| pit | 예시 | f0_med(semi) | f0_p95(semi) |
|---:|---|---:|---:|
| 2 | RAS HOWLING AMBITION | 66.6 | **79.1** (최상위!) |
| 3 | afterglow/mygo/poppin… (10곡) | 63.6–68.0 | 70.5–75.6 |
| 4 | hello/morfonica/pastel… (14곡) | 64.3–69.2 | 70.1–76.8 |
| 5 | mugendai / roselia Song I am. | 71.1 / 64.9 | 77.9 / 76.6 |

전 밴드 f0_med가 **64~71 semitone(≈E4~B4) 한 옥타브 안에 뭉쳐** 있다. 사용자가 "저음(2)"이라 들은 RAS의 f0_p95가 오히려 최상위(79). **원인 = BanG Dream은 전곡 여성 보컬·유사 음역** → 기음으로는 지각 음고를 못 가른다. 사용자의 "고음/저음"은 보컬 register가 아니라 **편곡·음색의 게슈탈트**로 추정.

**퍼센타일 역전**(median 0.37 > p90 0.23 > p95 0.01): 높은 퍼센타일일수록 상관이 떨어짐 → spec §2.1의 "클라이막스 peak f0가 지각 음고" 가설은 이 청자에게 **성립하지 않음**. 굳이 f0를 쓴다면 95p가 아니라 **median**(그래도 약함, r=0.37).

### 2.2 valence (y후보3: 오디오 정서) — ✅ 검증

| feature | pearson r | p | spearman ρ | p |
|---|---:|---:|---:|---:|
| contrast | +0.558 | 0.002 | +0.558 | 0.002 |
| ★ **mode_score** | **+0.509** | **0.006** | +0.504 | 0.006 |
| x_f0_cent_roll | −0.389 | 0.041 | −0.435 | 0.021 |
| voiced_frac | +0.357 | 0.062 | +0.357 | 0.063 |

spec 지정 **mode_score(장/단조)가 |r|=0.51, p=0.006으로 임계 통과.** 장조일수록 밝게 지각. spectral contrast도 +0.56으로 동급. **후보3 채택 가능.**

### 2.3 rough (y후보2: 음색 거칢) — ✅ 강하게 검증

| feature | pearson r | p | spearman ρ | p |
|---|---:|---:|---:|---:|
| ★ **contrast** | **−0.808** | **<0.001** | −0.803 | <0.001 |
| ★ **flatness** | **+0.592** | **0.001** | +0.595 | 0.001 |
| rolloff | +0.456 | 0.015 | +0.484 | 0.009 |
| centroid | +0.452 | 0.016 | +0.468 | 0.012 |

**spectral contrast가 |r|=0.81** — 전체에서 가장 강한 신호. contrast 낮음=거침(디스토션/노이즈로 스펙트럼 골-마루 대비 소멸), 높음=매끄러움. flatness도 보강(+0.59). **후보2가 가장 견고.**

---

## 3. 해석·결정

### spectral contrast가 두 축을 지배 — y축은 실질적으로 하나
contrast는 valence(+0.56)·rough(−0.81) 양쪽 최상위다. 이 청자에게 **밝음↔어두움과 매끄러움↔거침이 상관**돼 있기 때문(라벨 자체도: RAS·ave = 거침&어두움, hello·morfonica = 매끄러움&밝음). 즉 **y축 후보3과 후보2가 사실상 같은 물리 차원(스펙트럼 대비)의 양면.**

- **y축 확정 권고**: **spectral contrast 주축** + mode_score 보조.
  - "거칢"으로 라벨링하면 contrast가 −0.81로 압도적 → 축 이름을 **매끄러움↔거침**으로 하면 가장 정직(r 최고).
  - "정서(밝음↔어두움)"를 원하면 mode_score(+0.51)+contrast(+0.56) 결합. 사용자 원래 의도(정서)에 부합하나 contrast 단독보다 약간 약함.
  - 두 라벨이 상관되므로 **한 축으로 통합**하고 라벨만 선택하면 됨.

### x축은 재설계 필요 (f0 폐기 수순)
현 파일럿 데이터로는 **x축을 어떤 feature로도 정직하게 세울 수 없음.** 선택지:
1. **f0 median으로 약하게 유지**(r=0.37, p=0.05 경계) — 정직성 미달, 비권장.
2. **x축 개념 재정의** — "음고"가 아니라 이 청자가 실제로 가르는 다른 지각축(예: 편곡 **에너지/밀도**, 또는 템포·리듬). 새 라벨 필요.
3. **라벨 보강 후 재검정** — pitch 라벨이 3~4에 몰려(sd 0.73) 검정력이 약함. **의도적으로 극단 고음/저음 곡을 추가**해 재라벨(spec §5 주석)하면 f0가 살아날 여지는 있으나, §2.1 진단(음역 균질)상 기대 낮음.

---

## 4. 한계

- **주관 1인·n=28**: 상관은 이 청자 기준. pitch 라벨 sd=0.73으로 x축 검정력 특히 약함.
- **pitch 라벨 저분산**: 2·5가 각 2곡뿐 → 극단 표본 부족. x축 실패를 "f0 무효"로 단정하긴 이르나, feature 값 자체가 평평해 라벨 보강만으로 뒤집힐 가능성은 낮음.
- **누락 2곡**(idx 11·58 다운로드 실패) · **そばかす(idx 68)는 커버곡**(파스파레 버전 기준 라벨·feature 일관).
- **mode(장/단조) 추정**은 Krumhansl 상관 기반이라 오류 존재(그럼에도 r=0.51 확보).
- 2D 축 채택은 정성 탐색용. 밴드 식별 정직성은 별개(고차원 LOO, [../cluster_experiment.md](../cluster_experiment.md)).

---

## 5. 재현

```bash
# 1) 후보 feature 추출(전곡 Demucs 보컬분리 + f0/mode/timbre). 로컬 전용(저작물).
python -m pip install demucs                      # torch 위. CREPE/tensorflow 불필요
python tools/cluster/perceptual_features.py --pilot   # → cluster/axis_pilot_features.csv (n=28)

# 2) 손 라벨과 상관
python tools/cluster/axis_correlation.py          # 라벨 축별 피어슨/스피어만 표
```
- 입력: `cluster/axis_labels_worksheet.csv`(손 라벨, 커밋) · 산출: `cluster/axis_pilot_features.csv`(커밋).
- 음원 `cluster/audio_full/`은 gitignore(저작물). CPU ~81초/곡(Demucs+f0).

---

## 6. 다음 단계 (1차 시점)

1. **y축 확정** — spectral contrast 주축(+ mode_score). → 2차에서 **거칢↔매끄러움** 채택.
2. **x축 결정** — (a) 개념 재정의 또는 (b) f0 보강 재검정. → **(a) 채택, §7.**
3. 확정 후 → 좌표·렌더 구현. → **완료(§8).**

---

## 7. 2차 — x축 재정의 재검정

1차에서 f0(음고)가 실패 → 사용자가 **개념 재정의**를 선택. 새 x 후보 3종을 손 라벨(n=28)로 재검정:
**energy(잔↔강)·tempo(느↔빠)·acoustic(어쿠↔일렉)**. 각 후보 feature도 보강(`onset_rate·harmonic_ratio·perc_ratio`, `add_x_features.py`).

### 7.1 결과 — 세 후보 모두 "밝기/거칢 축"으로 붕괴

| x 라벨 | 의도 feature (결과) | 실제 최상위 | 판정 |
|--------|--------------------|------------|------|
| energy | rms +0.16 · onset −0.33 ❌ | rolloff +0.81, centroid +0.80, **contrast −0.65** | 독립 x 아님 |
| tempo | **tempo +0.05 ❌** | rolloff +0.66, **contrast −0.53** | 독립 x 아님 |
| acoustic | harmonic_ratio −0.14 ❌ | **contrast −0.65**, flatness +0.56 | 독립 x 아님 |

의도한 feature(rms·onset·**librosa tempo**·harmonic_ratio)는 전부 실패. 세 후보가 모두 **동일한 밝기/contrast 클러스터**로 환원됨.

### 7.2 라벨 구조 — 지각은 2차원, 측정 가능은 1.x차원

라벨끼리 피어슨(n=28):

```
        rough energy tempo acoust valen
rough   +1.00  +0.42 +0.29 +0.72  -0.73
energy  +0.42  +1.00 +0.81 +0.42  -0.24
tempo   +0.29  +0.81 +1.00 +0.34  +0.01
acoust  +0.72  +0.42 +0.34 +1.00  -0.35
valen   -0.73  -0.24 +0.01 -0.35  +1.00
```

- 클러스터①: rough ≈ acoustic(+0.72) ≈ **−valence(−0.73)** — "거칢/어두움/일렉트로닉" 한 축.
- 클러스터②: **energy ≈ tempo(+0.81)** — "에너지/빠르기" 별개 지각축(rough와 0.29~0.42로 약결합 → 독립).
- **그러나 ②를 잡는 feature가 없다.** 강한 feature는 전부 ①(contrast/rolloff)로만 감. contrast와 독립적인 유일 feature = **mode_score**(contrast vs mode r=+0.37).

→ **측정 가능한 정직한 2D 기저는 (contrast, mode) 하나뿐.** 사용자가 시도한 energy/tempo/acoustic x축은 전부 contrast축의 재측정이라 독립 x가 못 됨.

### 7.3 채택 (사용자 결정)

| 축 | feature | 방향 | 검증 | 독립성 |
|----|---------|------|------|--------|
| **x** | spectral contrast | 오른쪽=거칢 / 왼쪽=매끄러움 | r=−0.81 | — |
| **y** | mode_score(장/단조) | 위=밝음 / 아래=어두움 | r=+0.51 | contrast와 r=0.37 |

역설: **spec 원래 y후보 2개(거칢 contrast + 정서 mode)가 결국 유일하게 성립한 2D.**

---

## 8. 구현 (채택본)

- **`tools/cluster/build_perceptual_map.py`** → `cluster/audio_map.json`. x=contrast, y=mode 를 각 z-score·스케일해 **좌표축으로 직접**(PCA/f0/Demucs 불필요). 밴드 중심=곡 평균. sim(CLAP 유사곡)은 v2 json에서 (band,song) 매칭 승계.
- **렌더**(`static/js/script.js renderCluster`): `axes.{x,y}.{pos,neg}`로 4모서리 라벨 자동, 곡=작은 점·밴드=중심 라벨점. **곡 클릭=재생**(곡 리스트 선택과 동일, 재생 곡은 지도에서 흰 테두리 강조)·**밴드 클릭=그 밴드 강조**. CLAP 유사곡(`sim`)은 JSON에 보존하되 **표시 제거**(근접=유사가 이 지도엔 더 자연스러움, 사용자 피드백).
- **원점 보정(사용자 피드백)**: 데이터 평균이 밝은 팝에 치우쳐 지각적 중립이 어둡게 찍힘 → **y +10**(RAS '약간 마이너'를 y≈−5에 앵커). 상수 가산이라 재계산 불필요. `Y_SHIFT`·metrics 기록.
- **큐레이션 보정 `BAND_OVERRIDES`(★측정 아님★)**: feature가 못 잡는 밴드만 밴드 단위 nudge, 전곡 균일 적용(개별 곡 스프레드 보존). 현재 **morfonica dy +15**(바이올린 음색 밝음 미측정 — §7.x 참조). `audio_map.json.overrides`에 투명 기록.
- **밴드 중심 정합(TOP10×10, 97곡 미리보기)**: 매끄러움=hello·morfonica·pastel / 거칢=mugendai·RAS·afterglow / 밝음=hello·poppin·morfonica(큐레이션) / 어두움=ave·roselia. (ave x는 오케스트라 배음이 contrast를 높여 매끄러움쪽 — 프록시 한계, y는 정확.)
- **다음(승인 시)**: 전곡 660 확대(contrast·mode는 저렴 — Demucs 불필요). 렌더 최적화(large/progressive) 동반.

### 8.1 morfonica 정서 — feature로 못 잡음(→ 큐레이션)
morfonica의 '밝음'은 바이올린 음색인데, ①곡별 mode가 −27~+29로 퍼져 **상수로 통용 불가**, ②HPSS 선율밝기(harm_cent val_r −0.20 / harm_ratio val_r +0.06)는 valence와 무상관, ③음색밝기(centroid)는 이 카탈로그에서 거친 밴드와 겹쳐(−0.66) valence −상관. **측정 불가 확인** → 사용자 판단(B안)으로 `BAND_OVERRIDES` 밴드 nudge. ave는 y(mode) 정확·x만 프록시 한계라 보정 안 함.

### 한계 (2차 추가)
- **librosa tempo가 체감 템포와 무관**(r=0.05) — BPM 추정 옥타브오류/지각 템포 불일치. rms도 무효(믹스 라우드니스 정규화로 분산 작음).
- 지각적으로 에너지/템포 축이 존재하나 현 feature로는 분리 불가 → 향후 loudness range·tempogram 등으로 재시도 여지(미착수).
