# 밴드 음원 지도 — 음원 임베딩 백엔드 비교 (librosa vs CLAP)

작성: 2026-07-01 · 브랜치 `feature/emoi-cluster` · 옵션2(음원 임베딩 강화) 결과

## 배경

클러스터(#2)는 "키워드 점들에서 밴드 군집이 안 보인다"는 관찰에서 출발해 재설계됐다.
실측 결과 **가사(키워드/문장)·곡 단위로는 어떤 신호도 silhouette≈0**(밴드 영역이 안 생김)이었고,
**단위를 밴드로 올려 음악적 특징으로 집계**하면 밴드가 구별됨을 확인했다(최근접-중심 LOO 분류).
옵션1은 `librosa` 수제 음악특징(71차원)으로 밴드 음원 지도를 탑재했다.
옵션2는 "더 강한 음악 임베딩(LAION-CLAP, 512차원)이 더 나은가?"를 검증한다.

## 방법

- 표본: 밴드별 조회수 TOP10 × 10밴드 → **동일 93곡**(지역락/전송실패 7곡 제외), 각 곡 45~105s(60초) 구간.
- 음원 캐시는 **48kHz**로 추출(CLAP은 48kHz 풀밴드 학습 모델 → 공정 비교를 위해 필수).
  - `librosa`: 내부 16kHz 로드 후 MFCC(20)·크로마·스펙트럼 대비/중심/대역폭/롤오프/평탄도·ZCR·RMS·템포.
  - `CLAP`: `laion/clap-htsat-unfused`(HuggingFace transformers 내장), 48kHz 네이티브, `pooler_output` 512차원.
- 지표(고차원에서 직접):
  - **LOO 최근접-중심 분류 정확도** — 곡을 (자신 제외) 가장 가까운 밴드 중심에 배정, 자기 밴드 적중률. 우연 10%.
  - **kNN 같은-밴드 배율** — 한 곡의 k=10 최근접 이웃이 같은 밴드일 확률 / 우연.
  - **silhouette** — 전역 군집 분리도(≈0 = 분리 없음).

## 결과

| 백엔드 | 차원 | LOO 분류 | kNN 배율 | silhouette |
|--------|-----:|---------:|---------:|-----------:|
| **librosa** | 71 | **53%** | **2.66x** | **−0.016** |
| CLAP | 512 | 45% | 2.40x | −0.044 |

> 보강: 16kHz·96곡 실행에서도 librosa 62% > CLAP 46%. **세 표본(93곡 53% / 96곡 62% / 97곡 59%) 모두 librosa 우위**로 일관 → 표본 노이즈 아님.
> (단, 밴드당 ~9곡이라 LOO 자체의 표본 변동은 ±수 %p 있음. CLAP은 45~46%로 일관.)
>
> **탑재본**: `cluster/audio_map.json` = librosa·**97곡·LOO 59%**(누락 3곡=지역락 추정 제외). 위 비교표의 53%는 CLAP과 동일한 93곡 부분집합 기준(공정 비교용).

### 밴드별 최근접 밴드(중심 거리)

| 밴드 | librosa 최근접 | CLAP 최근접 |
|------|----------------|-------------|
| afterglow | roselia | mygo |
| ave_mujica | morfonica | **roselia** ✓ |
| hello_happy_world | pastel_palettes ✓ | pastel_palettes ✓ |
| morfonica | afterglow | poppin_party |
| mugendai_mutype | afterglow | **raise_a_suilen** ✓ |
| mygo | poppin_party ✓ | afterglow ✓ |
| pastel_palettes | hello_happy_world ✓ | hello_happy_world ✓ |
| poppin_party | roselia | morfonica |
| raise_a_suilen | morfonica | roselia |
| roselia | afterglow | **ave_mujica** ✓ |

## 해석

**트레이드오프가 명확하다.**

- **librosa = 더 나은 분류·읽기**: LOO·kNN·silhouette 전부 우위. 중심점이 고르게 퍼져
  라벨이 안 겹치고 밴드가 또렷이 식별된다. 저수준 음향 특징(MFCC·스펙트럼 통계)이
  같은 제작사·같은 장르(BanG Dream 애니 밴드록) 안에서의 **미세한 제작/믹스/음색 지문**을
  더 잘 구분한다.
- **CLAP = 더 음악적인 밴드 관계**: 분류는 낮지만 최근접 밴드가 의미상 더 타당하다.
  - **roselia ↔ ave_mujica 상호 최근접** — 고딕 자매밴드(스타일·세계관 공유)를 정확히 포착.
    librosa는 못 잡았다(roselia↔afterglow, ave↔morfonica).
  - **mugendai ↔ raise_a_suilen** — EDM/일렉트로닉-록 융합 계열. 역시 librosa는 놓침.
  - 대신 그 의미적 묶음 탓에 **중심점이 충돌**(roselia·ave 거의 겹침 → 지도 라벨 겹침),
    범용 임베딩이 같은 장르 안의 개별 밴드를 "애니 록밴드"로 뭉뚱그려 미세 구분이 약함.

요약: **"강한 임베딩이 더 낫다"는 가설은 이 과제에선 성립하지 않았다.** CLAP은 장르/무드
의미를 잡아 *밴드 간 유사도*엔 강하지만, *밴드 식별(지도)* 목적엔 librosa가 낫다.

## 결정

**밴드 음원 지도는 `librosa` 백엔드를 채택**(옵션1 그대로 유지). 근거:

1. 분류·분리·가독성 모두 우위(53% vs 45%, 중심점 안 겹침).
2. 빌드 의존성 가벼움(CLAP은 ~1.5GB 모델 + 추론 필요).
3. 이미 탑재됨(`cluster/audio_map.json`).

CLAP이 보인 **음악적 최근접 관계(고딕쌍·EDM쌍)는 옵션3(곡/밴드 유사곡 탐색)에 더 적합**할
수 있어 후속 후보로 보존(이 문서가 그 근거).

## 한계

- 60초 1구간만 사용(CLAP은 ~10s 윈도 평균이 권장 — 청크 평균 시 소폭 개선 여지). 밴드당 ~9곡.
- 2D 투영(중심점 PCA-fit)은 정성 해석용. 정직성 지표는 고차원 LOO.

## 재현

```bash
python tools/cluster/build_audio_map.py --backend librosa            # 채택본(다운로드 포함)
python tools/cluster/build_audio_map.py --backend clap --no-download --out cluster/_audio_map_clap.json
```

비교 산점도: `docs/report/cluster_audio_backends.png` (좌 librosa / 우 CLAP).
음원 캐시(`cluster/audio_cache/`)·CLAP 비교본(`_audio_map_clap.json`)은 저작물/파생물로 비커밋(gitignore).
