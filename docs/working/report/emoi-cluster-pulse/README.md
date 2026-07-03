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

### tempo 옥타브 오류가 subdivision 선호의 진짜 원인 (2026-07-04 갱신)

처음엔 "tempo 로 자동 판정 불가"로 결론지었으나, **실제 BPM 을 확인하니 tempo 측정 오류가
원인**이었다. 아래 표의 `feature.tempo`·`beat_track` 은 둘 다 라이브러리 추정값이고,
`실제 BPM` 은 외부 확인값(사용자 제공):

| 밴드 | feature.tempo | beat_track | 실제 BPM | 선호 | 관계 |
|------|--------------|-----------|---------|------|------|
| afterglow (ON YOUR MARK) | 123 | 92.3 | **185** | 8분 | beat_track = 185÷2 (half 오류) |
| mugendai (アイの夢限) | 117.5 | 120.2 | **135** | 8분 | 배수도 아닌 근사 오류 |
| morfonica (Daylight) | 123 | 92.3 | ? | 박 | afterglow 와 측정값 동일 |
| mygo | 129 | 95.7 | ? | 박 | |
| hello_happy | 123 | 123 | ? | 박 | |
| ave_mujica | 136 | 132 | ? | 박 | |
| pastel | 144 | 144 | ? | 박 | |

- **afterglow**: beat_track 92.3 = 실제 185 의 **정확히 절반**. 그래서 8분음표(92.3×2=184.6≈185)
  가 실제 박 → "8분 선호"가 설명된다. (`feature.tempo(start_bpm=180)` 을 주면 184.6 으로 교정됨.)
- **mugendai**: 실제 135 인데 측정 117~120 — 옥타브(2배)도 아닌 어긋남. start_bpm 힌트도 무효.
- **결정적 난점**: afterglow(실제 185)와 morfonica(박 선호)는 **측정값이 완전히 동일**(beat_track
  92.3, IOI 최빈 0.15s). 측정만으론 둘을 구분할 수 없다 → **실제 BPM 없이는 자동 판정 불가**.
- IOI(inter-onset-interval) 최빈은 가장 촘촘한 연속(8분/16분)을 반영해 **박이 아닌 subdivision**
  을 가리킨다(afterglow 0.15s) → 박 추정엔 부적합.

### 해결 방안 (우선순위)

1. **실제 BPM 을 외부에서 확보 → 정확한 grid** ⭐권장.
   - 소스: songbpm.com·tunebat 등 스크래핑, MusicBrainz/AcousticBrainz, 또는 사용자 큐레이션.
   - 확보하면 grid = `실제 BPM` 기준(phase 는 beat_track/onset 으로 정렬), subdivision 큐레이션
     자체가 불필요해진다. `audio_map.json` 의 `bpm`(현재 feature.tempo 라 부정확)도 이 값으로 교체.
   - 리스크: 커버/편곡은 원곡 BPM 과 다를 수 있음 → 곡 단위 확인 필요.
2. **tempogram 다중 옥타브 후보 + 지각 폴딩** (보조·자동).
   - `librosa.feature.fourier_tempogram`/autocorr 에서 배수 후보(×½·×1·×2)를 나열하고 지각 tempo
     범위(≈100–200 BPM)로 폴딩해 옥타브를 고른다. afterglow 92.3→184.6 은 교정되나,
     morfonica 처럼 실제가 갈리는 경우는 여전히 한계(측정 동일).
3. **known-BPM 대조 교정 규칙**: 소수 곡의 실제 BPM 으로 측정 오차 패턴(예 특정 곡군은 beat_track×2)
   을 찾아 반영. 표본이 늘면 신뢰도 향상.
4. **현행 임시**: 실제 BPM 확보 전까지 '박' 고정 + 곡별 예외 큐레이션(`CL_ONSET_DEFDIV`).

→ **다음 단계 = 방안 1**: 전곡 실제 BPM 소스를 정해 `audio_map.json` 의 bpm 을 교체하고,
`build_beat_track.py` 가 beat_track 의 tempo 대신 그 BPM 으로 grid 를 생성하도록 개편.
(현재는 방안 4 상태 — 박 고정.)

---

## 미해결 / 향후

- **8분박 자동 판정 = tempo 옥타브 오류 문제**(위 "tempo 옥타브 오류" 절 참조): 근본 해결은
  **실제 BPM 확보(방안 1)** — 확보하면 subdivision 큐레이션 자체가 불필요. 확보 전까지는 '박'
  고정 + 곡별 예외(`CL_ONSET_DEFDIV`).
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
