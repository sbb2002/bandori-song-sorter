# research — 음원맵 실험 여정 논문 모음

`bandori-song-sorter`의 음원맵(F2) 관련 실험 중, **꽤 고민했던 탐색 과정**을 abstract paper 형식으로 정리한 문서 모음이다. 각 논문은 "무엇을 시도했고, 무엇이 실패했으며, 왜 지금 방식으로 귀결됐는지"를 수치·그림과 함께 순서대로 남긴다.

## 수록 논문

| 논문 | 주제 | 한 줄 요약 |
|------|------|-----------|
| [**cluster-map-extraction.md**](cluster-map-extraction.md) | 음원맵 **좌표** 추출 | 가사 의미로는 밴드가 안 갈린다 → 음원 밴드중심(LOO 61%) → 해석 가능한 지각축(x=contrast, y=mode) 발굴 |
| [**pulse-onset-extraction.md**](pulse-onset-extraction.md) | 재생 **펄스** 온셋 추출 | BPM등간격→onset검출→beat그리드, 그리고 "정확 tempo가 아니라 지각 pulse rate"라는 재정의(ACF 옥타브 비율) |
| [**emotion-axes-extraction.md**](emotion-axes-extraction.md) | 정서축(**arousal**) 추출 시도 | Russell V-A로 재해석 → 정식 오디오 feature로도 arousal 독립축 불가("실질 1.x차원") → x=timbre·y=valence 확정 |

---

## 작성 규칙 · 양식

새 논문은 이 규칙·양식을 따른다. (문서 전반 규칙은 [`../working/readme.md`](../working/readme.md) 참조 — research는 그 표의 "다듬은 연구 논문" 칸.)

### 언제 research로 쓰나
- **한 아이템에 2회 이상 분석을 시도했고, 그 아이템이 종결됐을 때** done·report를 종합해 승격한다(문서화 경로 규칙 = [`../working/readme.md`](../working/readme.md) 「구현 유형별 문서화 경로」). 가설 → 여러 시도(실패 포함) → 전환 → 귀결의 서사가 대상. **1회 분석·단순 완료는 report/done에 남기고 승격하지 않는다.**
- **1 논문 = 1 여정**(하나의 질문에서 출발해 하나의 결론으로). 진행 중인 조사는 `working/report/<주제>/`에 두고, **종결된 뒤** 종합·정제해 올린다. **그림·표·플롯은 모두 포함**한다.

### 파일·위치
- `docs/research/<주제>-extraction.md` (kebab-case). 그림은 `figures/<주제>_figN_*.png`.
- 상세 표·중간 수치·원본 데이터는 research 본문에 복붙하지 말고 **report로 링크**(research는 서사+핵심 수치+그림).

### 필수 구조 (이 순서)
1. **제목** — "A에서 B까지" 식으로 여정을 한 줄에.
2. **초록 (Abstract)** — 3~5문장: 던진 질문 · 핵심 전환 · 결론.
3. **1. 동기 (Motivation)** — 왜 이 문제인가, 기존 방식의 무엇이 어긋났나.
4. **2. 재료와 방법 (Materials & Methods)** — `2.1 데이터`(n·출처) · `2.2 지표`(정직성/검증 기준: r·p·정확도 등 무엇으로 합격을 판정하는가).
5. **3. 실험 여정 (Experiments, in order)** — `Exp 0, 1, 2 …`를 **시간순**으로. 각 Exp 제목 끝에 **판정 이모지**(❌ 신호 없음 / ⚠️ 부분 / 🎯 돌파). **음의 결과도 반드시 항목으로 남긴다.**
6. **4. 전환점 (Turning point)** — 관점이 뒤집힌 지점(있을 때만).
7. **5. 최종 방법과 구현 (Final Method)** — 채택안 + 동결 파라미터/상수.
8. **6. 한계 (Limitations)** — 표본 크기·일반화·미해결 지점.
9. **7. 재현 (Reproduction)** — 실행 명령을 코드블록으로. 음원 등 로컬 전용 자산은 그 사실을 표기.
10. **하단 서명** — `*작성 YYYY-MM-DD · 브랜치 xxx*`(갱신 시 `· 갱신 …` 덧붙임).
- 최종 결정은 **채택 (Adopted)** 소절로 굵게 못박는다.

### 문체·공통 원칙
- **시간순 서사**: "무엇을 시도 → 무엇이 실패 → 왜 지금 방식"을 순서대로. 결론만 나열하지 않는다.
- **수치·그림 동반**: 모든 주장에 숫자(r/p/정확도/n). 핵심 그림은 상단 그림 목록에 ★.
- **절대 날짜·커밋 해시** 명시(상대표현 금지 — working/readme.md 공통 규칙 계승).
- **음의 결과 보존**: 실패한 시도가 다음 판단의 자산 → 지우지 않는다.
- 새 논문·그림을 추가하면 이 README의 **수록 논문 표 + figures 목록**에 한 줄씩 갱신한다.

---

## 그림 (figures/)

실제 데이터(660곡 좌표, 파일럿 드럼 스템 ACF)와 검증 리포트 수치로 생성. 생성 스크립트는 재현용으로 남겨두지 않았으나 각 논문 §재현에 파이프라인이 기록돼 있다.

- `cluster_fig1_signal_progression.png` — 가사 단위별 밴드 신호 vs 밴드중심 LOO 도약
- `cluster_fig2_audiomap_660.png` — 최종 660곡 지각 음원맵 산점도 ★
- `cluster_fig3_axis_correlation.png` — 축 검증 상관(f0 실패 vs contrast/mode 승리)
- `cluster_fig4_label_matrix.png` — 지각 라벨 2D 붕괴 상관행렬
- `pulse_fig2_acf_octave.png` — ACF 옥타브 편향(afterglow vs morfonica, 같은 tempo 다른 pulse) ★
- `pulse_fig3_ratio_threshold.png` — τ=0.96 파일럿 검증
- (emotion-axes 그림은 `../working/report/emotion-axes/phasec_screening.png`에 원본 보관 — figures 미승격)

## 원자료 (상세 데이터·표)

이 논문들은 아래 작업 리포트를 종합·요약한 것이다. 전체 표·중간 실험은 원자료 참조:

- [`../working/report/cluster_experiment.md`](../working/report/cluster_experiment.md) — 가사→음원 P0~P5 전 단계
- [`../working/report/cluster-correlation/README.md`](../working/report/cluster-correlation/README.md) — 축 재정의 상관분석 1·2차
- [`../working/report/cluster_audio_clap.md`](../working/report/cluster_audio_clap.md) — librosa vs CLAP 백엔드 비교
- [`../working/report/emoi-cluster-pulse/README.md`](../working/report/emoi-cluster-pulse/README.md) — 재생 펄스 방법론 진화
- [`../working/report/cluster-energy-axis/README.md`](../working/report/cluster-energy-axis/README.md) — B0 onset 스크리닝(전멸) · [`../working/report/emotion-axes/`](../working/report/emotion-axes/) — Phase C 정식 feature 검증

---

*작성 2026-07-04 · 갱신 2026-07-08(작성 규칙·양식 추가 · emotion-axes 등재) · 브랜치 `fix/emoi-map-labels-pulse`*
