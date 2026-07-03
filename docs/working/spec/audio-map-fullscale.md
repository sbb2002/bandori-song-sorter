# 음원맵 전곡 확대 — 구현 스펙

> **이 파일 = 음원맵을 TOP10×10(현재) → 전 카탈로그로 확대할 때 볼 유일한 구현 문서.**
> 축 재정의(30곡 파일럿 검증)는 **완료**(done 세션 21). 축·좌표 설계 근거는 [audio-map-axes.md](audio-map-axes.md) + `docs/working/report/cluster-correlation/README.md`. 여기는 **스케일업만** 다룸.

마지막 갱신: **2026-07-02** (feature/emoi-cluster-v2)

---

## 현재 상태 (확대의 출발점)

- **채택 축**: x = spectral contrast(오른쪽 거칢 / 왼쪽 매끄러움, r=−0.81), y = mode_score 장·단조(위 밝음 / 아래 어두움, r=+0.51). **Demucs·f0·PCA 전부 불필요** — contrast·mode 두 특징만, z-score 직접좌표.
- **파이프라인**: `python src/tools/cluster/build_perceptual_map.py [--cache audio_cache|audio_full]` → `src/content/cluster/audio_map.json`(커밋).
  - 입력 매니페스트 = **`src/content/cluster/songs_top10.csv`**(하드코딩 `MANIFEST`, 컬럼 `band,idx,song,url`).
  - 음원 = `src/content/cluster/<cache>/<band>__<idx:03d>.wav`(48kHz, gitignore). 현재 `audio_cache`=60초 클립 TOP10×10 **97곡만** 존재.
  - 튜닝 상수: `X_SHIFT,Y_SHIFT=0.0,10.0`(y 원점 보정), `BAND_OVERRIDES = {morfonica: dy+15}`(★측정 아님★ 밴드 큐레이션, `audio_map.json.overrides`에 투명 기록).
- **렌더**: `static/js/script.js` `_clDraw()` — ALL(정적 개요, 밴드 아이콘 PNG + 곡 점 s=0.5 뭉침) / 포커스(센트로이드 정중앙 + x·y 축선). 재생 곡 파동. `<script src>` 연결이라 JS 수정은 리빌드 불필요.

---

## 확대 시 할 일 (순서대로)

### 1. 범위 결정 (택1) — ⚠️ 사용자 결정 필요
| 옵션 | 곡수 | 캐시 용량 | 성격 |
|------|------|-----------|------|
| ① 전체 660 | 660 | ~3.7GB | "전 디스코그래피를 소리로 탐색하는 도구". 점 매우 빽빽 |
| ② **밴드당 캡 N(예 30~40)** | ~300 | ~1.7GB | 중심점 균형 유지 + 탐색 3~4배(개인 추천 균형안) |
| ③ 지금 유지 | 97 | 현행 | 나중으로 |

**밴드 불균형**(고유 660 기준): poppin124·roselia98·raise80·pastel74·afterglow72·hello72·morfonica57·mygo41·ave29·mugendai23 / **various_artists5·ikka_dump_rock1·millsage1**(곡 너무 적음 → 중심점 생략, 점으로만 or 제외).

### 2. 매니페스트 생성
`src/content/songs/*.yaml`에서 **전체/캡 매니페스트 CSV**(`band,idx,song,url`, dedup=vid) 생성. `build_perceptual_map.py`에 **`--manifest` 인자 추가**(현재 `MANIFEST` 하드코딩) 또는 새 CSV로 교체. 캡 옵션이면 밴드당 상한 N 잘라내기.

### 3. 오디오 추출
매니페스트의 각 url을 **`fetch_audio.py`로 추출 → `src/content/cluster/audio_full/<band>__<idx:03d>.wav`**(48kHz mono, gitignore).
- 툴: `python src/tools/cluster/fetch_audio.py --cache audio_full --manifest <full.csv>` (2026-07-03 추가). **재개 가능**(skip-existing)·**fail-soft**(실패곡 스킵, 재실행 재시도). 안티봇 5원칙(`-f ba -x` / 곡간 30–60s 랜덤 / `--sleep-requests 5` / `--limit-rate 250K` / `--cookies-from-browser`) 출처 = [../../idea/260703.md](../../idea/260703.md). `--dry-run`/`--limit N` 으로 무네트워크 점검·스모크.
- contrast·mode는 **전곡 통계**라 60초 크롭 불필요 — 전곡(또는 대표 구간) 로드로 충분. Demucs 보컬분리 **불필요**(f0 축을 폐기했으므로).
- 비용: 다운로드 ~30–60분 + 추출 ~20–30분, **일회성 로컬 빌드**(산출 `audio_map.json`만 커밋). ⚠️ wav 캐시는 gitignore=장치 전용 → 다른 로컬은 재수집.

### 4. 빌드
`python src/tools/cluster/build_perceptual_map.py --cache audio_full [--manifest <full.csv>]` → `src/content/cluster/audio_map.json` → `python src/build.py`.
- 곡수 급증 시 `BAND_OVERRIDES`(morfonica) 재점검. 필요하면 `--y-shift` 재튜닝. **이 전곡 빌드가 좌표 기준의 "마지막 튜닝 순간"** — 여기서 상수를 확정·동결하고 그 다음부터 오디오 폐기.
- ⭐ **증분 자동화 대비(지금 남길 것)**: 이후 CI 신곡을 재다운로드 없이 얹으려면 **정규화 파라미터(contrast·mode의 mean·std + x/y_shift + overrides)를 `audio_map.json`에 함께 저장**. 오디오는 분석 후 폐기되므로 지금 안 남기면 나중에 전곡 재수집 필요. 자동화 설계 = [pipeline-automation.md](pipeline-automation.md) §5.
- `carry_sim()`은 (band,song) 매칭으로 구 CLAP sim 승계 — 신규 곡은 sim 없음(연결선은 이미 표시 제거 상태라 무해).

### 5. 렌더 최적화 (수백 점 대응)
- ECharts `series.large: true` + `largeThreshold`, 필요 시 `progressive` 렌더.
- 밴드 클릭 강조·줌/팬 **더 중요**(빽빽함). ALL에서 밴드 아이콘이 곡 점에 묻히지 않도록 z-order·크기 재점검.
- 넓은 표시 영역 필요 → **분할 비율(yt:음원맵)·배치 결정과 연결**(HANDOFF 열린 결정).

---

## 한계 (유지)
2D 투영은 정성용(정직성 지표는 고차원). BanG Dream 동일 장르라 음향 변별력 본질적으로 낮음 — 카탈로그가 **음향적으로 사실상 1차원**(contrast/밝기 지배, mode만 독립 r=0.37). 곡별 y(mode)는 불안정 → s=0.5 뭉침으로 완화 중. morfonica 밝음(바이올린 음색)은 어떤 feature로도 측정 불가 → 밴드 큐레이션으로만 보정.

---

## 밴드 퍼스널 컬러 (렌더 재사용 — `script.js` `BAND_COLORS`)
| 밴드 | 색 | 밴드 | 색 |
|------|------|------|------|
| poppin_party | `#ff3377` | morfonica | `#33AAFF` |
| afterglow | `#ee3344` | raise_a_suilen | `#33CCCC` |
| pastel_palettes | `#33ddaa` | mygo | `#0088BB` |
| roselia | `#3344aa` | ave_mujica | `#881144` |
| hello_happy_world | `#ffdd00` | mugendai_mutype | `#ff7788` |
| millsage | `#AA22EE` | ikka_dump_rock | `#FFAA33` |
