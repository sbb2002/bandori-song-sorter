# EMOI-MAP 좌표계 고찰 — Opus 코멘트 & 실행 기획안

> `docs/idea/260708.md`(사용자 3문항 + Millsage·Ikka 관찰)에 대한 Opus 검토·기획.
> 별밭/딥스페이스(작업 4, 완료) 뒤를 잇는 **좌표계 재고찰**. 사용자 선택 방향 3개(라벨 정직화·y축 토글·새 지각축 연구)를 의존 관계로 단계화.
>
> ⚠️ **인계 메모**: 이 세션 로컬은 `audio_full` **285/660**(부분)이라 Phase C 전곡 추출 불가.
> **오디오 완비 로컬/세션에서 이어받아 작업**한다(타 로컬 660곡 전곡 캐시, 메모리 `emoi-cluster-v4-status`).
> Phase A·B는 데이터(onset/energy 660 완비)만 있으면 어디서든 실행 가능.

---

## 1. 진단 (근거 있는 코멘트)

Millsage·Ikka에서 느낀 어색함은 우연이 아니라 **상관 보고서가 이미 문서화해 둔 두 한계**가 1곡 밴드에서 그대로 노출된 것이다.

### 지금 축이 실제로 무엇인가
- **x = spectral contrast** (거칢↔매끄러움), 검증 r=**−0.81** — 매우 강함. (`build_perceptual_map.py`)
- **y = mode_score** 장/단조 (어두움↔밝음), 검증 r=**+0.51** — 중간.
- 보고서(`side-project/emoi-map-axis-correlation`) 핵심: **contrast 하나가 '밝음(+0.56)'과 '거칢(−0.81)' 양쪽을 지배** → 이 청자에게 두 축이 상관돼, 명목상 2D지만 **실질 1.x 차원**(곡이 대각선으로 퍼짐). "경향성은 보이는데 개별 곡이 어색한" 근본 원인.

### 두 관찰 = 문서화된 한계의 교과서적 사례
- **Millsage** (매스록, 거친 리듬 + 키보드로 부드러움): x축이 재는 건 스펙트럼 대비뿐. 거친 기타가 contrast를 낮춰 오른쪽(거칢)에 찍히는데, **키보드 패드의 "부드러움"은 contrast에 안 잡힌다.** 보고서도 "지각은 보컬 register가 아니라 **편곡·음색의 게슈탈트**"라 적음. → "매끄러움" 라벨이 과대약속, contrast는 "맑음/디스토션 없음"에 가까움.
- **Ikka dumb rock** (펑크, 고음 아님 + 경쾌해서 밝음): y축은 장/단조만 봄. 파워코드/단조 리프면 mode_score가 낮게(어두움) 나오는데, 지각적 "밝음"은 **템포·리듬의 경쾌함**에서 옴. 보고서 §7.2 그대로: **`energy≈tempo(r=0.81)` 지각축이 존재하나 그걸 잡는 feature가 하나도 없었다**(librosa tempo r=0.05, rms 무효).

두 곡 모두 ① contrast를 "매끄러움" 프록시로 쓸 때의 편곡 음색 누락, ② energy/tempo 지각축의 feature 부재 — 딱 그 두 구멍. 하필 1곡 밴드라 밴드평균 보정(morfonica처럼)도 못 받아 프록시 한계가 날것으로 드러남.

### 3문항에 대한 답
1. **라벨 적절성** — 부분적으로 과대약속. x '매끄러움'은 실제론 "스펙트럼이 맑음"(편곡 부드러움과 어긋남). y '밝음'은 tempo/energy 밝음까지 기대되는데 실제론 장/단조만. → 라벨을 실체로 좁히는 게 정직.
2. **다른 feature** — 이미 광범위 시도해 대부분 소진(f0·centroid·rolloff·flatness·flux·zcr·rms·tempo·harmonic/perc ratio·onset_rate 전부 contrast로 붕괴/무효). **미착수 유망 후보는 loudness range·tempogram 둘뿐**(보고서 §215–216). 단 새 feature는 **손 라벨 재검정 전제**(현 n=28 과소). 에너지 성분은 이미 `dyn.v`로 계산돼 있어 재분석 없이 분포 확인 가능.
3. **3+ 좌표 표현** — 이미 z축이 하나 살아 있음(작업 4에서 energy=별 밝기/크기). 이를 명시 범례로 승격(2D+밝기). + **y축 토글**(정서 mode ↔ energy/tempo)로 다각 검증. small multiples(2장 병치)는 탐색·리포트엔 좋지만 프로덕션 HUD엔 무겁고 밴드 위치 대조가 어려움 → 비권장.

### 솔직한 우선순위
근본 해결(새 지각축 feature)은 라벨 재검정 + 오디오 재분석 + 검증 실패 리스크가 큰 **연구성 작업**. 반면 **라벨 정직화 + energy 범례 + y축 토글**은 저렴하고 즉시 체감이 바뀜. 후자를 먼저 하고, 그 과정에서 energy 분포를 보며 새 축의 정식 연구 가치를 판단.

---

## 2. 데이터 현황 (실행 전 확인됨)
- onset `dyn.v` **660/660**(energy 원천 완비) · `audio_map.json` `energy` **660/660**.
- `audio_full` wav — **이 로컬 285/660**(부분) / **오디오 완비 로컬 660/660**(Phase C는 여기서).
- 환경: A/B = **base env**(json/csv/jinja2). C = **hummingbird conda env**(librosa/오디오 스택). (메모리 `python-envs`)

## 편집 규칙(작업 4와 동일)
- `static/js/functions/16-audiomap.js`, `static/css/desktop.css` = 참조식 → **리빌드 불필요**.
- `audio_map.json` 변경 시에만 `python src/build.py` 1회(→ `window.CLUSTER_DATA` 재주입). `index.html`은 gitignore 산출물.

---

## 3. 실행 기획 (3단계)

### Phase A — 라벨 정직화 + energy 범례 (즉시 · 저비용)
현재 축 이름이 과대약속. 정직화 + energy(이미 별 밝기로 쓰임)를 명시.
- **축 라벨 정직화** — `audio_map.json`의 `axes.{x,y}.{pos,neg}` 텍스트를 실체에 맞게(예: y를 `밝음(장조)`/`어두움(단조)`로 한정, x에 "스펙트럼 대비" 함의 명시). `_clAxisLabels`(16-audiomap.js:693)가 이 값을 그대로 읽음 → **텍스트만** 수정. 원천 수정이므로 `build.py` 1회.
- **energy 범례 + 툴팁**(순수 JS, 리빌드 X):
  - 툴팁 formatter(16-audiomap.js:452–455)에 곡 energy 한 줄(`· 에너지 NN%`). `s.energy`는 이미 `_clDraw`에서 읽음.
  - `_clBuildSensTabs`(216) 패턴으로 범례 칩 1회 생성: "★ 별 밝기·크기 = 곡 에너지".

### Phase B — y축 토글: 정서(mode) ↔ 에너지 (즉시 · 중간)
이미 있는 energy(dyn.v)를 **대체 y좌표**로 만들어 지도에서 y축 전환. Millsage/Ikka를 에너지 축에서 즉석 재검증. (템포 축은 신뢰 feature 부재로 Phase C까지 보류 — `bpm`은 옥타브오류 r=0.05라 축 승격 안 함.)
- **데이터 precompute**(base env): `add_energy.py` 확장 또는 신규 `add_axis_energy.py`.
  - raw `mean(dyn.v)`를 `build_perceptual_map.zscale`와 동일 z-score·스케일 → `songs[].y_energy`(좌표 수학 일관).
  - 밴드별 `y_energy` 평균 → `centroids[].y_energy`.
  - `axes` 옆 대체 축 정의 추가(예: `axes_alt: {pos:'에너지↑/강함', neg:'에너지↓/잔잔'}`).
  - `build.py` 1회 → CLUSTER_DATA에 신규 필드 흐름(build.py는 json 필드 그대로 주입).
- **프론트**(16-audiomap.js, 리빌드 X):
  - 모드 상태 `_clYMode`('mood'|'energy') + 셀렉터 `_clYof(s)`/`_clCentYof(c)`.
  - `_clDraw`에서 `s.y`/`c.y` 읽는 지점 교체: 포커스 offset(565·567·568), ALL shrink(575–576), cent-arrow(594·597), 축 range. 토글 시 `_clRangeKey=null`로 range 재계산 강제.
  - 축 라벨 소스(`_clAxisLabels`)·HUD "밴드 밝음 y"(661–662)·부제 "거칢×정서"(438·586)를 `_clYMode`에 따라 스왑.
  - 토글 UI: `_clBuildSensTabs` 패턴의 `_clBuildYTabs()`(우상단, "정서/에너지") → 클릭 시 모드 설정 + 라벨 갱신 + `_clDraw()`.
- 참고: energy가 별 밝기(z채널)와 y축 두 역할 — 에너지 모드에선 밝은 별이 위로 정렬돼 상호 보강(문제 아님).

### Phase C — 새 지각축 연구 → report (연구 트랙 · **오디오 완비 로컬에서**)
energy/tempo 지각축을 **정직하게 측정**하는 마지막 후보 검증. 실패 리스크 있는 연구성 작업.
- **feature 추출**(hummingbird env): `perceptual_features.timbre()` 확장 — **loudness range**(pyloudnorm 단기 LUFS 스프레드 또는 RMS dB p95−p10)와 **tempogram 기반 지각 템포**(`librosa.feature.tempogram` 자기상관 피크; 현 `feature.tempo`보다 옥타브오류 완화). `axis_pilot_features.csv`에 열 추가.
- **재검정**: `axis_correlation.py`로 손 라벨(energy/tempo) 상관. n=28 과소 → **라벨 표본 확대**(에너지/템포 극단 곡 추가) 전제.
- **report**: `side-project/emoi-map-emotion-axes/phase-b0/README.md` — 방법·분포·r·채택여부.
- **실행 위치**: 이 로컬은 `audio_full` 285/660 → **전곡 추출은 오디오 완비 로컬**에서. 검증 통과 시 → Phase B 토글의 '에너지' 축을 '검증된 energy/tempo'로 승격/추가.

---

## 4. 변경 파일
| 파일 | 변경 | Phase | 리빌드 |
|------|------|-------|--------|
| `src/content/cluster/audio_map.json` | axes 텍스트 정직화 · `y_energy`/`axes_alt` 추가 | A·B | ✅ build.py |
| `src/tools/cluster/add_energy.py`(또는 신규 `add_axis_energy.py`) | raw dyn.v → `y_energy` 좌표·대체 centroid | B | — |
| `static/js/functions/16-audiomap.js` | 툴팁 energy·범례 칩(A) · y축 셀렉터/토글/라벨·HUD 스왑(B) | A·B | ❌ |
| `static/css/desktop.css` | 범례 칩·y토글 스타일(필요 시) | A·B | ❌ |
| `src/tools/cluster/perceptual_features.py` | loudness range·tempogram feature | C | — |
| `src/tools/cluster/axis_correlation.py` | 신규 후보 상관(기존 재사용) | C | — |
| `side-project/emoi-map-emotion-axes/phase-b0/README.md` | 연구 결과 report | C | — |
| `docs/working/HANDOFF.md` | 작업 5 행+섹션, 마지막 갱신 | A·B·C | — |

## 5. Verification (E2E)
1. **Phase A**: (라벨 편집 시) `python src/build.py` → 새로고침. 4모서리 축 라벨 정직 문구, 호버 툴팁 에너지%, 범례 칩. 회귀: 격자·HUD·재생 펄스 정상.
2. **Phase B**: precompute → `y_energy` 660곡·대체 centroid 확인 → `build.py`. 우상단 "정서/에너지" 토글:
   - 에너지 모드에서 **Millsage/Ikka 재배치** 확인(에너지 축 검증). 밴드 포커스·곡 클릭 재생·HUD "밝음 y"→"에너지 y" 스왑·라벨/부제 스왑·range 재계산.
   - 회귀: 정서 모드 복귀 동일. 줌/팬·onset 펄스·별밭 정상. 모바일 320px OK.
3. **Phase C**: hummingbird env, (완비 로컬)에서 전곡 feature 추출 → `axis_correlation.py` r 확인 → report.

## 6. 의존/순서 & 롤백
- 순서: **A(독립) → B(energy 완비 → 지금) → C(오디오·라벨 확보 후, 완비 로컬)**.
- 롤백: A=axes 텍스트 원복+build / JS 가드 off. B=`_clYMode` 기본 'mood' 고정(토글 숨김), `y_energy`는 남아도 무해(폴백). C=report/도구는 산출물이라 축 채택 전 프론트 무영향.
