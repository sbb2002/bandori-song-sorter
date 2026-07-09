# 클러스터(#2) 실험 종합 보고서 — 가사 의미공간에서 음원 밴드 지문까지

> 본 문서는 bandori-song-sorter "밴드 시각화 클러스터"(#2)의 전체 탐색 기록이다.
> **무엇을 시도했고, 무엇이 실패했으며, 왜 음원으로 귀결됐는지**를 수치와 함께 남긴다.
> 향후 재현·재설계·인용의 단일 출처. 백엔드 비교 상세는 [cluster_audio_clap.md](cluster_audio_clap.md).
>
> 작성 2026-07-01 · 브랜치 `feature/emoi-cluster` · 대상 표본 밴드 10개(TOP10 가사/음원 보유 밴드).

---

## 0. TL;DR

| 단계 | 점의 단위 | 입력 | 밴드 신호 | 깨끗한 군집? |
|------|-----------|------|-----------|--------------|
| P0 | 키워드(단어) | 가사 키워드 jp 임베딩 | kNN **1.19x** | ✗ 노이즈 |
| P1 | 문장(가사 행) | 가사 행 jp 임베딩 | kNN **1.99x**, sil −0.055 | ✗ |
| P2 | 곡 | 음원/문장/융합 | 음원 **2.79x**, sil≈0 | ✗ |
| P3 | **밴드(중심)** | **음원(librosa)** | **LOO 분류 59~62%** (우연 10%) | **✓** |
| P4 | 밴드(중심) | librosa vs **CLAP** | librosa 우위(식별), CLAP 우위(유사) | — |
| P5 | 곡 | **CLAP** 유사곡 | 무드 일관 추천 | — |

**핵심 결론 3가지**
1. **가사 의미로는 밴드가 안 갈린다.** 키워드/문장/곡 어느 단위로도 전역 군집(silhouette)≈0. 10밴드가 사랑·꿈·밤 등 **주제를 공유**하기 때문. 의미 임베딩은 정상 작동(유의어는 뭉침)하나 **밴드 소속과 의미 축은 직교**한다.
2. **음악적 소리로는 밴드가 갈린다.** 곡을 밴드로 집계하면 librosa 음향 특징이 밴드를 **LOO 59~62%**(우연 6배)로 분류. 안 보였던 건 신호 부재가 아니라 곡 단위 노이즈.
3. **역할 분담.** 밴드 **식별 지도**=librosa(저수준 음향 지문), 곡 **유사도 추천**=CLAP(의미·무드). 각 백엔드가 잘하는 일이 다르다.

---

## 1. 동기

초기 구현은 **키워드 의미공간 2D 산점도**였다(워드클라우드 키워드를 다국어 문장임베딩 → UMAP, 점=키워드, 색=주 밴드). 사용자 관찰: **"키워드 점들에서 밴드끼리의 군집이 안 보인다."** 이를 정량 검증하고, 보인다면 강화하고 안 보이면 대안을 찾는 것이 본 실험의 목표였다.

---

## 2. 데이터 출처 (provenance)

| 자산 | 내용 | 추적 | 비고 |
|------|------|------|------|
| `data/*.yaml` | 전 곡 메타(밴드·곡명·**url**) 660곡 화면 | 커밋 | 음원 URL의 원천 |
| `assets/lyrics/<band>.md` | 가사 원문(jp+로마자+ko 3줄/연), 밴드 TOP10 | **gitignore** | 저작물. 템플릿만 커밋 |
| `wordcloud/*.yaml` | 가사 키워드 집계(jp·ko·weight·senti) | 커밋 | P0 키워드 입력 |
| `cluster/songs_top10.csv` | TOP10×10 매니페스트(idx·band·song·url) | **커밋** | 음원 재현 키. 가사가 gitignore라 별도 필요 |
| `cluster/audio_cache/*.wav` | 곡당 60초(45–105s) **48kHz mono** | **gitignore** | 저작물. yt-dlp 추출 |
| `cluster/audio_map.json` | 밴드 지도 좌표+유사곡 | 커밋 | 앱 입력(`build.py`) |
| `cluster/keywords_2d.json` | (구) 키워드 좌표 | 커밋 | P0 잔존, 미사용 |

**표본 규모**: TOP10×10밴드 = 100곡 후보. 지역락/전송실패 제외 후 음원 확보 **93~97곡**(실행마다 변동). 가사 행은 일본어 원문 **4,323행**(중복 후렴 제거 시 고유 3,463행, 중앙값 13자).

---

## 3. 방법론

### 3.1 임베딩
- **텍스트(P0·P1·P2)**: `sentence-transformers paraphrase-multilingual-MiniLM-L12-v2`(384d). 일본어 원문 인코딩(번역 손실 회피). **이 모델은 문장 인코더** → 단어 단독(P0)은 설계 용도 밖, 문장(P1)이 본령.
- **음원-librosa(P2~)**: 71차원 수제 음악특징 = MFCC(20) mean+std, 크로마(12) mean, 스펙트럼 대비(7) mean, 스펙트럼 중심/대역폭/롤오프/평탄도·ZCR·RMS의 mean/std, 템포. 내부 16kHz 로드.
- **음원-CLAP(P4·P5)**: `laion/clap-htsat-unfused`(HuggingFace transformers 내장, 512d). 48kHz 네이티브, `get_audio_features().pooler_output`.

### 3.2 차원축소
- 텍스트 P0·P1: UMAP(cosine, n_neighbors=15, min_dist=0.1).
- 음원 지도: **밴드 중심점에 PCA(2) fit → 곡·중심점을 같은 변환으로 투영**. 밴드 간 분산 최대화 축이라 중심점이 또렷이 분리되고 곡은 그 주위로 흩어진다(차별적 투영, LDA의 비지도 근사). 0~100 정규화.

### 3.3 지표 (정직성 기준은 고차원에서 직접 측정)
- **kNN 같은-밴드 배율** = (한 점의 k 최근접 이웃이 같은 밴드일 확률) / (우연 기대값 Σ pᵦ²). 1.0=무작위.
- **silhouette(밴드 라벨)** ∈ [−1,1]. ≈0 = 전역 군집 분리 없음. **2D 산점도의 "깔끔함"을 가장 잘 대변.**
- **LOO 최근접-중심 분류 정확도** = 각 곡을 (자신 제외) 가장 가까운 밴드 중심에 배정한 자기 밴드 적중률. 우연 = 1/밴드수 ≈ 10%. **밴드 식별력의 핵심 지표.**

---

## 4. 단계별 결과

### P0 — 키워드(단어) 단위 : 신호 없음
- 고유 키워드 **567개** / 10밴드. **155개(27%)가 2밴드+ 공유어.**
- kNN(k=6) 같은-주밴드 **13.9%** vs 우연 11.7% = **1.19x ≈ 노이즈.**
- 임베딩 자체는 정상: 유의어가 정확히 인접(`夜`→夜中·夜空·暗夜·今夜·夜明け / `花`→薔薇·花弁·蕾·山茶花 / `愛`→동경·갈망·소원·희망).
- **해석**: 지도의 축=단어 의미, 색=밴드. 둘은 **직교**. 모든 밴드가 같은 주제를 노래 → 의미 무리 안에 색이 골고루 섞임. 이 맵은 "감정·주제 지형도"이지 "밴드 지도"가 아니다.

### P1 — 문장(가사 행) 단위 : 국소 2배, 전역 0
- 일본어 원문 행 (band,jp) 중복제거 후 **3,479점**.
- kNN(k=10) 같은-밴드 **20.5%** vs 우연 10.3% = **1.99x**, **silhouette −0.055.**
- 밴드별 자기응집 배율: hello **4.35x**, mygo 2.35x, poppin 2.23x, pastel 1.95x, roselia 1.91x, ave 1.78x, raise 1.70x, morfonica 1.63x, afterglow 1.44x, mugendai 1.32x.
- **해석**: 문맥·문체가 더해져 국소 신호 2배(키워드 1.19x→1.99x), 일부 밴드(hello=난센스·영어혼용 어휘 독보적)는 가사로도 구별. **그러나 silhouette≈0 → 전역 분리 없음.** 고딕 두 밴드(roselia·ave)가 중간인 건 서로 고딕 어휘를 공유해 독자성이 깎이기 때문. 가사 의미의 천장.

### P2 — 곡 단위 멀티모달 : 음원>문장, 융합 무익
96곡(60초), 동일 곡 집합·동일 지표:

| 구성 | 차원 | kNN 배율 | silhouette | 2D kNN |
|------|-----:|---------:|-----------:|-------:|
| 음원만(librosa) | 71 | **2.79x** | −0.012 | **3.13x** |
| 문장만(행 임베딩 평균) | 384 | 2.42x | −0.016 | 2.26x |
| 융합(z-score 결합) | 455 | 2.79x | −0.003 | 2.73x |

- **음원 > 문장**. **융합은 이득 없음** — 고차원 text(384d)가 audio(71d)를 희석, 2D에선 오히려 융합(2.73x) < 음원(3.13x).
- 셋 다 곡 단위 silhouette≈0 → **곡 산점도는 무엇을 써도 섞여 보인다.**

### P3 — 밴드(중심) 단위 : 돌파구
- **LOO 최근접-중심 분류**: 음원 **61%**(우연 10% = **6배**), 융합 55%. → **음원 단독이 최선**(융합 또 손해).
- **곡은 섞여도 밴드 평균(중심)은 또렷이 다르다.** 안 보였던 건 신호 부재가 아니라 곡 단위 노이즈에 묻혀서.
- → 제품의 점 단위는 **밴드(중심점)**여야 한다(키워드/곡 아님). 옵션1로 탑재.

### P4 — librosa vs CLAP (밴드 식별) : librosa 채택
동일 93곡(48kHz):

| 백엔드 | 차원 | LOO | kNN | silhouette |
|--------|-----:|----:|----:|-----------:|
| **librosa** | 71 | **53%** | **2.66x** | **−0.016** |
| CLAP | 512 | 45% | 2.40x | −0.044 |

- 세 표본(93곡 53% / 96곡 62% / 97곡 59%) 전부 librosa 우위, CLAP 45~46% 일관. **표본 노이즈 아님.**
- 최근접 밴드 타당성은 **CLAP이 더 음악적**: roselia↔ave_mujica(고딕 자매밴드 상호 최근접, librosa는 놓침), mugendai↔raise(EDM쌍). 대신 그 의미 묶음으로 **중심점이 충돌**(roselia·ave 겹침)해 식별·가독성은 떨어짐.
- **결정**: 밴드 식별 지도 = **librosa**(분류·분리·가독성 우위, 의존성 가벼움). 상세 [cluster_audio_clap.md](cluster_audio_clap.md) · 그림 [cluster_audio_backends.png](cluster_audio_backends.png).

### P5 — 곡 유사곡 (추천) : CLAP 채택
샘플곡 유사곡 TOP5, librosa vs CLAP:

| 질의곡(무드) | librosa | CLAP |
|---|---|---|
| roselia 礎の花冠(웅장) | ⚠️mugendai 먼저, 혼재 | roselia·roselia·raise·raise → 강렬록 일관 |
| poppin Returns(밝음) | ⚠️ave(고딕) 먼저 | poppin·poppin·poppin·afterglow → 밝음 일관 |
| hello ゴーカ(발랄) | hello·pastel·hello·⚠️**ave·ave**(고딕!) | hello·pastel·hello·hello → 무드 일관 |
| mygo 春日影 | mygo 2곡, 혼재 | mygo 3곡 |
| mugendai コミュ着火 | mugendai 5곡 | mugendai 5곡(일치) |

- **librosa는 "제작 지문"을 매칭 → 무드가 튀는 추천**(발랄 hello에 고딕 ave). **CLAP은 "소리·무드" 매칭 → 자연스러움.**
- **결정**: 곡 유사곡 = **CLAP**. P4 보고서 예측("CLAP=유사도, librosa=식별") 그대로 실증.

---

## 5. 종합 — 두 백엔드의 역할 분담

```
            식별(밴드를 가른다)        유사도(소리가 비슷하다)
librosa   ●●●●●  (LOO 59%, 또렷)     ●●○○○  (지문 매칭, 무드 튐)
CLAP      ●●○○○  (LOO 45%, 충돌)     ●●●●●  (무드 일관, 고딕쌍 포착)
```
- **밴드 음원 지도**(옵션1·2) = librosa 좌표.
- **곡 유사곡 탐색**(옵션3) = CLAP 코사인 top-N(곡별 사전계산, `audio_map.json.songs[i].sim`).
- 한 파이프라인(`build_audio_map.py --sim clap`)이 둘을 한 파일로 산출 → 렌더는 CLAP 불필요(인덱스만 읽음).

---

## 6. 산출 아티팩트 (data dictionary)

`cluster/audio_map.json`:
```
{ generated, backend:"librosa", sim_backend:"clap",
  bands:[stem…],
  songs:[ { band, song, x, y, sim:[songs 인덱스…] } ],   # x,y=PCA-fit 좌표 0~100
  centroids:[ { band, x, y, n } ],                        # 밴드 중심점
  metrics:{ loo_acc, knn_ratio, knn_same, chance, silhouette, k } }
```
- `songs[i].sim` = i번 곡과 **CLAP 코사인** 최근접 곡들의 **songs 배열 인덱스**(자기 제외, 최대 6). 옵션3 하이라이트용.
- 그림: `cluster_audio_backends.png`(좌 librosa / 우 CLAP 중심점 배치).

---

## 7. 재현

```bash
# 의존성(음원=로컬 전용, 저작물)
python -m pip install -r tools/cluster/requirements-audio.txt   # librosa·yt-dlp·imageio-ffmpeg
python -m pip install "transformers>=5"                          # CLAP(내장). torchaudio 불필요(librosa 로드)

# 채택본(밴드 지도=librosa, 유사곡=CLAP). 음원 없으면 yt-dlp로 60s 48kHz 추출.
python tools/cluster/build_audio_map.py                          # = --backend librosa --sim clap
python build.py                                                  # index.html 주입

# 비교 재현
python tools/cluster/build_audio_map.py --backend clap --no-download --sim none \
       --out cluster/_audio_map_clap.json
```
- `--no-download` 캐시만 사용 · `--sim none` 유사곡 생략(빠름) · `--backend {librosa,clap}`.
- 매니페스트(`songs_top10.csv`)는 커밋되어 다른 장치서도 음원 재수급 가능(가사 원문 불필요).

---

## 8. 한계

- **표본**: 밴드별 ~9곡(TOP10−누락), 60초 1구간. LOO는 ±수 %p 표본 변동. CLAP은 ~10s 윈도 평균이 권장(청크 평균 미적용).
- **2D 투영**: 거리 왜곡 있어 정성 해석용. 정직성 지표는 고차원 LOO/silhouette.
- **장르 동질성**: 10밴드가 동일 제작사·동일 장르(애니 밴드록)라 식별 난도가 본질적으로 높음(silhouette≈0이 그 증거). 타 장르 혼재 코퍼스라면 군집이 더 또렷할 것.
- **CLAP 범용성**: 장르/무드는 잘 잡으나 같은 장르 내 미세 식별은 약함 — P4가 그 사례.

---

## 9. 후속 후보

- 청크(10s) 평균 CLAP·전곡 사용으로 식별·유사도 동시 개선 검증.
- 밴드 아이콘 배지/밴드 하이라이트 필터(기존 #2 백로그).
- 게시 위치((D) 결정)와 모바일 레이아웃 — HANDOFF #1-D와 함께.
