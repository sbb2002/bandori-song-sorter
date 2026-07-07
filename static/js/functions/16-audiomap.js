// ===========================================================
// BanG Dream! Song Sorter — 16-audiomap.js
// §14.6 음원맵(F2) ECharts 산점도 + 유사곡
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 14.6 Band audio map (F2) — ECharts 음악 음원 2D 산점도 + 유사곡 탐색
// ───────────────────────────
// 점=곡, 큰 라벨 점=밴드 중심점. 색=밴드 퍼스널 컬러.
// 좌표축 = 사용자 손 라벨로 검증한 지각 feature(build_perceptual_map.py):
//   x = spectral contrast → 거칢↔매끄러움 (검증 r=−0.81)
//   y = mode(장/단조)     → 어두움↔밝음  (검증 r=+0.51)
// PCA가 아니라 두 지각축을 직접 좌표로 사용(원점=평균 곡). 축 재정의 실험:
// docs/working/report/cluster-correlation, 이전 PCA/식별 실험: docs/working/report/cluster_experiment.md.
// 곡 클릭=재생(곡 리스트 선택과 동일)·밴드 원 클릭=그 밴드 곡 강조. CLAP 유사곡 데이터
// (songs[i].sim)는 JSON에 보존하되 표시는 하지 않음(근접=유사가 이 지도엔 더 자연스러움).

let _clusterChart = null;
let _clHover = null;               // ALL 모드에서 호버 중인 밴드(센트로이드) → 그 밴드 확장 미리보기
let _clRangeKey = null;            // 마지막 적용 축범위 키(포커스 밴드/'ALL') — 호버·재생 시 줌 리셋 방지
let _clPulseTimer = null;          // [실험] 박 타이밍 setInterval id(커스텀 펄스)
let _clPulseKey = null;            // [실험] 현재 펄스 대상(곡@주기) — 재draw 시 리듬 리셋 방지
let _clPlay = null;                // [실험] 재생 곡의 지도 좌표/색 { val:[x,y], color }
let _clOnset = null;               // [파일럿] 로드된 onset 트랙 { events:[{t,v,sus}] }
let _clOnsetIdx = 0;               // 다음 발생할 이벤트 포인터
let _clOnsetKey = null;            // 현재 트랙의 곡 key(중복 시작 방지)
let _clOnsetLastNow = 0;           // 직전 재생 위치(뒤로 시크 감지)
let _clRafId = null;               // onset 폴링 requestAnimationFrame id
let _clOnsetVmax = 1;              // 현재 곡 onset 최대 볼륨 — 볼륨 프리셋 경계를 곡별 상대화
let _clSensIdx = 0;                // 선택된 subdivision 레벨(0=박·1=8분·2=16분). 기본 박.
const CL_SHRINK = 0.5;             // 곡을 밴드 중심으로 뭉치는 정도(고정). 곡별 y 노이즈 완화.
// various_artists = 여러 아티스트 묶음 → '밴드 중심점'이 의미 없음(이질적 곡 평균, y 폭주).
// 센트로이드(중심 아이콘)만 숨기고 곡 점은 그대로 유지. score·신뢰도막대·최애 후보 제외와 일관(14-share.js).
const clHideCentroid = b => b === 'various_artists';
// [EMOI-MAP 전용] 딥스페이스 배경 가시성 보정 오버라이드(지도 한정). 전역 BAND_COLORS(공유)는 불변.
// ave_mujica 오버라이드(#e64c8c 로즈)는 제거 — 코어 명도를 energy로 올리는 _clEnergyColor(채도 하한·L 0.40~0.82)가
// 어두운 원색(#881144 와인)도 배경 위 가시 처리하므로 원 지정색을 그대로 사용(사용자 요청 2026-07-07).
const CL_COLOR_OVERRIDE = {};
function _clBandColor(band) { return CL_COLOR_OVERRIDE[band] || BAND_COLORS[band] || '#c084fc'; }
// 선택 밴드 배경: 퍼스널 컬러(BAND_COLORS)를 짙게 눌러(×CL_TINT_K) 은은한 틴트로 깐다.
// 곡 점은 밝은 밴드색이라 어두운 동색 배경 위에서도 대비 유지. 투톤 밴드(BAND_SUBCOLORS,
// 예: mugendai_mutype='유메미타')는 메인→보조 대각 그라데이션(워드클라우드 투톤과 일관).
// ALL/미정의 밴드는 CSS 기본 서피스로 복귀.
const CL_TINT_K = 0.16;   // 배경 어둡기(작을수록 어둡게)
function _clDark(hex, k = CL_TINT_K) {
    const h = (hex || '#c084fc').replace('#', '');
    const n = parseInt(h.length === 3 ? h.replace(/(.)/g, '$1$1') : h, 16);
    const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    return `rgb(${Math.round(r * k)},${Math.round(g * k)},${Math.round(b * k)})`;
}
function _clBandBg(band) {
    const main = _clDark(BAND_COLORS[band] || '#c084fc');
    const sub = BAND_SUBCOLORS[band] ? _clDark(BAND_SUBCOLORS[band]) : null;
    return sub ? `linear-gradient(135deg, ${main}, ${sub})` : main;
}

// [실험] 재생 곡 펄스 주기를 그 곡 BPM(60/bpm 초)에 맞춘다. bpm 없는 곡(캐시 미수집)은 기본 주기.
// 롤백: CL_PULSE_BPM=false 로 두면 기존 고정 펄스로 즉시 복귀(songs[].bpm 데이터는 남아도 무해).
const CL_PULSE_BPM = true;
const CL_PULSE_DEFAULT = 2.4;   // 기존 고정 펄스 주기(초, bpm 미상 곡)
const CL_PULSE_SCALE = 1;         // 펄스 발생 간격 배율(클수록 뜸하게). ※퍼지는 속도는 CL_PULSE_SPREAD_MS
const CL_PULSE_SPREAD_MS = 480;   // [실험] 한 펄스가 커지며 사라지는 시간(ms) — BPM 폴백 펄스용
const CL_PULSE_MAX_R = 46;        // [실험] 펄스 최대 반경(px)
const CL_PULSE_SPEED = 90;        // [실험] onset 펄스 전파속도 상한(px/s, v=1일 때). 낮출수록 느리게 퍼짐
const CL_PULSE_DUR_MAX = 1600;    // [실험] onset 펄스 지속 상한(ms) — 약한 히트가 너무 오래 안 남게
// [실험] beat 그리드 방식: 각 박의 볼륨(v)을 4단계로 나눠 크기·두께·속도 결정(강=크고 두껍게).
// build_beat_track.py 의 events{t,v} 와 짝. 볼륨 경계 [0.2, 0.6, 0.9] → 1·2·3·4단계.
//   1·2단계(v≤0.6): 펄스 없음 / 3단계(0.6~0.9): 24px·3px / 4단계(0.9~1.0): 48px·7px. (배열 idx=단계-1)
const CL_PULSE_R3 = [0, 0, 36, 48];            // 볼륨 4단계 크기(px). 1·2=0(발생 안 함)·3=24·4=48
const CL_PULSE_SPEED3 = [0, 0, 45, 63];        // 4단계 전파속도(px/s). 지속=크기/속도(3≈381ms·4≈762ms)
const CL_PULSE_LW3 = [3, 3, 3, 7];             // 볼륨 4단계 펄스 두께(px lineWidth). 3=3·4=7
const CL_VOL_ADAPTIVE = true;   // 볼륨 경계를 곡 최대볼륨(에너지)에 상대화(false=절대 v 사용)
function _clVolStep(v) {         // 경계[0.2/0.4/0.6]는 _clOnsetVmax 기준 비율 → 곡마다 프리셋 범위 일관
    const r = (CL_VOL_ADAPTIVE && _clOnsetVmax > 0) ? v / _clOnsetVmax : v;
    return r <= 0.2 ? 1 : (r <= 0.4 ? 2 : (r <= 0.6 ? 3 : 4));   // v 0~1 → 1~4
}
// subdivision 탭 — UI에서 제거(박 고정 확정). 로직·라벨은 보존하여 추후 '설정' 패널로 이관.
// 되살리려면 이 값만 true. 라벨은 build_beat_track SUBDIV 순서와 동기.
const CL_ONSET_TABS = false;
const CL_ONSET_SENS = ['박', '8분', '16분'];
// [실험] BPM 구간별 계단식으로 펄스를 묶는 박 수 — 빠를수록 더 성기게(부산스러움 완화).
// 경계 초과 시 해당 박 수 적용(내림차순 우선). 3/4박자 등 변박은 일단 무시(4/4 가정).
const CL_PULSE_STEPS = [
    { over: 150, beats: 1 },   // >150 → 4박(한 마디)
    { over: 130, beats: 1 },   // 131~150 → 3박
    { over: 110, beats: 1 },   // 111~130 → 2박
];                             //   ≤110 → 1박
function _clPulsePeriod(bpm) {
    if (!CL_PULSE_BPM || !bpm) return CL_PULSE_DEFAULT * CL_PULSE_SCALE;
    const step = CL_PULSE_STEPS.find(s => bpm > s.over);
    return Math.min(2.0, (60 / bpm) * (step ? step.beats : 1)) * CL_PULSE_SCALE;
}

// 펄스 색 가시성 보정: 배경 = 밴드색을 어둡게 깐 것(_clBandBg)이라, 원래 어두운 밴드색
// (ave_mujica '#881144' 등)은 펄스도 어두워 배경에 묻힌다. HSL 밝기(L)에 하한을 둬 밝게
// 끌어올리되 색상(H)·채도(S)는 보존 → 밴드 정체성 유지하며 어두운 배경 위 대비 확보.
const CL_PULSE_LMIN = 0.62;        // 펄스색 밝기 하한(0~1) — 높을수록 밝게(가시성↑)
function _clPulseColor(hex, lOverride) {
    const s = (hex || '#c084fc').replace('#', '');
    const h6 = s.length === 3 ? s.replace(/(.)/g, '$1$1') : s;
    let r = parseInt(h6.slice(0, 2), 16) / 255,
        g = parseInt(h6.slice(2, 4), 16) / 255,
        b = parseInt(h6.slice(4, 6), 16) / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    let H = 0, S = 0, L = (mx + mn) / 2;
    if (d) {
        S = L > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
        H = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
        H /= 6;
    }
    L = (lOverride != null) ? lOverride : Math.max(L, CL_PULSE_LMIN);   // 밝기 하한(또는 명시 L)
    S = Math.max(S, 0.5);                  // 채도 유지(밴드색 정체성)
    const hue = (p, q, t) => { t = (t + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
    const q = L < 0.5 ? L * (1 + S) : L + S - L * S, p = 2 * L - q;
    const to = x => Math.round(hue(p, q, x) * 255);
    return `rgb(${to(H + 1 / 3)},${to(H)},${to(H - 1 / 3)})`;
}
// 곡 energy(0~1) → 별 코어 색의 명도(L): 고에너지=밝게·저에너지=어둡게(딥스페이스 별의 광도감).
// hue·채도는 밴드 정체성 유지(_clPulseColor 내 S 하한). e=0.5(중앙값)≈현행 밝기, 양끝으로 벌어짐.
const CL_E_LMIN = 0.40, CL_E_LMAX = 0.82;
function _clEnergyColor(hex, e) {
    const t = Math.max(0, Math.min(1, typeof e === 'number' ? e : 0.5));
    return _clPulseColor(hex, CL_E_LMIN + (CL_E_LMAX - CL_E_LMIN) * t);
}

// [실험] 커스텀 펄스: 박 타이밍마다 원 하나가 짧게(CL_PULSE_SPREAD_MS) 커지며 사라진다.
// effectScatter의 연속 물결과 달리 '발생 간격(period)'과 '퍼지는 속도(spread)'를 분리 → 박자감.
function _clEmitPulse(r, ms, lw) {
    if (!_clusterChart || !_clPlay) return;
    const px = _clusterChart.convertToPixel({ seriesIndex: 0 }, _clPlay.val);   // songs 좌표계 → 픽셀
    if (!px) return;
    const maxR = r || CL_PULSE_MAX_R, dur = ms || CL_PULSE_SPREAD_MS, lineW = lw || 3;
    const circle = new echarts.graphic.Circle({
        shape: { cx: px[0], cy: px[1], r: 4 }, silent: true, z: 100,
        // stroke=밝기 보정 밴드색 · 두께(볼륨단계별) · 어두운 글로우로 밝은 배경(hello 노랑)에도 외곽 대비.
        style: { stroke: _clPulseColor(_clPlay.color), fill: 'none', lineWidth: lineW, opacity: 0.95,
                 shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.55)' },
    });
    _clusterChart.getZr().add(circle);
    circle.animateTo(
        { shape: { r: maxR }, style: { opacity: 0 } },
        { duration: dur, easing: 'cubicOut',
          done: () => { _clusterChart && _clusterChart.getZr().remove(circle); } });
}
function _clStopPulse() {
    if (_clPulseTimer) { clearInterval(_clPulseTimer); _clPulseTimer = null; }
    _clPulseKey = null;
}

// 선택(재생) 곡 상시 글로우: 데이터포인트 뒤(z:1)에서 느리게 점멸하는 밴드색 헤일로.
// 박 펄스(_clEmitPulse, stroke 파동)와 별개 — 이건 "지금 이 곡" 표식(fill glow). 재draw마다 재설정.
let _clPlayGlow = null;
function _clSetPlayGlow() {
    if (_clPlayGlow) { _clusterChart && _clusterChart.getZr().remove(_clPlayGlow); _clPlayGlow = null; }
    if (!_clusterChart || !_clPlay) return;
    const px = _clusterChart.convertToPixel({ seriesIndex: 0 }, _clPlay.val);
    if (!px) return;
    const col = _clPulseColor(_clPlay.color);
    const glow = new echarts.graphic.Circle({
        shape: { cx: px[0], cy: px[1], r: 17 }, silent: true, z: 1,
        style: { fill: col, opacity: 0.3, shadowBlur: 18, shadowColor: col },
    });
    _clusterChart.getZr().add(glow);
    const loop = to => glow.animateTo({ style: { opacity: to } },      // 느린 점멸(1.6s ease)
        { duration: 1600, easing: 'sinusoidalInOut', done: () => _clPlayGlow === glow && loop(to > 0.2 ? 0.1 : 0.34) });
    loop(0.1);
    _clPlayGlow = glow;
}

// ── onset 트랙 재생: 유튜브 타임스탬프(getCurrentTime)에 맞춰 사전분석 이벤트로 펄스 ──
// 이벤트 {t 시각, v 볼륨(→크기)}. build_beat_track.py 산출(onsets/<band>__<idx>.json).
// 곡 key→onset id 매핑: build.py 가 onsets/ 존재 곡 전체를 window.CLUSTER_ONSET_LIST 로 주입
// (하드코딩 파일럿 → 전곡 매니페스트). 데이터 자체는 런타임 lazy-fetch(_clFetchOnset).
const CL_ONSET_IDMAP = {};
(window.CLUSTER_ONSET_LIST || []).forEach(([b, s, id]) => { CL_ONSET_IDMAP[C.songKey(b, s)] = id; });
const CL_ONSET_BASE = './src/content/cluster/onsets/';   // index.html(루트) 기준 상대경로
const CL_ONSET_DUR_TOL = 5;   // 광고 판별: getDuration()이 onset 트랙 길이와 이 초 이상 다르면 본편 아님(펄스 억제)
const _clOnsetPending = {};   // 진행 중 fetch 중복 방지
// [에너지→subdivision] onset JSON 의 dyn(정규화 intensity 2Hz, build_dynamics.py)로 순간 subdivision
// 선택: 조용(intro/outro/브레이크다운)=박 · 고조=8분 · 피크=16분. 임계는 여기서 튜닝(재추출 불필요).
const CL_DYN_ON = true;      // false면 고정 subdivision(_clSensIdx 기본값 유지)
const CL_DYN_T1 = 0.37;      // 박↔8분 임계(글로벌 절대음량 정규화 intensity; ~-16.5dB)
const CL_DYN_T2 = 0.83;      // 8분↔16분 임계(~-9.5dB) — 계산엔 남기되 CL_DYN_MAX로 표시만 비활성
const CL_DYN_MAX = 1;        // 최대 레벨=1 → 박/8분만 표시(16분=레벨2는 clamp로 비활성). 2로 올리면 16분 부활.
const CL_DYN_HYST = 0.05;    // 경계 히스테리시스(잦은 토글 방지)
// 곡별 기본 subdivision(0=박·1=8분·2=16분). dyn 없을 때 폴백값(사용자 지정 기본 박).
// tempo/bpm 으로 자동판정 불가(같은 tempo·비율에 선호 상반 — report 참조)라,
// 박(0)이 나은 곡의 공통 패턴을 찾으면 그때 예외를 큐레이션한다.
const CL_ONSET_DEFDIV = {};   // 예외 지정: CL_ONSET_DEFDIV[C.songKey('roselia','FIRE BIRD')] = 0; (박)
function _clOnsetId(key) { return CL_ONSET_IDMAP[key] || null; }
function _clFetchOnset(id) {                 // 곡별 onset 런타임 로드(캐시=window.CLUSTER_ONSETS)
    const cache = (window.CLUSTER_ONSETS = window.CLUSTER_ONSETS || {});
    if (cache[id]) return Promise.resolve(cache[id]);
    if (_clOnsetPending[id]) return _clOnsetPending[id];
    const p = fetch(CL_ONSET_BASE + id + '.json')
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) cache[id] = d; delete _clOnsetPending[id]; return d; })
        .catch(() => { delete _clOnsetPending[id]; return null; });   // file:// / 404 → BPM 폴백
    _clOnsetPending[id] = p;
    return p;
}
function _clBisect(ev, t) {                 // 첫 t>=목표 인덱스(시크 시 포인터 재설정)
    let lo = 0, hi = ev.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (ev[m].t < t) lo = m + 1; else hi = m; }
    return lo;
}
function _clStartOnset(key, track) {
    if (_clOnsetKey === key && _clOnset) return;
    _clStopOnset();
    _clOnsetKey = key; _clOnset = track; _clOnsetIdx = 0; _clOnsetLastNow = 0;
    _clOnsetVmax = 0;              // 곡 최대 onset 볼륨 산출(볼륨 프리셋 경계 곡별 정규화)
    for (const lv of (track.levels || [])) for (const e of (lv.events || [])) if (e.v > _clOnsetVmax) _clOnsetVmax = e.v;
    if (!(_clOnsetVmax > 0)) _clOnsetVmax = 1;
    _clSensIdx = CL_ONSET_DEFDIV[key] ?? 0;    // 곡별 기본 subdivision(기본 박, 예외만 큐레이션)
    document.querySelectorAll('#cl-sens-tabs button').forEach(b =>   // 탭 하이라이트 동기
        b.style.background = (+b.dataset.i === _clSensIdx) ? '#c084fc' : 'rgba(30,30,42,0.85)');
    _clUpdateSensLabels();
    _clRafId = requestAnimationFrame(_clOnsetTick);
}
function _clStopOnset() {
    if (_clRafId) { cancelAnimationFrame(_clRafId); _clRafId = null; }
    _clOnset = null; _clOnsetIdx = 0; _clOnsetKey = null;
}

// [실험] 감도 탭 UI(메인 제외). 감도만 바꿔 비교, 프리셋/파이프라인은 그대로.
function _clBuildSensTabs() {
    if (!CL_ONSET_TABS) return;
    const wrap = document.getElementById('cluster-wrap');
    if (!wrap || document.getElementById('cl-sens-tabs')) return;
    const bar = document.createElement('div');
    bar.id = 'cl-sens-tabs';
    bar.style.cssText = 'position:absolute;top:4px;left:4px;z-index:20;display:flex;gap:3px;';
    CL_ONSET_SENS.forEach((label, i) => {
        const b = document.createElement('button');
        b.textContent = label; b.dataset.i = i;
        b.style.cssText = 'font-size:10px;padding:2px 6px;border-radius:5px;border:1px solid #444;cursor:pointer;color:#fff;background:'
            + (i === _clSensIdx ? '#c084fc' : 'rgba(30,30,42,0.85)');
        b.onclick = () => _clSetSens(i);
        bar.appendChild(b);
    });
    wrap.appendChild(bar);
}
function _clSetSens(i) {
    _clSensIdx = i;
    document.querySelectorAll('#cl-sens-tabs button').forEach(b =>
        b.style.background = (+b.dataset.i === i) ? '#c084fc' : 'rgba(30,30,42,0.85)');
    if (_clOnset && player && typeof player.getCurrentTime === 'function') {   // 재생 중이면 현재 위치로 포인터 재설정
        const ev = (_clOnset.levels[i] || {}).events || [];
        _clOnsetIdx = _clBisect(ev, player.getCurrentTime() || 0);
    }
}
function _clUpdateSensLabels() {   // 탭 버튼 title(hover)에 곡별 onset 개수 표시
    if (!_clOnset) return;
    document.querySelectorAll('#cl-sens-tabs button').forEach(b => {
        const lv = _clOnset.levels[+b.dataset.i];
        if (lv) b.title = `${lv.n}개 · 초당 ${(lv.n / _clOnset.dur).toFixed(1)} (kick ${lv.kick}/snare ${lv.snare})`;
    });
}
function _clDynLevel(now) {              // 현재 시각 intensity → subdivision 레벨(0박·1·2 계산 후 CL_DYN_MAX로 clamp)
    const dyn = _clOnset && _clOnset.dyn;
    if (!CL_DYN_ON || !dyn || !dyn.v || !dyn.v.length)
        return Math.min(CL_DYN_MAX, (CL_ONSET_DEFDIV[_clOnsetKey] ?? 0));   // dyn 없으면 고정 폴백
    const v = dyn.v;
    let i = Math.floor(now * dyn.hz);
    i = i < 0 ? 0 : (i >= v.length ? v.length - 1 : i);
    const e = v[i];
    let lvl = e < CL_DYN_T1 ? 0 : (e < CL_DYN_T2 ? 1 : 2);
    if (Math.abs(lvl - _clSensIdx) === 1) {          // 히스테리시스: 경계 ±HYST 안이면 현재 유지
        const thr = Math.max(lvl, _clSensIdx) === 2 ? CL_DYN_T2 : CL_DYN_T1;
        if (Math.abs(e - thr) < CL_DYN_HYST) lvl = _clSensIdx;
    }
    return Math.min(CL_DYN_MAX, lvl);                 // CL_DYN_MAX=1 → 16분(레벨2)은 clamp로 비활성, 박/8분만 표시
}
function _clOnsetTick() {
    _clRafId = requestAnimationFrame(_clOnsetTick);
    if (!_clOnset || !player || typeof player.getCurrentTime !== 'function') return;
    // 광고 중 펄스 억제: 유튜브 재생길이(getDuration)가 onset 트랙 길이와 맞을 때만 발화.
    // 프리롤 광고 중엔 getDuration 이 광고 길이(또는 0)라 트랙 길이와 어긋남 → 펄스 정지.
    const vdur = (typeof player.getDuration === 'function' && player.getDuration()) || 0;
    if (Math.abs(vdur - _clOnset.dur) > CL_ONSET_DUR_TOL) { _clOnsetIdx = 0; _clOnsetLastNow = 0; return; }
    const now = player.getCurrentTime() || 0;
    const dlvl = _clDynLevel(now);                   // 에너지 기반 순간 subdivision(박/8분/16분)
    const lv = _clOnset.levels[dlvl];
    if (!lv) return;
    const ev = lv.events;
    if (dlvl !== _clSensIdx || now < _clOnsetLastNow - 0.3) {   // 레벨 변화/뒤로 시크 → 포인터 재설정
        _clSensIdx = dlvl;
        _clOnsetIdx = _clBisect(ev, now);
    }
    _clOnsetLastNow = now;
    while (_clOnsetIdx < ev.length && ev[_clOnsetIdx].t <= now) {
        const e = ev[_clOnsetIdx++];
        if (now - e.t <= 0.25) {            // 밀린 과거 이벤트(랙/앞 시크)는 스킵해 폭발 방지
            const step = _clVolStep(e.v);                          // 볼륨 → 3단계
            const maxR = CL_PULSE_R3[step - 1];
            if (maxR > 0) {                                        // 1단계(0px) = 펄스 발생 안 함
                const speed = CL_PULSE_SPEED3[step - 1];           // 구 3·5단계 속도 승계
                _clEmitPulse(maxR, Math.min(CL_PULSE_DUR_MAX, maxR / speed * 1000), CL_PULSE_LW3[step - 1]);
            }
        }
    }
}

// 재생 곡/주기가 바뀔 때만 타이머 재설정(같으면 유지 → 재draw로 리듬 안 끊김).
// onset 트랙이 있는 곡이면 BPM 대신 타임스탬프 동기 재생(_clStartOnset).
function _clSyncPulse(period) {
    if (!CL_PULSE_BPM || !_clPlay) { _clStopPulse(); _clStopOnset(); return; }
    const id = _clOnsetId(nowPlaying);
    if (id) {                                         // onset 트랙 보유 곡 → 타임스탬프 동기 재생
        const key = nowPlaying, cache = window.CLUSTER_ONSETS || {};
        if (cache[id]) { _clStopPulse(); _clStartOnset(key, cache[id]); return; }
        _clStopPulse();                               // 로딩 동안엔 펄스 없음(잠깐)
        _clFetchOnset(id).then(track => {             // 도착 시 아직 같은 곡이면 시작(아니면 폐기)
            if (track && nowPlaying === key && _clPlay) _clStartOnset(key, track);
        });
        return;
    }
    _clStopOnset();
    if (!period) { _clStopPulse(); return; }
    const pkey = nowPlaying + '@' + period;
    if (pkey === _clPulseKey) return;
    _clStopPulse();
    _clPulseKey = pkey;
    _clEmitPulse();                                   // 박 시작 즉시 1발
    _clPulseTimer = setInterval(_clEmitPulse, period * 1000);
}

// ───────────────────────────
// [별밭] 딥스페이스 장식 레이어 — 데이터(#cluster-chart, 투명) 뒤 canvas(z-index:0)에서
// 반짝이는 별 + 밴드 성운을 그린다. 곡 점(별)과 별개의 순수 장식이라 인터랙션·데이터 무관.
// rAF 루프는 탭 숨김 시 정지(CPU 절약). 곡 점은 트윈클 안 함(가독성·성능).
// ───────────────────────────
const _clSky = { canvas: null, ctx: null, stars: [], neb: [], focus: null, raf: null,
                 w: 0, h: 0, dpr: 1, t0: 0, _lt: 0 };
function _clSkyRand(a, b) { return a + Math.random() * (b - a); }
function _hex2rgb(hex) {
    const s = (hex || '#c084fc').replace('#', '');
    const h6 = s.length === 3 ? s.replace(/(.)/g, '$1$1') : s;
    return [parseInt(h6.slice(0, 2), 16), parseInt(h6.slice(2, 4), 16), parseInt(h6.slice(4, 6), 16)];
}
function _clSkyInitObjects() {
    const area = _clSky.w * _clSky.h;
    const n = Math.max(60, Math.min(240, Math.round(area / 1600)));   // 면적 비례(모바일=자동 감소)
    _clSky.stars = Array.from({ length: n }, () => ({
        x: Math.random() * _clSky.w, y: Math.random() * _clSky.h,
        r: _clSkyRand(0.4, 1.5), base: _clSkyRand(0.15, 0.7), amp: _clSkyRand(0.1, 0.5),
        w: _clSkyRand(0.4, 1.8), ph: Math.random() * Math.PI * 2,   // 트윈클 위상·속도(별마다 다름)
        vx: _clSkyRand(-3, 3), vy: _clSkyRand(-3, 3),               // 아주 느린 드리프트(px/s) = "떠 있음"
        c: Math.random() < 0.75 ? [220, 235, 255] : [255, 240, 225],
    }));
    const m = Math.min(_clSky.w, _clSky.h);
    _clSky.neb = [                                                  // 앰비언트 성운(딥스페이스 깊이감)
        { x: _clSky.w * 0.28, y: _clSky.h * 0.32, r: m * 0.6, c: [80, 120, 200], a: 0.05, vx: 1.2, vy: 0.6 },
        { x: _clSky.w * 0.72, y: _clSky.h * 0.70, r: m * 0.55, c: [130, 70, 180], a: 0.045, vx: -1.0, vy: -0.8 },
    ];
    _clSky.focus = { x: _clSky.w * 0.5, y: _clSky.h * 0.5, r: m * 0.7,   // 밴드 포커스 성운(_clSetNebula 구동)
                     c: [192, 132, 252], a: 0, target: 0, vx: 0.8, vy: -0.5 };
}
function _clSkyResize() {
    const wrap = document.getElementById('cluster-wrap');
    if (!wrap || !_clSky.canvas) return;
    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (!w || !h) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const reinit = !_clSky.stars.length || Math.abs(w - _clSky.w) > 1 || Math.abs(h - _clSky.h) > 1;
    _clSky.w = w; _clSky.h = h; _clSky.dpr = dpr;
    _clSky.canvas.width = Math.round(w * dpr); _clSky.canvas.height = Math.round(h * dpr);
    _clSky.canvas.style.width = w + 'px'; _clSky.canvas.style.height = h + 'px';
    _clSky.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (reinit) _clSkyInitObjects();
}
function _clSetNebula(hex) {              // 밴드 포커스=밴드색 성운 부각 / ALL=off (루프가 부드럽게 lerp)
    if (!_clSky.focus) return;
    if (hex) { _clSky.focus.c = _hex2rgb(hex); _clSky.focus.target = 0.16; }
    else { _clSky.focus.target = 0; }
}
function _clSkyDrawNeb(nb, dt) {
    nb.x += nb.vx * dt; nb.y += nb.vy * dt;
    if (nb.x < -nb.r) nb.x = _clSky.w + nb.r; else if (nb.x > _clSky.w + nb.r) nb.x = -nb.r;
    if (nb.y < -nb.r) nb.y = _clSky.h + nb.r; else if (nb.y > _clSky.h + nb.r) nb.y = -nb.r;
    if (nb.a <= 0.002) return;
    const g = _clSky.ctx.createRadialGradient(nb.x, nb.y, 0, nb.x, nb.y, nb.r);
    g.addColorStop(0, `rgba(${nb.c[0]},${nb.c[1]},${nb.c[2]},${nb.a})`);
    g.addColorStop(1, `rgba(${nb.c[0]},${nb.c[1]},${nb.c[2]},0)`);
    _clSky.ctx.fillStyle = g;
    _clSky.ctx.fillRect(0, 0, _clSky.w, _clSky.h);
}
function _clSkyTick(ts) {
    _clSky.raf = requestAnimationFrame(_clSkyTick);
    const ctx = _clSky.ctx; if (!ctx) return;
    if (!_clSky.focus || _clSky.w <= 0 || _clSky.h <= 0) return;   // 아직 초기화 전(패널 0 크기) = 스킵
    if (!_clSky.t0) { _clSky.t0 = ts; _clSky._lt = 0; }
    const t = (ts - _clSky.t0) / 1000;
    const dt = Math.min(0.05, t - _clSky._lt); _clSky._lt = t;
    ctx.clearRect(0, 0, _clSky.w, _clSky.h);
    ctx.globalCompositeOperation = 'lighter';        // 별·성운 가산합성(빛)
    for (const nb of _clSky.neb) _clSkyDrawNeb(nb, dt);
    _clSky.focus.a += (_clSky.focus.target - _clSky.focus.a) * Math.min(1, dt * 2.5);   // 포커스 전환 lerp
    _clSkyDrawNeb(_clSky.focus, dt);
    for (const s of _clSky.stars) {
        s.x += s.vx * dt; s.y += s.vy * dt;
        if (s.x < 0) s.x += _clSky.w; else if (s.x > _clSky.w) s.x -= _clSky.w;
        if (s.y < 0) s.y += _clSky.h; else if (s.y > _clSky.h) s.y -= _clSky.h;
        let a = s.base + s.amp * Math.sin(t * s.w + s.ph);   // 트윈클
        if (a <= 0.02) continue; if (a > 1) a = 1;
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${s.c[0]},${s.c[1]},${s.c[2]},${a})`;
        ctx.fill();
    }
    ctx.globalCompositeOperation = 'source-over';
}
function _clSkyStart() { if (!_clSky.raf && _clSky.canvas) { _clSky.t0 = 0; _clSky.raf = requestAnimationFrame(_clSkyTick); } }
function _clSkyStop() { if (_clSky.raf) { cancelAnimationFrame(_clSky.raf); _clSky.raf = null; } }
function _clBuildStarfield() {            // renderCluster 에서 1회 idempotent 생성(_clBuildSensTabs 패턴)
    const wrap = document.getElementById('cluster-wrap');
    if (!wrap) return;
    if (_clSky.canvas) { _clSkyResize(); _clSkyStart(); return; }
    const cv = document.createElement('canvas');
    cv.id = 'cl-starfield';
    wrap.insertBefore(cv, wrap.firstChild);          // #cluster-chart 뒤(z-index:0)
    _clSky.canvas = cv; _clSky.ctx = cv.getContext('2d');
    _clSkyResize();
    document.addEventListener('visibilitychange', () => { if (document.hidden) _clSkyStop(); else _clSkyStart(); });
    _clSkyStart();
}

// 헤더(am-head)에 범례 칩 1회 생성(idempotent, _clBuildStarfield 패턴).
// 곡 점(별)의 크기·글로우가 곡 energy(add_energy.py, 0~1)에 비례함을 안내.
function _clBuildEnergyLegend() {
    const head = document.querySelector('#audiomap .am-head');
    if (!head || document.getElementById('cl-legend')) return;
    const chip = document.createElement('span');
    chip.id = 'cl-legend'; chip.className = 'am-legend';
    chip.innerHTML = '<span class="am-legend-star">★</span> 밝기·크기 = 곡 에너지';
    head.appendChild(chip);
}

/** 밴드 음원 지도 진입점. 정적 베이스는 1회만 설정(줌/팬 보존), 그리기는 _clDraw 가 담당. */
function renderCluster() {
    const el = document.getElementById('cluster-chart');
    const empty = document.getElementById('cl-empty');
    const subEl = document.getElementById('cl-sub');
    if (!el) return;

    const data = window.CLUSTER_DATA || {};
    const songs = data.songs || [];
    if (!window.echarts || songs.length === 0) {
        if (empty) empty.hidden = false;
        if (subEl) subEl.textContent = '';
        return;
    }
    if (empty) empty.hidden = true;
    if (subEl) subEl.textContent =
        `${(data.bands || []).length}밴드 · 곡 ${songs.length} · 거칢×정서 지각 2D`;
    _clAxisLabels(data.axes);      // 축 +/− 방향 의미 라벨

    if (!_clusterChart) {
        _clusterChart = echarts.init(el);
        window.addEventListener('resize', () => { if (_clusterChart) { _clusterChart.resize(); _clPositionAxisLabels(); } _clSkyResize(); });
        _clusterChart.setOption({                 // 정적 베이스(1회)
            backgroundColor: 'transparent',
            animation: true, animationDuration: 0,        // 초기=즉시 / 클릭 이동=애니메이션
            animationDurationUpdate: 350, animationEasingUpdate: 'cubicOut',
            tooltip: {
                trigger: 'item', confine: true,
                backgroundColor: 'rgba(20,20,30,0.95)', borderColor: '#2a2a3a',
                textStyle: { color: '#e8e8f0', fontSize: 11 },
                formatter: p => p.data && p.data._song
                    ? `<b>${p.data._song}</b><br>${bandDisplay(p.data._band)}`
                      + (typeof p.data._e === 'number' ? ` · 에너지 ${Math.round(p.data._e * 100)}%` : '')
                      + ` · 클릭=재생`
                    : (p.data && p.data._n != null
                        ? `<b>${bandDisplay(p.data._band)}</b> · ${p.data._n}곡`
                          + (p.data._n < 3 ? ` · <span style="color:#ffe14d">n=${p.data._n} · 잠정</span>` : '')
                          + ` (클릭=이 밴드 보기)`
                        : ''),
            },
            grid: { left: 6, right: 6, top: 6, bottom: 6 },
            xAxis: { type: 'value', show: false, scale: true,
                     splitLine: { show: true, lineStyle: { color: 'rgba(102,224,230,0.07)' } } },   // 희미한 HUD 격자
            yAxis: { type: 'value', show: false, scale: true,
                     splitLine: { show: true, lineStyle: { color: 'rgba(102,224,230,0.07)' } } },
            dataZoom: [                        // 휠/핀치 줌·드래그 팬(점 유지)
                { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
                { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
            ],
        });
        _clusterChart.on('click', p => {           // seriesIndex 대신 seriesId(series 순서 변경에 안전)
            if (p.seriesId === 'songs') {          // 곡 클릭 = 재생(이미 재생 중이면 무시)
                const s = p.data;
                if (s && s._url && C.songKey(s._band, s._song) !== nowPlaying)
                    playSong({ band: s._band, title: s._song, url: s._url });
            } else if (p.seriesId === 'cents') {   // 센트로이드 클릭 = 그 밴드를 셀렉터에서 고른 것과 동일
                if (currentBand === 'ALL') selectBand(p.data._band);
            }
        });
        _clusterChart.on('mouseover', p => {       // ALL 모드: 센트로이드 호버 = 그 밴드 확장 미리보기
            if (currentBand === 'ALL' && p.seriesId === 'cents') { _clHover = p.data._band; _clDraw(); }
        });
        _clusterChart.on('mouseout', p => {
            if (currentBand === 'ALL' && p.seriesId === 'cents' && _clHover) { _clHover = null; _clDraw(); }
        });
        _clusterChart.on('dataZoom', () => {       // 줌/팬: 글로우(zrender 절대픽셀)·화살표를 새 좌표로 갱신(분리 방지)
            if (_clPlayGlow && _clPlay) {
                const px = _clusterChart.convertToPixel({ seriesIndex: 0 }, _clPlay.val);
                if (px) _clPlayGlow.attr({ shape: { cx: px[0], cy: px[1], r: 17 } });
            }
            _clUpdateHud(_clFocus());
            _clPositionAxisLabels();               // 줌/팬: 축선 이동 → 라벨 재정렬
        });
        _clusterChart.getZr().on('click', e => {   // 포커스 모드에서 빈 영역 클릭 = ALL(개요)로 복귀
            if (!e.target && currentBand !== 'ALL') selectBand('ALL');
        });
    }
    _clBuildSensTabs();            // [실험] 감도 탭(1회 생성, idempotent)
    _clBuildStarfield();           // 딥스페이스 별밭 canvas(1회 생성, idempotent)
    _clBuildEnergyLegend();        // ★ 밝기·크기 = 곡 에너지 범례 칩(1회 생성, idempotent)
    _clHover = null;                // 재진입 시 호버 초기화(포커스는 currentBand 따라감)
    _clDraw();
    _clusterChart.resize();
    _clPositionAxisLabels();                // 초기 크기 확정 후 축 라벨 정렬
}

/** 센트로이드(0,0) 기준 x·y 축선 점선 — 밴드 포커스 모드에서만 표시. */
function _clOriginCross() {
    return {
        symbol: 'none', silent: true, animation: false,
        lineStyle: { color: 'rgba(255,255,255,0.16)', type: 'dashed', width: 1 },
        label: { show: false },
        data: [{ xAxis: 0 }, { yAxis: 0 }],
    };
}

/** 두 모드: ALL 개요(정적, 호버=타밴드 흐림) / 특정 밴드 포커스(센트로이드=정중앙). */
function _clDraw() {
    const data = window.CLUSTER_DATA || {};
    const songs = data.songs || [];
    const cents = data.centroids || [];
    const playKey = nowPlaying;            // 재생 중 곡 = 지도에서도 강조(리스트와 동기)
    const subEl = document.getElementById('cl-sub');
    const cById = {};
    cents.forEach(c => { cById[c.band] = c; });
    const focus = (currentBand !== 'ALL' && cById[currentBand]) ? currentBand : null;
    // 밴드 포커스: 딥스페이스(CSS)는 유지하고 그 밴드 퍼스널 컬러를 '성운'으로 부각(구 _clBandBg 배경 교체 대체).
    // various_artists는 밴드가 아니므로(센트로이드 숨김) 성운도 off — ALL과 동일한 딥스페이스.
    _clSetNebula((focus && !clHideCentroid(focus)) ? _clBandColor(focus) : null);

    let playingPt = null;                  // 재생 곡의 화면 좌표(글로우/펄스용)
    // 곡 점 = 딥스페이스의 별: 밝힌 밴드색 코어 + 흰 림 + 에너지 비례 글로우(shadowBlur).
    // energy(0~1, add_energy.py)로 크기·글로우 변조 → 에너지 큰 곡 = 밝은 별. 없으면 0.5 폴백.
    const songMark = (s, val, base) => {   // 재생 곡=가장 밝게 / 재생 중이면 나머지=약간 어둡게 / 호버 흐림=글로우 억제
        const col = _clBandColor(s.band);
        const e = typeof s.energy === 'number' ? s.energy : 0.5;
        if (playKey && C.songKey(s.band, s.song) === playKey) {
            const bright = _clPulseColor(col);                     // 밝기 보정색
            playingPt = { value: val, itemStyle: { color: col }, _bpm: s.bpm };
            return {
                value: val, name: s.song, symbolSize: Math.max(base.size, 14) + 2,
                itemStyle: { color: bright, opacity: 1, borderColor: '#fff', borderWidth: 2,
                             shadowBlur: 16 + e * 10, shadowColor: bright },   // 가장 밝은 별
                _band: s.band, _song: s.song, _url: s.url, _e: e,
            };
        }
        const dim = playKey ? 0.62 : 1;                            // 재생 곡 있으면 나머지 어둡게
        const faint = base.op < 0.3;                               // ALL 호버 시 흐려진 타밴드 = 글로우 억제
        const star = faint ? col : _clEnergyColor(col, e);         // 코어 명도 = 곡 에너지(고=밝게·저=어둡게)
        return {
            value: val, name: s.song, symbolSize: base.size * (0.7 + 0.6 * e),
            itemStyle: {
                color: star, opacity: base.op * dim,
                borderColor: faint ? base.bc : 'rgba(255,255,255,0.72)',   // 밝은 코어 림
                borderWidth: faint ? base.bw : 0.6,
                shadowBlur: faint ? 0 : (2 + e * 8) * (base.gk ?? 1), shadowColor: star,   // 색 있는 헤일로(gk=모드별 글로우 배율)
            },
            _band: s.band, _song: s.song, _url: s.url, _e: e,
        };
    };
    const centMark = (band, val, size, opacity) => {   // 센트로이드 = 밴드 아이콘 PNG
        const n = (cById[band] || {}).n;
        const prov = n != null && n < 3;               // n=1~2 = 관측 부족 → '잠정 별'(반투명, 별밭 컨셉: 흐릿)
        return {
            value: val, symbol: 'image://' + bandIcon(band), symbolSize: size,
            name: bandDisplay(band), itemStyle: { opacity: prov ? opacity * 0.5 : opacity },
            _band: band, _n: n,
        };
    };

    let songPts, centPts, xAxis, yAxis;
    if (focus) {
        // 포커스: 그 밴드만 · 센트로이드=원점 · 곡=센트로이드 기준 offset · 대칭범위로 정중앙
        const c = cById[focus];
        const list = songs.filter(s => s.band === focus);
        songPts = list.map(s => songMark(s, [s.x - c.x, s.y - c.y], { op: 0.9, size: 12, bc: 'rgba(255,255,255,0.85)', bw: 1 }));
        let Mx = 1, My = 1;
        list.forEach(s => { Mx = Math.max(Mx, Math.abs(s.x - c.x)); My = Math.max(My, Math.abs(s.y - c.y)); });
        xAxis = { min: -Mx * 1.3, max: Mx * 1.3 }; yAxis = { min: -My * 1.3, max: My * 1.3 };
        centPts = clHideCentroid(focus) ? [] : [centMark(focus, [0, 0], 46, 0.3)];   // 포커스: 반투명(데이터 안 가리게)
        if (subEl) subEl.textContent = `${bandDisplay(focus)} · 곡 ${list.length} · 곡 클릭=재생 · 빈 곳=개요로`;
    } else {
        // ALL 개요: 전 밴드 항상 뭉침(이동 없음). 호버 밴드만 부각, 나머지는 투명도만 낮춤.
        const expB = _clHover;
        songPts = songs.map(s => {
            const c = cById[s.band] || { x: 0, y: 0 };
            const val = [c.x + CL_SHRINK * (s.x - c.x), c.y + CL_SHRINK * (s.y - c.y)];
            const faded = expB && s.band !== expB;
            // ALL 개요는 곡이 밴드 중심으로 뭉쳐(CL_SHRINK) 밀집 → 별을 작게 + 글로우 약하게(gk)로
            // 엉겨붙음 완화(색은 유지). 포커스 모드는 여유 있어 기존 크기/글로우 유지.
            return songMark(s, val, faded ? { op: 0.12, size: 4, bc: 'rgba(0,0,0,0.3)', bw: 0.5, gk: 0.5 }
                                          : { op: 0.6, size: 5, bc: 'rgba(0,0,0,0.3)', bw: 0.5, gk: 0.5 });
        });
        centPts = cents.filter(c => !clHideCentroid(c.band)).map(c => centMark(c.band, [c.x, c.y],
            expB === c.band ? 40 : 34, (expB && expB !== c.band) ? 0.35 : 1));
        xAxis = { min: null, max: null }; yAxis = { min: null, max: null };
        if (subEl) subEl.textContent = `${(data.bands || []).length}밴드 · 곡 ${songs.length} · 거칢×정서 지각 2D`;
    }

    const rangeKey = focus || 'ALL';        // 모드/밴드 바뀔 때만 축범위 갱신(줌/팬 보존)
    const axisOpt = {};
    if (rangeKey !== _clRangeKey) { axisOpt.xAxis = xAxis; axisOpt.yAxis = yAxis; _clRangeKey = rangeKey; }
    // 센트로이드 절대원점 방향지시기(밴드색·센트로이드 투명도 승계) — 원점(0,0)을 가리키는 쐐기
    const centArrowData = focus
        ? (clHideCentroid(focus) ? [] : [{ coord: [0, 0], origin: [-cById[focus].x, -cById[focus].y],
                                           color: _clBandColor(focus), op: 0.3, gap: 30 }])
        : cents.filter(c => !clHideCentroid(c.band)).map(c => ({
              coord: [c.x, c.y], origin: [0, 0], color: _clBandColor(c.band),
              op: (_clHover && _clHover !== c.band) ? 0.35 : 1, gap: 24 }));
    _clusterChart.setOption({
        ...axisOpt,
        series: [
            { id: 'songs', type: 'scatter', data: songPts, z: 2, emphasis: { scale: 1.3 },
              markLine: _clOriginCross() },                                        // 원점 십자선(항상)
            {
                id: 'cent-arrows', type: 'custom', z: focus ? 0 : 4, silent: true,   // 센트로이드→원점 방향지시기
                data: centArrowData.map(it => it.coord),
                renderItem: (params, api) => {
                    const it = centArrowData[params.dataIndex];
                    if (!it) return;
                    const p = api.coord(it.coord), o = api.coord(it.origin);       // 픽셀 기준(aspect 정확)
                    const ang = Math.atan2(o[1] - p[1], o[0] - p[0]);
                    return {
                        type: 'path', silent: true,
                        shape: { pathData: 'M9,0 L-5,-5 L-1,0 L-5,5 Z' },
                        x: p[0] + Math.cos(ang) * it.gap, y: p[1] + Math.sin(ang) * it.gap,
                        rotation: -ang,                                            // echarts custom=반시계 → -ang
                        style: { fill: it.color, opacity: it.op * 0.85 },
                    };
                },
            },
            {
                id: 'cents', type: 'scatter', data: centPts, z: focus ? 1 : 5,   // 포커스: 데이터 뒤로
                silent: !!focus,                                                  // 포커스: 클릭·호버 비활성(ALL 복귀 시 재활성)
                label: {
                    show: true, formatter: p => p.data.name, position: 'bottom',
                    color: '#fff', fontSize: 12, fontWeight: 700,
                    textBorderColor: 'rgba(0,0,0,0.7)', textBorderWidth: 3,
                },
                labelLayout: { hideOverlap: false },
            },
            {
                id: 'playing', type: 'effectScatter', coordinateSystem: 'cartesian2d', z: 3,
                data: (playingPt && !CL_PULSE_BPM) ? [playingPt] : [], symbolSize: 14, showEffectOn: 'render',
                rippleEffect: { period: _clPulsePeriod(playingPt && playingPt._bpm), scale: 4.5, brushType: 'stroke' }, itemStyle: { opacity: 0.9 },
            },
        ],
    });
    _clPlay = playingPt ? { val: playingPt.value, color: playingPt.itemStyle.color } : null;
    _clSyncPulse(playingPt ? _clPulsePeriod(playingPt._bpm) : null);
    _clSetPlayGlow();                       // 선택 곡 상시 글로우(느린 점멸)
    _clSimList(focus);
    _clUpdateHud(focus);                    // HUD readout(밴드·센트로이드·재생곡·메타) 갱신
    _clPositionAxisLabels();                // 축 라벨을 x=0·y=0 축선에 정렬(ALL 개요 원점 오프셋 대응)
}

/** HUD readout: 밴드명·센트로이드 좌표(포커스), 재생곡 거리·좌표·원점 방향 화살표·곡 메타. */
function _clFocus() {   // 현재 포커스 밴드(줌/재draw 밖에서 _clUpdateHud 호출 시 focus 재계산용)
    const cById = {};
    ((window.CLUSTER_DATA || {}).centroids || []).forEach(c => { cById[c.band] = c; });
    return (currentBand !== 'ALL' && cById[currentBand]) ? currentBand : null;
}
function _clFmt(n) { return (n >= 0 ? '+' : '') + n.toFixed(2); }
function _clUpdateHud(focus) {
    const $ = id => document.getElementById(id);
    const data = window.CLUSTER_DATA || {};
    const cById = {};
    (data.centroids || []).forEach(c => { cById[c.band] = c; });
    const band = $('hud-band'), ro = $('hud-centroid');
    if (focus && cById[focus] && !clHideCentroid(focus)) {          // 포커스: 밴드명 + 센트로이드 좌표
        const c = cById[focus];
        band.innerHTML = `<span class="hud-name">${bandDisplay(focus)}</span>`;
        ro.innerHTML = `밴드 거침 <span class="hud-val">x ${_clFmt(c.x)}</span><br>`
                     + `밴드 밝음 <span class="hud-val">y ${_clFmt(c.y)}</span>`;
    } else {                                                        // ALL: 'BanG Dream' + 밴드별 곡수
        band.innerHTML = '<span class="hud-name">BanG Dream</span>';
        const cs = (data.centroids || []).slice().sort((a, b) => b.n - a.n);
        ro.innerHTML = cs.map(c => `${bandDisplay(c.band)} <span class="hud-val">${c.n}</span>`).join('<br>');
    }
    band.hidden = false; ro.hidden = false;                        // ALL 포함 항상 표시
    const trk = $('hud-track'), meta = $('hud-meta'), arrow = $('hud-arrow'), txt = $('hud-track-txt');
    const song = (data.songs || []).find(s => C.songKey(s.band, s.song) === nowPlaying);
    if (song) {                                                     // 재생곡: 밴드중심 거리·좌표·방향·메타
        const c = cById[song.band] || { x: 0, y: 0 };
        const dx = song.x - c.x, dy = song.y - c.y;
        const dist = Math.hypot(dx, dy);
        const xWord = dx >= 0 ? '거침' : '부드러움';                 // x 편차 부호 → 음색 방향
        const yWord = dy >= 0 ? '발랄함' : '진지함';                // y 편차 부호 → 정서 방향
        if (txt) txt.innerHTML = '<div class="hud-hd">▶ 재생 중</div>'
            + `밴드 평균점으로부터 거리 <span class="hud-val">${dist.toFixed(2)}</span><br>`
            + `밴드 평균보다 <span class="hud-val">${Math.abs(dx).toFixed(2)}</span>만큼 ${xWord}<br>`
            + `밴드 평균보다 <span class="hud-val">${Math.abs(dy).toFixed(2)}</span>만큼 ${yWord}`;
        if (arrow && _clPlay && _clusterChart) {                    // 화살표: 화면 픽셀 기준 밴드 중심(센트로이드) 방향
            const pS = _clusterChart.convertToPixel({ seriesIndex: 0 }, _clPlay.val);
            const cs = cById[song.band] || { x: 0, y: 0 };
            const centVal = focus ? [0, 0] : [cs.x, cs.y];          // 재생곡 밴드 중심의 현 좌표계 값(포커스=원점 offset)
            const pC = _clusterChart.convertToPixel({ seriesIndex: 0 }, centVal);
            if (pS && pC) arrow.style.transform =
                `rotate(${(Math.atan2(pC[1] - pS[1], pC[0] - pS[0]) * 180 / Math.PI).toFixed(1)}deg)`;
        }
        const list = ((window.SONG_DATA || {}).songsByBand || {})[song.band] || [];
        const rec = list.find(t => C.songKey(song.band, t.title) === nowPlaying) || {};
        meta.innerHTML = `<div class="hud-song">${song.song}</div>` + (rec.album ? `<div>${rec.album}</div>` : '');
        trk.hidden = false; meta.hidden = false;
    } else { trk.hidden = true; meta.hidden = true; }
}

/** 축 +/− 방향 의미 라벨(data.axes: x/y 각 {pos,neg,feature})을 4모서리에 표시. */
function _clAxisLabels(axes) {
    const set = (id, txt) => { const e = document.getElementById(id); if (e) e.textContent = txt; };
    const x = axes && axes.x, y = axes && axes.y;
    set('cl-ax-top', y ? `↑ ${y.pos}` : '');
    set('cl-ax-bottom', y ? `↓ ${y.neg}` : '');
    set('cl-ax-left', x ? `← ${x.neg}` : '');
    set('cl-ax-right', x ? `${x.pos} →` : '');
}

/** 축 방향 라벨(cl-ax-*)을 x=0·y=0 축선의 현재 픽셀 위치에 붙인다.
 *  ALL 개요는 auto scale이라 원점이 화면 중앙이 아님 → CSS 50% 고정으로는 축선과 어긋난다. */
function _clPositionAxisLabels() {
    if (!_clusterChart) return;
    const px0 = _clusterChart.convertToPixel({ xAxisIndex: 0 }, 0);   // x=0 세로선의 화면 x
    const py0 = _clusterChart.convertToPixel({ yAxisIndex: 0 }, 0);   // y=0 가로선의 화면 y
    if (px0 == null || py0 == null) return;
    const set = (id, prop, val) => { const e = document.getElementById(id); if (e) e.style[prop] = val + 'px'; };
    set('cl-ax-top', 'left', px0);       // 세로축(y) 라벨 = x=0 세로선 위/아래에 정렬
    set('cl-ax-bottom', 'left', px0);
    set('cl-ax-left', 'top', py0);       // 가로축(x) 라벨 = y=0 가로선 좌/우에 정렬
    set('cl-ax-right', 'top', py0);
}

/** #cl-similar 목록: 포커스 밴드면 그 밴드 곡 전체 / 개요면 안내. */
function _clSimList(focus) {
    const box = document.getElementById('cl-similar');
    if (!box) return;
    const songs = (window.CLUSTER_DATA || {}).songs || [];
    if (focus) {
        const list = songs.filter(s => s.band === focus);
        const items = list.map(s =>
            `<li><span class="cl-dot" style="background:${_clBandColor(s.band)}"></span>${s.song}</li>`).join('');
        box.innerHTML = `<div class="cl-q"><b>${bandDisplay(focus)}</b> · ${list.length}곡 · 클릭=재생</div><ul>${items}</ul>`;
        return;
    }
    box.innerHTML = '<span class="cl-hint">밴드 원 호버=미리보기 · 클릭=그 밴드 보기 · 곡 클릭=재생</span>';
}

