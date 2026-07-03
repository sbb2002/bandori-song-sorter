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
const CL_SHRINK = 0.5;             // 곡을 밴드 중심으로 뭉치는 정도(고정). 곡별 y 노이즈 완화.

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

    let playingPt = null;                  // 재생 곡의 화면 좌표(effectScatter 파동용)
    const songMark = (s, val, base) => {   // 재생 곡이면 흰 테두리 override + 파동 좌표 기록
        let st = base;
        if (playKey && C.songKey(s.band, s.song) === playKey) {
            st = { op: 1, size: Math.max(base.size, 14), bc: '#fff', bw: 2 };
            playingPt = { value: val, itemStyle: { color: BAND_COLORS[s.band] || '#c084fc' } };
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
        centPts = [centMark(focus, [0, 0], 46, 1)];
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
        centPts = cents.map(c => centMark(c.band, [c.x, c.y],
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
                data: playingPt ? [playingPt] : [], symbolSize: 14, showEffectOn: 'render',
                rippleEffect: { period: 2.4, scale: 4.5, brushType: 'stroke' }, itemStyle: { opacity: 0.9 },
            },
        ],
    });
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

