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
let _clSensIdx = 0;                // [실험] 선택된 감도 레벨 인덱스(탭)
const CL_SHRINK = 0.5;             // 곡을 밴드 중심으로 뭉치는 정도(고정). 곡별 y 노이즈 완화.
// various_artists = 여러 아티스트 묶음 → '밴드 중심점'이 의미 없음(이질적 곡 평균, y 폭주).
// 센트로이드(중심 아이콘)만 숨기고 곡 점은 그대로 유지. score·신뢰도막대·최애 후보 제외와 일관(14-share.js).
const clHideCentroid = b => b === 'various_artists';
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
// [실험] beat 그리드 방식: 각 박의 볼륨(v)을 5단계로 나눠 크기 결정(강=크고 느리게 / 약=작고 빠르게).
// build_beat_track.py 의 events{t,v} 와 짝.
const CL_PULSE_R5 = [16, 24, 32, 40, 48];      // 볼륨 5단계 크기(px)
function _clVolStep(v) { return Math.max(1, Math.min(5, Math.ceil(v * 5))); }   // v 0~1 → 1~5
// [실험] subdivision 탭(메인 버전에선 CL_ONSET_TABS=false). 라벨은 build_beat_track SUBDIV 순서와 동기.
const CL_ONSET_TABS = true;
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

// [실험] 커스텀 펄스: 박 타이밍마다 원 하나가 짧게(CL_PULSE_SPREAD_MS) 커지며 사라진다.
// effectScatter의 연속 물결과 달리 '발생 간격(period)'과 '퍼지는 속도(spread)'를 분리 → 박자감.
function _clEmitPulse(r, ms) {
    if (!_clusterChart || !_clPlay) return;
    const px = _clusterChart.convertToPixel({ seriesIndex: 0 }, _clPlay.val);   // songs 좌표계 → 픽셀
    if (!px) return;
    const maxR = r || CL_PULSE_MAX_R, dur = ms || CL_PULSE_SPREAD_MS;
    const circle = new echarts.graphic.Circle({
        shape: { cx: px[0], cy: px[1], r: 4 }, silent: true, z: 100,
        style: { stroke: _clPlay.color, fill: 'none', lineWidth: 2, opacity: 0.9 },
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

// ── [파일럿] onset 트랙 재생: 유튜브 타임스탬프(getCurrentTime)에 맞춰 사전분석 이벤트로 펄스 ──
// 이벤트 {t 시각, v 볼륨(→크기), sus 서스테인(→퍼지는 시간)}. build_onset_track.py 산출.
// 지금은 1곡만 매핑(window.CLUSTER_ONSETS[id]) — 검증 후 전곡 확대.
const CL_ONSET_PILOT = {};
[
    ['afterglow', 'ON YOUR MARK', 'afterglow__000'],
    ['ave_mujica', 'KiLLKiSS', 'ave_mujica__072'],
    ['hello_happy_world', 'キミがいなくちゃっ！', 'hello_happy_world__106'],
    ['morfonica', 'Daylight -デイライト-', 'morfonica__180'],
    ['mugendai_mutype', 'アイの夢限', 'mugendai_mutype__237'],
    ['mygo', '迷星叫', 'mygo__260'],
    ['pastel_palettes', 'TITLE IDOL', 'pastel_palettes__301'],
].forEach(([b, s, id]) => { CL_ONSET_PILOT[C.songKey(b, s)] = id; });
// [실험] 곡별 기본 subdivision(0=박·1=8분·2=16분). 현재 전곡 '박' 고정.
// tempo/bpm 으로 8분 여부 자동판정 불가(같은 tempo·비율에 선호 상반 — report 참조)라,
// 8분이 나은 곡(afterglow·mugendai 등)의 공통 패턴을 찾으면 그때 예외를 큐레이션한다.
const CL_ONSET_DEFDIV = {};   // 예: CL_ONSET_DEFDIV[C.songKey('afterglow','ON YOUR MARK')] = 1;
function _clOnsetTrack(key) {
    const id = CL_ONSET_PILOT[key];
    return (id && (window.CLUSTER_ONSETS || {})[id]) || null;
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
    _clSensIdx = CL_ONSET_DEFDIV[key] || 0;    // 곡별 기본 subdivision(박/8분 큐레이션)
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
function _clOnsetTick() {
    _clRafId = requestAnimationFrame(_clOnsetTick);
    if (!_clOnset || !player || typeof player.getCurrentTime !== 'function') return;
    const lv = _clOnset.levels[_clSensIdx];
    if (!lv) return;
    const ev = lv.events, now = player.getCurrentTime() || 0;
    if (now < _clOnsetLastNow - 0.3) _clOnsetIdx = _clBisect(ev, now);   // 뒤로 시크 → 포인터 재설정
    _clOnsetLastNow = now;
    while (_clOnsetIdx < ev.length && ev[_clOnsetIdx].t <= now) {
        const e = ev[_clOnsetIdx++];
        if (now - e.t <= 0.25) {            // 밀린 과거 이벤트(랙/앞 시크)는 스킵해 폭발 방지
            const step = _clVolStep(e.v);                          // 볼륨 → 크기 단계 1~5
            const maxR = CL_PULSE_R5[step - 1];
            const speed = CL_PULSE_SPEED * (1.25 - step * 0.11);   // 큰 펄스일수록 느리게(묵직)
            _clEmitPulse(maxR, Math.min(CL_PULSE_DUR_MAX, maxR / speed * 1000));
        }
    }
}

// 재생 곡/주기가 바뀔 때만 타이머 재설정(같으면 유지 → 재draw로 리듬 안 끊김).
// onset 트랙이 있는 곡이면 BPM 대신 타임스탬프 동기 재생(_clStartOnset).
function _clSyncPulse(period) {
    if (!CL_PULSE_BPM || !_clPlay) { _clStopPulse(); _clStopOnset(); return; }
    const track = _clOnsetTrack(nowPlaying);
    if (track) { _clStopPulse(); _clStartOnset(nowPlaying, track); return; }
    _clStopOnset();
    if (!period) { _clStopPulse(); return; }
    const key = nowPlaying + '@' + period;
    if (key === _clPulseKey) return;
    _clStopPulse();
    _clPulseKey = key;
    _clEmitPulse();                                   // 박 시작 즉시 1발
    _clPulseTimer = setInterval(_clEmitPulse, period * 1000);
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
        window.addEventListener('resize', () => _clusterChart && _clusterChart.resize());
        _clusterChart.setOption({                 // 정적 베이스(1회)
            backgroundColor: 'transparent',
            animation: true, animationDuration: 0,        // 초기=즉시 / 클릭 이동=애니메이션
            animationDurationUpdate: 350, animationEasingUpdate: 'cubicOut',
            tooltip: {
                trigger: 'item', confine: true,
                backgroundColor: 'rgba(20,20,30,0.95)', borderColor: '#2a2a3a',
                textStyle: { color: '#e8e8f0', fontSize: 11 },
                formatter: p => p.data && p.data._song
                    ? `<b>${p.data._song}</b><br>${bandDisplay(p.data._band)} · 클릭=재생`
                    : (p.data && p.data._n != null
                        ? `<b>${bandDisplay(p.data._band)}</b> · ${p.data._n}곡 (클릭=이 밴드 보기)` : ''),
            },
            grid: { left: 6, right: 6, top: 6, bottom: 6 },
            xAxis: { type: 'value', show: false, scale: true },
            yAxis: { type: 'value', show: false, scale: true },
            dataZoom: [                        // 휠/핀치 줌·드래그 팬(점 유지)
                { type: 'inside', xAxisIndex: 0, filterMode: 'none' },
                { type: 'inside', yAxisIndex: 0, filterMode: 'none' },
            ],
        });
        _clusterChart.on('click', p => {
            if (p.seriesIndex === 0) {             // 곡 클릭 = 재생(이미 재생 중이면 무시)
                const s = p.data;
                if (s && s._url && C.songKey(s._band, s._song) !== nowPlaying)
                    playSong({ band: s._band, title: s._song, url: s._url });
            } else if (p.seriesIndex === 1) {      // 센트로이드 클릭 = 그 밴드를 셀렉터에서 고른 것과 동일
                if (currentBand === 'ALL') selectBand(p.data._band);
            }
        });
        _clusterChart.on('mouseover', p => {       // ALL 모드: 센트로이드 호버 = 그 밴드 확장 미리보기
            if (currentBand === 'ALL' && p.seriesIndex === 1) { _clHover = p.data._band; _clDraw(); }
        });
        _clusterChart.on('mouseout', p => {
            if (currentBand === 'ALL' && p.seriesIndex === 1 && _clHover) { _clHover = null; _clDraw(); }
        });
        _clusterChart.getZr().on('click', e => {   // 포커스 모드에서 빈 영역 클릭 = ALL(개요)로 복귀
            if (!e.target && currentBand !== 'ALL') selectBand('ALL');
        });
    }
    _clBuildSensTabs();            // [실험] 감도 탭(1회 생성, idempotent)
    _clHover = null;                // 재진입 시 호버 초기화(포커스는 currentBand 따라감)
    _clDraw();
    _clusterChart.resize();
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
    const wrap = document.getElementById('cluster-wrap');   // 밴드 선택 시 그 밴드 퍼스널 컬러를 배경에 은은히 깔기
    // various_artists는 밴드가 아니므로(센트로이드도 숨김) 배경도 ALL과 동일하게 기본 서피스 유지.
    if (wrap) wrap.style.background =
        (currentBand !== 'ALL' && !clHideCentroid(currentBand)) ? _clBandBg(currentBand) : '';

    let playingPt = null;                  // 재생 곡의 화면 좌표(effectScatter 파동용)
    const songMark = (s, val, base) => {   // 재생 곡이면 흰 테두리 override + 파동 좌표 기록
        let st = base;
        if (playKey && C.songKey(s.band, s.song) === playKey) {
            st = { op: 1, size: Math.max(base.size, 14), bc: '#fff', bw: 2 };
            playingPt = { value: val, itemStyle: { color: BAND_COLORS[s.band] || '#c084fc' }, _bpm: s.bpm };
        }
        return {
            value: val, name: s.song, symbolSize: st.size,
            itemStyle: { color: BAND_COLORS[s.band] || '#c084fc', opacity: st.op, borderColor: st.bc, borderWidth: st.bw },
            _band: s.band, _song: s.song, _url: s.url,
        };
    };
    const centMark = (band, val, size, opacity) => ({   // 센트로이드 = 밴드 아이콘 PNG
        value: val, symbol: 'image://' + bandIcon(band), symbolSize: size,
        name: bandDisplay(band), itemStyle: { opacity: opacity },
        _band: band, _n: (cById[band] || {}).n,
    });

    let songPts, centPts, xAxis, yAxis;
    if (focus) {
        // 포커스: 그 밴드만 · 센트로이드=원점 · 곡=센트로이드 기준 offset · 대칭범위로 정중앙
        const c = cById[focus];
        const list = songs.filter(s => s.band === focus);
        songPts = list.map(s => songMark(s, [s.x - c.x, s.y - c.y], { op: 0.9, size: 12, bc: 'rgba(255,255,255,0.85)', bw: 1 }));
        let Mx = 1, My = 1;
        list.forEach(s => { Mx = Math.max(Mx, Math.abs(s.x - c.x)); My = Math.max(My, Math.abs(s.y - c.y)); });
        xAxis = { min: -Mx * 1.3, max: Mx * 1.3 }; yAxis = { min: -My * 1.3, max: My * 1.3 };
        centPts = clHideCentroid(focus) ? [] : [centMark(focus, [0, 0], 46, 1)];
        if (subEl) subEl.textContent = `${bandDisplay(focus)} · 곡 ${list.length} · 곡 클릭=재생 · 빈 곳=개요로`;
    } else {
        // ALL 개요: 전 밴드 항상 뭉침(이동 없음). 호버 밴드만 부각, 나머지는 투명도만 낮춤.
        const expB = _clHover;
        songPts = songs.map(s => {
            const c = cById[s.band] || { x: 0, y: 0 };
            const val = [c.x + CL_SHRINK * (s.x - c.x), c.y + CL_SHRINK * (s.y - c.y)];
            const faded = expB && s.band !== expB;
            return songMark(s, val, faded ? { op: 0.12, size: 8, bc: 'rgba(0,0,0,0.3)', bw: 0.5 }
                                          : { op: 0.6, size: 9, bc: 'rgba(0,0,0,0.3)', bw: 0.5 });
        });
        centPts = cents.filter(c => !clHideCentroid(c.band)).map(c => centMark(c.band, [c.x, c.y],
            expB === c.band ? 40 : 34, (expB && expB !== c.band) ? 0.35 : 1));
        xAxis = { min: null, max: null }; yAxis = { min: null, max: null };
        if (subEl) subEl.textContent = `${(data.bands || []).length}밴드 · 곡 ${songs.length} · 거칢×정서 지각 2D`;
    }

    const rangeKey = focus || 'ALL';        // 모드/밴드 바뀔 때만 축범위 갱신(줌/팬 보존)
    const axisOpt = {};
    if (rangeKey !== _clRangeKey) { axisOpt.xAxis = xAxis; axisOpt.yAxis = yAxis; _clRangeKey = rangeKey; }
    _clusterChart.setOption({
        ...axisOpt,
        series: [
            { id: 'songs', type: 'scatter', data: songPts, z: 2, emphasis: { scale: 1.3 },
              markLine: focus ? _clOriginCross() : { silent: true, data: [] } },
            {
                id: 'cents', type: 'scatter', data: centPts, z: 5,
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
    _clSimList(focus);
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

/** #cl-similar 목록: 포커스 밴드면 그 밴드 곡 전체 / 개요면 안내. */
function _clSimList(focus) {
    const box = document.getElementById('cl-similar');
    if (!box) return;
    const songs = (window.CLUSTER_DATA || {}).songs || [];
    if (focus) {
        const list = songs.filter(s => s.band === focus);
        const items = list.map(s =>
            `<li><span class="cl-dot" style="background:${BAND_COLORS[s.band] || '#c084fc'}"></span>${s.song}</li>`).join('');
        box.innerHTML = `<div class="cl-q"><b>${bandDisplay(focus)}</b> · ${list.length}곡 · 클릭=재생</div><ul>${items}</ul>`;
        return;
    }
    box.innerHTML = '<span class="cl-hint">밴드 원 호버=미리보기 · 클릭=그 밴드 보기 · 곡 클릭=재생</span>';
}

