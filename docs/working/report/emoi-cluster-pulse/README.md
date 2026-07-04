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

| 밴드 | feature.tempo | beat_track | 실제 BPM | 선호 | 원하는 pulse |
|------|--------------|-----------|---------|------|------|
| afterglow (ON YOUR MARK) | 123 | 92.3 | **185** | 8분 | 185 |
| morfonica (Daylight) | 123 | 92.3 | **185** | 박 | 92.3 |
| mugendai (アイの夢限) | 117.5 | 120.2 | **135** | 8분 | ? |
| mygo | 129 | 95.7 | ? | 박 | ~95 |
| hello_happy | 123 | 123 | ? | 박 | ~123 |
| ave_mujica | 136 | 132 | ? | 박 | ~132 |
| pastel | 144 | 144 | ? | 박 | ~144 |

- **핵심 반전(2026-07-04)**: afterglow 와 morfonica 는 **실제 tempo(185)·측정(92.3)·IOI(0.15s)가
  전부 동일**한데 원하는 펄스가 다르다 — afterglow=8분(185 pulse), morfonica=박(92.3 pulse).
  → tempo 로는(실제든 측정이든) **원리적으로 구분 불가**. 목표는 "정확한 tempo"가 아니라
  **곡에 어울리는 지각적 pulse rate**(= 사용자가 원하는 펄스 밀도)임이 드러난다.
- **afterglow**: 실제 185, 드럼이 꽉 차 185 pulse 가 두드러짐 → 8분(185). **morfonica**: 실제 185
  지만 강세가 92.3 간격(하프타임 느낌) → 박(92.3). **같은 tempo, 다른 지각 pulse.**
- **mugendai**: 실제 135 인데 측정 117~120 — 옥타브도 아닌 어긋남(변박/약한 다운비트). 난곡.
- IOI 최빈은 가장 촘촘한 연속(8분/16분)을 반영해 박이 아닌 subdivision 을 가리킴 → 박 추정 부적합.

### 해결 방안 — "지각 pulse rate" 추정 (2026-07-04, 목표 재정의)

**목표는 "정확한 악보 tempo"가 아니다.** afterglow·morfonica 는 실제 tempo 가 같아도(185) 원하는
펄스가 8분/박으로 다르다 → 맞춰야 할 것은 **곡에 어울리는 지각적 pulse rate**(사용자 선호 펄스 밀도).
외부 BPM(비공식·부재)은 정답이 아니라 sanity check 보조로만.

**A. 옥타브 후보 정합 스코어링 + 편향 보정** ⭐핵심 (실측 검증됨)
- onset envelope autocorrelation(ACF)으로 후보 pulse 와 옥타브(×½·×1·×2)를 스코어링.
- 관찰: **ACF 최고값은 느린 옥타브로 편향**(자기상관 배음). 단독으론 항상 절반을 고름.
- **옥타브 쌍 비율 규칙**: `ACF(빠름) ≥ ACF(느림) × τ` (τ≈0.9) 이면 빠른 쪽 채택. 이 **비율 자체가
  "빠른 pulse 가 얼마나 두드러지나" = 지각 pulse 지표**다.

  | 곡 | ACF(92) | ACF(185) | 비율 | 판정 pulse | 실제 tempo | 선호 |
  |----|---------|----------|------|-----------|-----------|------|
  | afterglow | 1.00 | 0.976 | 0.98 | **185** | 185 | 8분 ✓ |
  | morfonica | 0.989 | 0.828 | 0.84 | **92** | 185 | 박 ✓ |

  → **실제 tempo 는 둘 다 185 로 같지만**, ACF 비율이 지각 pulse(afterglow 185 / morfonica 92)를
    잡아 **둘 다 사용자 선호와 일치**. 이 방안은 "tempo 추정기"가 아니라 **지각 pulse 추정기**라서
    오히려 목표에 정확히 부합한다(정확 tempo 로는 원리적으로 구분 불가였던 케이스를 해결).

**B. 지각 prior + 앙상블**(강건화): `feature.tempo`·`beat_track`·ACF peak·`plp` 를 옥타브 정규화
  후 합의(중앙값/투표) + 지각 pulse 범위(≈90–185) 가중.

**C. 외부 BPM = 검증 보조**: 비공식이라도 소수 곡과 대조해 τ·prior 튜닝(정답 아님). 단 afterglow·
  morfonica 처럼 **실제 BPM 이 같아도 원하는 pulse 가 다르므로, 외부 BPM 을 grid 로 직접 쓰면 오히려
  틀린다**(morfonica 를 185 로 강제 → 박 선호와 어긋남). 외부 BPM 은 pulse 판정에 쓰지 말 것.

**한계**: mugendai(실제 135)는 ACF·tracker 가 모두 120 을 골라 실패(변박/약한 다운비트). 난곡은
  수동 큐레이션(`CL_ONSET_DEFDIV`).

**구현 방향**: `build_beat_track.py` 에 **지각 pulse 추정 함수**(ACF 후보 → 옥타브 비율 규칙 →
  prior/앙상블)를 넣어 beat_track tempo 대신 이 pulse 로 grid 를 만들고(phase 는 plp/onset 정렬).
  `audio_map.json` 의 `bpm`(feature.tempo)은 **음악 특징용이라 별개** — pulse 값과 혼동 말 것.
  검증 = A 의 τ 를 소수 정답 pulse(사용자 선호)로 튜닝.

**✅ 구현 완료 (2026-07-04, feature/emoi-cluster-v3b)** — `build_beat_track.py` `perceptual_pulse()`:
onset-envelope ACF 로 base(beat_track) 와 ×2 를 비교, `ratio = ACF(fast)/ACF(slow) ≥ τ` 이면
8분(div 2) 채택. onsets json 에 `pulse:{pulse_bpm,pulse_div,slow,fast,acf_slow,acf_fast,ratio,tau}`
저장. **τ=0.96**(아래 재튜닝 참조).

  파일럿 7곡 검증 (τ=0.96 · **6/7 선호 일치**):

  | 곡 | ratio | 판정 pulse | 선호 | |
  |----|-------|-----------|------|--|
  | afterglow | 0.976 | 185 (8분) | 8분 | ✅ |
  | mygo | 0.941 | 95.7 (박) | 박 | ✅ |
  | morfonica | 0.837 | 92.3 (박) | 박 | ✅ |
  | pastel | 0.824 | 143.6 (박) | 박 | ✅ |
  | hello_happy | 0.73 | 123 (박) | 박 | ✅ |
  | ave_mujica | 0.267 | 132.5 (박) | 박 | ✅ |
  | mugendai | 0.52 | 120.2 (박) | 8분 | ❌ 난곡(변박·약다운비트) |

  - **핵심 확인**: afterglow(0.976)·morfonica(0.837)는 **실제 tempo 가 둘 다 185 로 같은데** ratio 로
    8분/박을 정확히 갈랐다 — 정확 tempo 로는 불가능한 구분(방안 A 목표 달성). README 초안 표(0.98/0.84)
    와도 재현 일치.
  - **τ 재튜닝 0.9→0.96**: 초안 τ≈0.9 는 afterglow/morfonica 2곡만 본 값. **mygo(ratio 0.941, 선호 박)**
    가 τ=0.9 에서 8분으로 오검출 → 정답 경계 afterglow 0.976(8분) vs mygo 0.941(박) 사이인 **0.96**
    으로 상향, mygo 정정(6/7). ⚠️ 마진 좁음(0.941~0.976) → **전곡 확대 시 재검증 필요**(오버피팅 주의).
  - **mugendai** 만 실패: 빠른 pulse 가 ACF 로 안 두드러지는데 8분 선호(변박) = τ 로 불가 → 난곡 수동
    큐레이션(`CL_ONSET_DEFDIV`).
  - **남은 것**: 프론트(`16-audiomap.js`)가 `pulse.pulse_div` 를 기본 subdivision 으로 소비하도록 연결
    (현재는 `CL_ONSET_DEFDIV` 수동/‘박’ 고정) + 브라우저 렌더 검증.

---

## 미해결 / 향후

- **8분박 자동 판정 = 지각 pulse 추정 문제**(위 절 참조): 근본 해결은 **ACF 옥타브 비율로 지각
  pulse 추정(방안 A)** — 구현되면 subdivision 큐레이션 불필요. 그 전까진 '박' 고정 + 예외
  (`CL_ONSET_DEFDIV`). ※ 외부 BPM 을 grid 로 직접 쓰면 안 됨(morfonica: 실제 185 지만 박 선호).
- **전곡 확대**: `build_pulse_all.py` 로 배치. 단 (1) demucs 가 CPU 곡당 ~45s → 수백 곡은 수 시간
  (오디오 수집 완료 후 무인 배치), (2) onsets 총량이 커지면 index.html 인라인이 무거워짐 →
  **곡별 lazy fetch**(재생 시 해당 곡 json 만 로드)로 전환 필요. 로컬 검증은 http server 필요.
- **볼륨 5단계 구간·프리셋** 미세조정 여지(`CL_PULSE_R5`, `_clVolStep` 경계).
- 파일럿 캐시(`audio_drums/`)는 gitignore(대용량). 다른 장치에선 `separate_drums.py` 재실행 필요.

## 향후 아이디어 — 곡 구조 기반 section별 리듬 패턴 (2026-07-04 제안)

**착상**: 노래는 intro–verse–chorus… 구조를 띠고, section 마다 드럼 리듬 패턴이 반복된다.
구조를 읽어 **각 section 의 반복 리듬 패턴을 그 구간에 적용**하면 전역 tempo/정박에 덜 의존한다.

**왜 유망한가 = 지각 pulse 의 자연 확장**
- 지금까지의 결론은 "pulse 는 곡마다 하나"(전곡 '박' 또는 곡별 8분 큐레이션). 하지만 pulse 는
  **곡 내에서도 section 별로 변한다** — verse 는 차분(박), chorus 는 꽉 참(8분/16분).
- afterglow 를 '8분'이 낫다고 느낀 것도 특정 section(후렴)일 가능성. 전곡 단일 subdivision 으로
  억지 통일하던 것을 **곡 내 다이나믹스**로 푼다 → morfonica/afterglow 같은 곡별 상반도 흡수.

**기술 경로**
- 구조 분할: `librosa.segment`(recurrence/self-similarity matrix, novelty), laplacian segmentation,
  또는 MSAF. → intro/verse/chorus 경계.
- section 별 패턴: 각 구간 국소 autocorrelation 으로 반복 주기 + 드럼 onset 시퀀스 → 대표 1–2마디
  패턴. 그 패턴을 구간에 반복 배치해 펄스 이벤트 생성.
- 전역 tempo 추정(옥타브 오류)을 **국소 반복 주기**로 대체 → 옥타브 문제 상당 부분 우회.

**한계·리스크**
- "정박 완전 무관"은 아님: 반복 패턴 **단위 길이**(마디/박)는 여전히 필요.
- 구조 분할 정확도(경계 오검출) + SSM 계산 비용.

**순서 제안**: 우선 방안 A(전곡 단일 지각 pulse)를 검증·구현한 뒤, 그 pulse 추정을 **section 단위로
국소 적용**하는 방식으로 확장하는 게 점진적이고 안전하다(A 가 section 내 pulse 추정의 부품이 됨).

### 구체화 (2026-07-04, millsage 타당성 프로브)

**동기 재정의**: 진짜 표적은 뮤타입이 아니라 **millsage(매스락)** 이다. 변칙 리듬패턴(변박·폴리리듬)이
잦아 전역 단일 pulse 전제가 근본적으로 깨진다. 또한 **신뢰할 tempo ground-truth 가 없다** — 뮤타입을
135로도 120으로도 잴 수 있는데, 아래 프로브가 그 이유(단일 정답 tempo 부재)를 실증한다.

**프로브 v1 — naive 국소 지배 tempo (실패)**: full-mix onset envelope → tempogram 프레임별 argmax.
- 지배 BPM std: millsage **32.8** vs poppin(대조군) **45.0** → *대조군이 더 큼 = 판별 실패*.
- 원인: 변동의 대부분이 진짜 박자 변화가 아니라 **옥타브/배음 모호성**(전역 방안의 그 적).
- **교훈**: "ACF 를 국소화만" 하면 옥타브 문제를 그대로 물려받는다. 방안 A 의 옥타브-강건 규칙을
  반드시 **구간 안으로** 가져가야 한다. → `figures/section_probe_v1_naive_octave.png`

**프로브 v2 — 옥타브 접기([90,180)) (결정적 분리)**:

| 지표 | millsage #179 | poppin #375 (대조) |
|---|---|---|
| 접은 pulse **구간간 편차**(6등분 중앙값의 std) | **24.9 BPM** | **2.6 BPM** (~10배) |
| 6구간 지배 pulse | 161·161·117·112·172·172 | 92·92·92·92·92·99 |
| 상위2피크 비율 성격 | **헤미올라(≈1.5) 54%**, 옥타브 16% | 옥타브(≈2.0) 52%, 헤미올라 19% |
| median 피크비율 | **1.53** (3:2) | 2.00 (2:1) |

`figures/section_probe_v2_folded.png` — poppin 은 92 한 줄에 고정, millsage 는 112↔172 를 토글하며
그 균형이 구간마다 이동.

**해석 = millsage 문제의 정체**: "tempo 가 시간에 따라 변한다"가 아니라, **어느 순간에도 3:2 로 경쟁하는
두 pulse(112·172)가 공존하고, 어느 쪽이 체감 박인지가 구간마다 바뀐다.** 전역 단일 pulse 는 원리적으로
불가. poppin 은 경쟁 피크가 2:1 clean 배음(= 한 pulse 의 subdivision) → 전역 하나로 충분.

**확정 설계 (방안 B, 4단계)**:
1. **구간화**: 6등분 슬라이딩창만으로도 편차 24.9 를 포착했다 → *의미적 intro/verse/chorus 분할은
   필수 아님*. 저비용 **고정/슬라이딩 시간창**으로 시작하고, 원하면 `librosa.segment` 경계로 스냅.
2. **구간별 pulse = 방안 A 국소 적용 + 옥타브 접기 + 상위2피크 비율 판정**. 비율 ≈1.5 면 폴리메트릭
   구간으로 인식(두 pulse 병존), ≈2.0/3.0 이면 단일 pulse 의 subdivision.
3. **대표 패턴**: 구간 내 국소 pulse 로 beat-sync 평균 → 그 구간 드럼 groove(킥/스네어/하이햇 위치)
   1–2 마디 템플릿. (개별 onset 검출이 아니라 *주기성* 이라 세대3 plateau 함정 회피.)
4. **기존 프리셋 렌더 그대로 소비**: 패턴을 구간에 타일링해 `{t,v}` 이벤트 생성 → 볼륨 프리셋
   (1/2/3단계) 렌더러 무변경.

**효율 게이트(중요)**: 전곡을 section 처리할 필요 없다. **진단 패스**(v2 = librosa 만, demucs 불필요)로
*구간간 편차 > τ_seg(예: 10 BPM)* 인 곡만 flag → 그 소수만 방안 B 적용, 나머지(poppin 류)는 방안 A 전역
유지. **660 재빌드 불필요, 증분 추가.**

**미해결**: (a) 폴리메트릭 구간에서 두 pulse 중 '체감 박' 선택 규칙 — 드럼 킥/스네어 백비트 정렬을
tie-break 후보. (b) 렌더 onset 포맷 확장 — `sections[]{t0,t1,pulse,div,pattern}` vs 평탄화 `events[]`.

**순서**: Phase0 방안 A 전곡 추출(진행 중) → Phase1 진단 게이트(cheap) → Phase2 flagged 곡 section
파이프라인 → Phase3 패턴+렌더 포맷. **벤치마크 곡 = millsage #179**(성공 판정: 구간별로 112/172 를
올바로 전환).

## 최종 구현 — 에너지 기반 동적 subdivision (2026-07-05, 채택 · 방안 B 대체)

방안 B(구간 tempo period 국소화)는 **프로토타입까지만**(`section_pulse_proto.py`: millsage 172↔112 구간 검출 확인). 실제 채택은 더 단순·견고한 **에너지 기반 동적 subdivision**.

**착상(사용자)**: 곡 구조(intro/verse/chorus) 판별은 과함. **에너지(음량)만으로** subdivision 제어 — 조용(intro/outro/브레이크다운/잔잔한 1절)=박, 고조=8분. 구조 검출 실패(특히 millsage 같은 매스락)에 안 걸리고 전곡 동일 적용.

**진단 게이트**(`diagnose_pulse_variability.py`): full-mix tempogram → **옥타브 원(circular) spread**로 곡내 pulse 변동 측정(linear std는 90 BPM fold 경계에서 89↔92를 92↔178로 쪼개는 위양성 → circular로 해결). 전곡 스캔 `pulse_variability.csv`: ~70% 안정(spread<4), ~22%만 방안 B급 변동.

**정규화 = 글로벌 절대음량(핵심)**: 처음엔 곡별(per-song) intensity 정규화 → **곡 간 절대 energy 차이가 뭉개짐**(Symbol I처럼 시종 시끄러운 곡에 박 오지정). 검증: ave_mujica `Symbol I`(절대 −8dB 평탄, 시종 에너지) vs roselia `軌跡`(1절 −18~−22dB, 조용) → 두 곡이 반대로 나와야 함. `build_dynamics.py`가 RMS dB를 **글로벌 앵커(−22~−7dB; 카탈로그 프레임 p10~p90 = −14.5~−8.9dB 압축분포 기준)**로 정규화 → onset JSON `dyn`(2Hz). 결과: Symbol I = 시종 dense, 軌跡 1절 = 박.

**렌더**: `16-audiomap.js _clDynLevel`이 매 프레임 `dyn` 임계(`CL_DYN_T1`0.37 ≈ −16.5dB / `CL_DYN_T2`0.83)로 레벨 선택, 변화 시 재-bisect, 히스테리시스. `CL_DYN_MAX=1`(박/8분 — 16분은 과함). 3레벨 그리드는 이미 추출돼 있어 선택만.

**볼륨 프리셋 4단계**(`_clVolStep` 경계 0.2/0.4/0.6): 1·2 = 발생 안 함 · 3(0.6~0.9) = 24px·두께3px · 4(0.9~1.0) = 48px·두께7px(`CL_PULSE_R3/LW3/SPEED3`). 경계는 **곡 최대볼륨(`_clOnsetVmax`) 상대화**(`CL_VOL_ADAPTIVE`) — 각 곡이 프리셋 범위를 일관되게 사용.

**두 축 정리**: **밀도**(얼마나 자주 = subdivision) ← 글로벌 **절대** energy(음량). **크기·두께**(얼마나 세게 = 프리셋) ← 곡내 **상대** volume. 정규화 방향이 반대인 게 의도적(밀도는 곡 간 비교, punch는 곡 내 비교).

**버그수정**: 프리롤 광고 중 `getCurrentTime` 진행으로 onset 오발화 → `getDuration()`이 트랙 길이 ±5s(`CL_ONSET_DUR_TOL`)일 때만 발화.

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
