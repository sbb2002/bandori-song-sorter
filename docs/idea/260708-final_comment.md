# 260708 최종 코멘트 — EMOI-MAP 좌표계 돌파안 (fable × opus 통합)

> 원 문제: [260708.md](260708.md) · 통합 원본: [260708-fable_comment.md](260708-fable_comment.md) · [260708-opus_comment.md](260708-opus_comment.md)
> 두 코멘트는 상보적이다 — **fable = 진단(n=1 통계)·검정 설계·데이터 계약(rank/z) / opus = 실질 1.x차원 진단·구현 기획(파일·라인·env)·실행 단계**. 상충 3건은 §0에서 해소 근거와 함께 기록.
> 작성 2026-07-07 · 근거: [research](../research/cluster-map-extraction.md) · [report](../working/report/cluster_experiment.md) · cluster-correlation

---

## 0. 두 코멘트 대조 — 상충 해소 기록

| 쟁점 | fable | opus | 최종 판정 |
|------|-------|------|-----------|
| **bpm을 새 축 후보로?** | 재검정 가치 있음(E4) | 옥타브오류 r=0.05, 승격 불가 | **opus 채택** — `build_perceptual_map.py:62` 확인: `songs[].bpm` = `librosa.feature.tempo`(주석 "[실험] 옥타브 오류 가능") 그대로. Exp 6에서 r=0.05로 실패한 그 feature다. **E4 폐기**, 템포 축은 Phase C tempogram으로만 |
| **검정 표본** | 기존 n=28 라벨 재사용(반나절) | n=28 과소 → 라벨 표본 확대 전제 | **2단계 통합**: 스크리닝 = 기존 n=28(비용 0, base env) → \|r\| 유망(≥0.4) 시 극단 곡 추가 라벨로 확대 확정검정. 확대 없이 축 '정식 승격'은 안 함 |
| **축 라벨 처리** | 지각 단어 유지 + note 부기 | pos/neg 텍스트 자체 정직화 | **같은 방향, opus 구현안 채택**: 지각 단어는 유지하되 괄호로 실체 한정 — 검증된 이름(r=−0.81/+0.51)을 버리지 않으면서(fable 논거) 과대약속을 끊는다(opus 논거). `_clAxisLabels`가 pos/neg를 그대로 읽으므로 텍스트만 수정 |
| energy 토글 시점 | 검정 통과 후 승격 | 토글로 즉시(즉석 재검증 겸) | **절충**: 토글은 **'β(실험 축)' 표기로 즉시** 제공(Millsage·Ikka 재배치를 눈으로 검증) · HUD 정식 선언·승격은 검정 후 |
| small multiples | report용 OK | 프로덕션 비권장 | 양립 — **프로덕션 ✗ / report·문서 ○** |
| n=1 밴드 처방 | overrides·잠정 별·소멸 규칙 | (진단 한 줄만) | **fable 채택** — Phase A에 편입(§3) |
| LRA를 오디오 없이? | dyn.v p90−p10 근사(base env) | 정식 LRA는 Phase C(오디오) | **둘 다** — 근사를 Phase B0 스크리닝에, 정식은 Phase C에 |

이하는 해소 결과를 반영한 단일 결론이다.

---

## 1. 통합 진단 — 왜 Millsage·Ikka 좌표가 어색한가

어색함은 우연이 아니라 **세 겹의 문서화된 한계**가 1곡 밴드에서 동시에 노출된 것:

1. **[구조] n=1 중심점은 이 지도의 전제 밖** (fable): 돌파구(Exp 3) 자체가 "곡은 섞여도 **밴드 평균**은 또렷하다"였다. 곡 1개 좌표는 원래 지각과 자주 어긋나며(research Fig 2 "곡은 흩어지되 중심점은 정합"), 기존 밴드는 n=23~72의 평균이 노이즈를 씻었지만 두 밴드는 곡 1개가 그대로 대표값(`centroids n=1`). **어떤 축을 써도 남는 문제 → 전용 처방 필요(§3 Phase A).**
2. **[축] 실질 1.x차원** (opus): cluster-correlation에서 **contrast 하나가 '밝음(+0.56)'과 '거칢(−0.81)' 양쪽을 지배** — 명목 2D지만 곡이 대각선으로 퍼지는 실질 1.x차원. "경향성은 보이는데 개별 곡이 어색한" 근본 배경.
3. **[축] 기지의 두 구멍을 각각 저격**:

| 곡 | 좌표 | 지각 | 구멍 |
|----|------|------|------|
| millsage 起死開戦 | x=+13.9(거칢), y=−10.1 | 키보드 → '부드러움' | **x 프록시 한계**: contrast는 스펙트럼 대비이지 편곡 게슈탈트가 아님(ave_mujica 한계와 동계열). '매끄러움' 라벨이 과대약속 — 실체는 "맑음/무디스토션" |
| ikka ホーミー・タイッ！！ | x=+21.1, y=−9.3(어두움) | 밝은 펑크 | **y 반쪽 측정**: mode는 조성만. 경쾌함 = Exp 6 Fig 4의 **미측정 지각축 ②(energy≈tempo, 라벨 간 r=0.81)** — "②를 잡는 feature가 없다" |

결정적 단서(fable): Ikka의 **energy=0.921**(전곡 상위 8%, `add_energy.py` 기산출) — 이미 있는 값이 정확히 빠진 정보를 담고 있다. "단조지만 에너지 최상위"로 함께 읽히면 지각과 정합. → §2-3·Phase B의 출발점.

---

## 2. 3문항에 대한 통합 답

**1) 축 이름** — 지각 단어 유지 + 괄호 한정(정직화). 이름 자체는 손 라벨 검증을 통과한 명명이므로 유지하되, 이번 두 오독 지점을 괄호가 끊는다:
- x: `거칢 ↔ 매끄러움` → **`거칢 ↔ 매끄러움(음색 질감)`** — "리듬의 거칢"으로 읽히는 것 차단(Millsage 오독 지점).
- y: `밝음 ↔ 어두움` → **`밝음(장조) ↔ 어두움(단조)`** — "경쾌함=밝음" 기대 차단(Ikka 오독 지점).
- 재명명 본격 재논의는 energy 축 성립 후(경쾌함이 분리되면 y를 "명랑↔우수(조성)"로 더 좁힐 실익 발생).

**2) 다른 feature** — 기존 후보는 사실상 소진(f0·centroid·rolloff·flatness·flux·zcr·rms·librosa tempo·harmonic ratio·onset_rate 전부 붕괴/무효). 남은 후보를 **비용 순으로 2계층**:
- **무-오디오(onset JSON 파생, base env)**: E1 `mean(dyn.v)`(=현 energy 원천 — 단 rms 계열 실패 전력, 검정 필수) · E2 `p90−p10(dyn.v)`(**LRA 근사** — research §6 지목 후보의 저비용판) · E3 온셋 밀도. ~~E4 bpm~~(폐기 — librosa tempo 그 자체로 확인됨).
- **오디오 필요(hummingbird env, 완비 로컬)**: 정식 loudness range(pyloudnorm LUFS) · **tempogram** 기반 지각 템포.
- 분포 점검(원 질문): 전곡 히스토그램(라우드니스 평준화로 E1이 뭉치는지 여기서 판명) + 밴드 간/내 분산비 + Millsage·Ikka 스팟 체크. **신호가 나오면 report 전환**(Exp 7, `docs/working/report/cluster-energy-axis/`).

**3) 3+ 좌표 표현** — 좌표축을 늘리지 말고 **지도 1장 + 시각 채널 2개**:
- (a) **제3축 = 별 밝기** (작업 4로 이미 렌더 중) → 범례 명시("★ 밝기·크기 = 곡 에너지")로 승격. 검정 통과 시 "검증된 제3축"으로 선언.
- (b) **y축 토글**(조성 ↔ 에너지β) — 점 이동 애니메이션이 지도 간 대응을 이어 줌. 원안 "대표 feature 2~3개 지도"의 인터랙티브 흡수판.
- small multiples = report·스크린샷용만 · 3D 산점도 = 비권장(silhouette≈0 데이터에서 착시 증폭) · 밴드 클릭 레이더 카드(contrast·mode·energy) = 선택, 성운 포커스와 궁합.

---

## 3. 실행 계획 — opus 3단계에 fable 보완을 삽입한 4단계

> 데이터 현황: onset `dyn.v` **660/660** · `energy` baked **660/660** · `audio_full` 이 로컬 285/660, **완비 로컬 660/660**(메모리 `emoi-cluster-v4-status`). A·B0·B = base env·어느 로컬이든 / C = hummingbird env·완비 로컬.
> 편집 규칙: `16-audiomap.js`·`desktop.css` 직접수정(리빌드 ✗) · `audio_map.json` 변경 시만 `python src/build.py`.

### Phase A — 라벨 정직화 + energy 범례 + n=1 처방 (즉시 · 저비용)
- **축 라벨**: `audio_map.json.axes.{x,y}.{pos,neg}` 텍스트를 §2-1로 수정 → `_clAxisLabels`(16-audiomap.js:693)가 그대로 읽음. `build.py` 1회.
- **energy 노출**(JS만): 툴팁 formatter(16-audiomap.js:452–455)에 `· 에너지 NN%` + `_clBuildSensTabs`(216) 패턴 범례 칩 "★ 밝기 = 곡 에너지".
- **n=1 처방**(fable):
  - `overrides`에 morfonica 선례대로 투명 기록 — millsage `dx≈−15~−20` "키보드 매끄러움 미측정" · ikka `dy≈+15~+20` "펑크 경쾌함(에너지축) 미측정". nudge 크기는 두 곡을 기존 1~5 지각 스케일로 라벨 → 좌표 환산으로 산정(자의성 최소화).
  - **잠정 별**: `centroids[].n < 3`이면 중심 ★ 반투명·점선 + 툴팁 "n=1 · 잠정" — 별밭 컨셉 정합(관측 부족한 별=흐릿).
  - **소멸 규칙**: 신곡 파이프라인으로 n≥5 도달 시 override 재검토·제거(만료 조건을 why에 병기).

### Phase B0 — onset 파생 후보 스크리닝 검정 (반나절 · base env) ★fable 삽입
- E1·E2·E3 × **기존 n=28 energy·tempo 라벨**(`content/cluster/legacy/axis_labels_worksheet.csv`) 상관 — `axis_correlation.py` 방법론 재사용.
- 판정: \|r\|≥0.5 + 기존 축과 독립(contrast·mode와 \|r\|≲0.4) → 유망하면 Phase C에서 라벨 확대 확정검정 / 전멸이면 Phase C(오디오 필요 후보)로 직행.
- 분포 점검 산출물(히스토그램·밴드별)을 여기서 만들어 두면 report 전환 재료가 된다.
- ⚠️ **오디오 캐시 폐기 보류**: B0·C가 끝나기 전 완비 로컬의 `audio_full`을 폐기하지 말 것(전멸 시 정식 LRA·tempogram에 원본 필요 — 재수급 비용 큼).

### Phase B — y축 토글: 정서(mode) ↔ 에너지β (중간 · base env)
opus 구현안 그대로(상세 라인·함수 = opus 코멘트 §3-B), 두 가지만 보강:
- **데이터 계약(fable)**: 좌표용 값은 **raw `mean(dyn.v)`의 z-score**(`zscale` 재사용 → `songs[].y_energy`·`centroids[].y_energy`) — percentile rank는 거리 파괴 + 신곡마다 전곡 재배열이라 **norm 동결 원칙 위반, 좌표 불가**. rank는 별 밝기 전용으로 유지(의도된 이중화). z 파라미터는 `norm`에 동결 저장.
- **β 표기**: 토글 라벨을 "에너지(β)"로 — 검정 전임을 명시. B0에서 E2가 E1보다 우수하면 토글 축을 E2로 교체 가능(precompute만 변경).
- 프론트: `_clYMode`('mood'|'energy') + `_clYof`/`_clCentYof` 셀렉터, `_clDraw` y 참조 교체(565–568·575–576·594·597), 토글 시 `_clRangeKey=null`, 라벨·HUD·부제 스왑, `_clBuildYTabs()`(우상단 "정서/에너지β").
- 검증 포인트: **에너지 모드에서 Millsage·Ikka 재배치 확인**(Ikka 0.921 → 상단 이동이 지각과 맞는지 육안 검증).

### Phase C — 새 지각축 정식 연구 (연구 트랙 · 완비 로컬 · hummingbird env)
- `perceptual_features.py` 확장: 정식 **loudness range**(pyloudnorm 단기 LUFS 스프레드) + **tempogram** 지각 템포(자기상관 피크 — 옥타브오류 완화).
- **라벨 표본 확대**(에너지/템포 극단 곡 추가) 후 `axis_correlation.py` 확정검정 → report(`cluster-energy-axis/README.md`).
- 통과 시: β 뗌 → 별 밝기를 "검증된 제3축"으로 HUD 선언 + y 명칭 재논의(§2-1) + energy z 동결 확정.

---

## 4. 변경 파일 (통합)

| 파일 | 변경 | Phase | 리빌드 |
|------|------|-------|--------|
| `src/content/cluster/audio_map.json` | axes 텍스트 정직화 · **overrides 2건(millsage·ikka)** · `y_energy`/`axes_alt`/z 동결 | A·B | ✅ build.py |
| `static/js/functions/16-audiomap.js` | 툴팁 energy·범례 칩·**잠정 별(n<3)**(A) / y토글·라벨 스왑(B) | A·B | ❌ |
| `static/css/desktop.css` | 범례 칩·토글·잠정 별 스타일(필요 시) | A·B | ❌ |
| `src/tools/cluster/add_energy.py`(또는 신규) | raw z-score `y_energy`·대체 centroid·**E1~E3 스크리닝 출력** | B0·B | — |
| `src/tools/cluster/perceptual_features.py` · `axis_correlation.py` | LRA·tempogram feature·확정검정 | C | — |
| `docs/working/report/cluster-energy-axis/README.md` | 연구 report(신호 시 idea→report 전환) | B0·C | — |
| `docs/working/HANDOFF.md` | 작업 5 등록·갱신 | A~C | — |

## 5. 검증 (opus E2E 계승 + 추가)
1. **A**: `build.py` → 축 라벨 정직 문구 · 툴팁 에너지% · 범례 칩 · **Millsage·Ikka 중심 ★가 잠정 표기 + override 반영 위치**. 회귀: 격자·HUD·펄스·별밭.
2. **B0**: E1~E3 × n=28 상관표 + 분포 그림 산출 → 판정 기록.
3. **B**: `y_energy` 660 확인 → 토글에서 **Millsage·Ikka 재배치 육안 검증** · 정서 모드 복귀 동일 · 줌/팬·재생·모바일 320px.
4. **C**: 완비 로컬 전곡 추출 → r 확정 → report.

## 6. 순서·롤백
- 순서: **A(독립·즉효) → B0(반나절, B와 병행 가능) → B(energy 완비 → 지금) → C(완비 로컬·라벨 확대 후)**.
- 롤백: A = axes 텍스트 원복+build, overrides 삭제(투명 기록이라 안전), 잠정 별 가드 off / B = `_clYMode='mood'` 고정(토글 숨김), `y_energy` 잔존 무해 / C = 산출물 트랙이라 채택 전 프론트 무영향.
