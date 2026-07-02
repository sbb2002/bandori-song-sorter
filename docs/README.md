# docs/ 안내

용도별 4개 버킷으로 정리되어 있다.

| 폴더 | 용도 | 진입점 / 대표 문서 |
|------|------|--------------------|
| **working/** | 작업 시 자주 참고하는 문서 (남은 작업·완료 기록·활성 스펙·실험 보고서) | **[working/HANDOFF.md](working/HANDOFF.md)** = 남은 작업 단일 출처 |
| **idea/** | 사용자가 아이디어를 적어두는 인박스 (채택 시 HANDOFF로 이관, 반려 시 '반려사항'에 기록) | [idea/260625.md](idea/260625.md) |
| **legacy/** | 더 이상 사용하지 않는 v1 문서·구 디자인 목업·구버전 UI 스크린샷 | — |
| **user_manual/** | 현행 사용자 매뉴얼 스크린샷 (PC/모바일) | — |

## working/ 세부

- `HANDOFF.md` — **앞으로 할 일** 단일 출처(진입점). `done.md` — 완료 기록 아카이브. `urgent.md` — 서비스 차질 수준 긴급사항(있으면 HANDOFF보다 우선).
- `spec/` — 활성 구현 스펙. `audio-map-fullscale.md`(음원맵 전곡 확대 = 다음 작업), `audio-map-axes.md`(축 설계 근거), `audio-map-axes-comment.md`(축 자문·검토).
- `report/` — 클러스터 실험 보고서(재현·인용 근거). `cluster_experiment.md`, `cluster_audio_clap.md`, `cluster-correlation/`.

> 참고: `done.md`는 세션별 날짜 스냅샷 아카이브라 당시 경로 표기를 그대로 보존한다(구 `docs/spec/`·`docs/archive/` 등 문자열은 그 시점 기록).
