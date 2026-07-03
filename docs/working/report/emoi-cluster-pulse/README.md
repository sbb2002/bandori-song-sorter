# 음원맵 재생 펄스 (emoi-cluster-pulse)

음원맵(F2)에서 **재생 중인 곡의 위치에 박자에 맞춰 펄스(물결)를 방출**하는 시각 연출.
HANDOFF 백로그 "재생 이퀄라이저 애니메이션"의 **B안(lazy 사전계산)** 구체화 — 실시간 오디오
분석이 아니라 **캐시 음원을 사전 분석**해 이벤트 트랙을 만들고, 유튜브 재생 타임스탬프
(`player.getCurrentTime()`)에 맞춰 프론트가 재생(playback)한다.

작성: 2026-07-04 (파일럿 · afterglow 외 7밴드 대표곡 1곡씩). 브랜치 `feature/emoi-cluster-v3b`.

---

## 결론 요약 (현재 채택 방식)

- **beat 그리드 방식**: `librosa.beat.beat_track` 으로 각 박 타임스탬프(실제 곡 pulse 위상 정렬)
  + 각 박의 **드럼 볼륨(RMS)을 5단계**로 나눠 펄스 크기·전파속도 결정.
- 드럼만 반응하도록 **demucs 로 드럼 스템 분리** 후 분석(기타·보컬 무반응).
- subdivision(박/8분/16분) 중 **'박' 고정**. 8분이 나은 곡도 있으나(afterglow·mugendai)
  tempo·bpm 으로 자동 판정 불가 → 향후 패턴 발견 시 곡별 예외 큐레이션.
- 파이프라인: `separate_drums.py` → `build_beat_track.py` → `build.py`(인라인).
  전곡 배치는 `build_pulse_all.py`.

## 파이프라인 / 파일

| 파일 | 역할 |
|------|------|
| `src/tools/cluster/separate_drums.py` | demucs 로 드럼 스템 분리 → `audio_drums/<band>__<idx>.wav` |
| `src/tools/cluster/build_beat_track.py` | 드럼 스템 → beat 그리드 트랙 `onsets/<band>__<idx>.json` (subdivision 박/8분/16분 + 볼륨) |
| `src/tools/cluster/build_pulse_all.py` | 위 둘을 매니페스트 전곡 순회(멱등 배치) |
| `src/build.py` `load_onsets()` | `onsets/*.json` → `window.CLUSTER_ONSETS` 로 index.html 인라인 |
| `static/js/functions/16-audiomap.js` | 재생 타임스탬프 폴링 → 펄스 방출(`_clOnsetTick` 등) |

트랙 스키마: `{sr, dur, tempo, levels:[{name, div, n, events:[{t, v}]}]}`
(`t`=시각초, `v`=볼륨 0~1 정규화). 감도/onset 방식 시절의 `k`(킥/스네어)는 폐기.

## 프론트 주요 상수 (16-audiomap.js)

- `CL_PULSE_BPM` — 실험 전체 on/off (false = 기존 고정 effectScatter 로 복귀, **롤백 스위치**).
- `CL_ONSET_TABS` — 감도/subdivision 탭 UI 표시(실험용, **메인 버전에선 false**).
- `CL_PULSE_R5 = [16,24,32,40,48]` — 볼륨 5단계 펄스 반경(px).
- `CL_PULSE_SPEED`, `CL_PULSE_DUR_MAX` — 전파속도 상한·지속 상한.
- `CL_ONSET_PILOT` — songKey → 트랙 id 매핑(파일럿 7곡).
- `CL_ONSET_DEFDIV` — 곡별 기본 subdivision(현재 비움 = 전곡 '박').

---

## 방법론 진화 (왜 지금 방식인가)

### 1) BPM 등간격 펄스 → 폐기
`rippleEffect.period = 60/bpm`. 위상(phase)을 무시해 실제 비트와 어긋나고, 빠른 곡은 부산스러움.
계단식 박 묶음(>150 BPM은 마디당 1회 등)·전역 배율(`CL_PULSE_SCALE`)로 다듬었으나 근본 해결 안 됨.

### 2) 커스텀 zrender 펄스
effectScatter 의 연속 물결은 '발생 간격'과 '퍼지는 속도'가 `period` 하나로 묶여 분리 불가.
→ 박 타이밍마다 zrender 원을 그려 짧게 커지며 사라지게(간격·속도 분리). 박자감 확보.

### 3) onset 검출 (demucs 드럼) → 폐기
"기타·보컬에 반응한다" → demucs 로 드럼 스템 분리. 이후:
- 하이햇 연타로 과다 → 저역통과 + `delta`/`vmin` 임계.
- 킥/스네어 대역 분리 검출 + 저역/고역 flux 로 분류(프리셋 구분).
- **치명적 한계**: 연속 균일 타격 구간은 onset envelope 이 **plateau** 가 되어 상대 peak(delta)로
  개별 히트를 못 잡음 → 둔감에서 통째로 놓침, 민감하면 다른 구간 과다. (HOP 512→256 으로
  시간해상도를 높이면 상당히 개선되나, "실제로 친 것"을 쫓는 접근 자체가 불안정.)

### 4) beat 그리드 (채택)
onset 검출을 버리고 **규칙적 박 그리드**로 전환:
- `beat_track` 은 실제 곡 pulse 위상에 정렬(등간격 아님, drift 없음).
- 조용/시끄러운 구간 상관없이 **항상 박에 존재** → 놓침·과다 없음.
- 세기는 **각 박의 볼륨(5단계)** 으로 → 조용한 박은 작게, 강한 다운비트는 크게·묵직하게.

---

## 주요 발견

### demucs `torchcodec` 우회
torchaudio 2.12 는 `ta.load` 가 `torchcodec` 을 요구(미설치 → 실패). **오디오를 librosa 로
로드해 텐서로 직접 `apply_model`** 하면 우회된다(`separate_drums.py`). 모델은 htdemucs(CPU).

### HOP 512 → 256 (연속 타격 분리)
onset 방식 시절, HOP512(23ms) 는 빠른 연속 타격(예 8초 인트로 필인)을 뭉갰다. HOP256(12ms)
으로 시간해상도를 높이니 같은 delta 로도 개별 히트가 살아남(afterglow 8초 구간 1개→6~10개).
beat 방식에도 HOP256 유지.

### tempo 로는 subdivision 을 자동 판정할 수 없다 (데이터)
사용자 청취 선호 vs 수치:

| 밴드 | 원곡 bpm | beat_track | 비율 | 선호 |
|------|---------|-----------|------|------|
| afterglow | 123 | 92.3 | 1.33 | **8분** |
| morfonica | 123 | 92.3 | 1.33 | 박 |
| mygo | 129 | 95.7 | 1.35 | 박 |
| mugendai | 117 | 120 | 1.00 | **8분** |
| hello_happy | 123 | 123 | 1.00 | 박 |
| ave_mujica | 136 | 132 | 1.03 | 박 |
| pastel | 144 | 144 | 1.00 | 박 |

비율 1.33 이 같은 afterglow·morfonica·mygo 인데 afterglow 만 8분, 비율 1.0(정확)인 mugendai 는
오히려 8분. **bpm·tempo·비율 어느 것도 선호를 예측 못 함** → 자동화 불가, 곡별 큐레이션이 정확.

---

## 미해결 / 향후

- **8분박 자동 판정**: afterglow·mugendai 처럼 8분이 나은 곡의 공통 패턴 미발견(위 표).
  아이디어 생기면 `CL_ONSET_DEFDIV` 에 규칙/예외로 반영. 현재는 전곡 '박' 고정.
- **전곡 확대**: `build_pulse_all.py` 로 배치. 단 (1) demucs 가 CPU 곡당 ~45s → 수백 곡은 수 시간
  (오디오 수집 완료 후 무인 배치), (2) onsets 총량이 커지면 index.html 인라인이 무거워짐 →
  **곡별 lazy fetch**(재생 시 해당 곡 json 만 로드)로 전환 필요. 로컬 검증은 http server 필요.
- **볼륨 5단계 구간·프리셋** 미세조정 여지(`CL_PULSE_R5`, `_clVolStep` 경계).
- 파일럿 캐시(`audio_drums/`)는 gitignore(대용량). 다른 장치에선 `separate_drums.py` 재실행 필요.

## 파일럿 결과 (7밴드 대표곡, HOP256)

| 밴드 (곡) | tempo | 박(초당) | 8분 | 16분 | 기본 |
|-----------|-------|---------|-----|------|------|
| afterglow (ON YOUR MARK) | 92.3 | 1.5 | 3.0 | 6.0 | 박(선호 8분) |
| ave_mujica (KiLLKiSS) | 132.5 | 1.7 | 3.4 | 6.8 | 박 |
| hello_happy (キミがいなくちゃっ！) | 123.0 | 1.9 | 3.9 | 7.7 | 박 |
| morfonica (Daylight) | 92.3 | 1.5 | 3.0 | 6.0 | 박 |
| mugendai (アイの夢限) | 120.2 | 1.9 | 3.8 | 7.6 | 박(선호 8분) |
| mygo (迷星叫) | 95.7 | 1.4 | 2.8 | 5.5 | 박 |
| pastel (TITLE IDOL) | 143.6 | 2.3 | 4.7 | 9.4 | 박 |
