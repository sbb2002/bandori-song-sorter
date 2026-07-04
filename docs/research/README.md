# research — 음원맵 실험 여정 논문 모음

`bandori-song-sorter`의 음원맵(F2) 관련 실험 중, **꽤 고민했던 탐색 과정**을 abstract paper 형식으로 정리한 문서 모음이다. 각 논문은 "무엇을 시도했고, 무엇이 실패했으며, 왜 지금 방식으로 귀결됐는지"를 수치·그림과 함께 순서대로 남긴다.

| 논문 | 주제 | 한 줄 요약 |
|------|------|-----------|
| [**cluster-map-extraction.md**](cluster-map-extraction.md) | 음원맵 **좌표** 추출 | 가사 의미로는 밴드가 안 갈린다 → 음원 밴드중심(LOO 61%) → 해석 가능한 지각축(x=contrast, y=mode) 발굴 |
| [**pulse-onset-extraction.md**](pulse-onset-extraction.md) | 재생 **펄스** 온셋 추출 | BPM등간격→onset검출→beat그리드, 그리고 "정확 tempo가 아니라 지각 pulse rate"라는 재정의(ACF 옥타브 비율) |

## 그림 (figures/)

실제 데이터(660곡 좌표, 파일럿 드럼 스템 ACF)와 검증 리포트 수치로 생성. 생성 스크립트는 재현용으로 남겨두지 않았으나 각 논문 §재현에 파이프라인이 기록돼 있다.

- `cluster_fig1_signal_progression.png` — 가사 단위별 밴드 신호 vs 밴드중심 LOO 도약
- `cluster_fig2_audiomap_660.png` — 최종 660곡 지각 음원맵 산점도 ★
- `cluster_fig3_axis_correlation.png` — 축 검증 상관(f0 실패 vs contrast/mode 승리)
- `cluster_fig4_label_matrix.png` — 지각 라벨 2D 붕괴 상관행렬
- `pulse_fig2_acf_octave.png` — ACF 옥타브 편향(afterglow vs morfonica, 같은 tempo 다른 pulse) ★
- `pulse_fig3_ratio_threshold.png` — τ=0.96 파일럿 검증

## 원자료 (상세 데이터·표)

이 논문들은 아래 작업 리포트를 종합·요약한 것이다. 전체 표·중간 실험은 원자료 참조:

- [`../working/report/cluster_experiment.md`](../working/report/cluster_experiment.md) — 가사→음원 P0~P5 전 단계
- [`../working/report/cluster-correlation/README.md`](../working/report/cluster-correlation/README.md) — 축 재정의 상관분석 1·2차
- [`../working/report/cluster_audio_clap.md`](../working/report/cluster_audio_clap.md) — librosa vs CLAP 백엔드 비교
- [`../working/report/emoi-cluster-pulse/README.md`](../working/report/emoi-cluster-pulse/README.md) — 재생 펄스 방법론 진화

---

*작성 2026-07-04 · 브랜치 `feature/emoi-cluster-v3b`*
