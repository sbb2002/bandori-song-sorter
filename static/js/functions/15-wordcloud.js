// ===========================================================
// BanG Dream! Song Sorter — 15-wordcloud.js
// §14.5 밴드 워드클라우드(F)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 14.5 Band wordcloud (F)
// ───────────────────────────

const WC_PALETTE = ['#c084fc', '#ff6b9d', '#ff9f6b', '#ffd06b', '#6bcfff', '#cfd0ea'];

// 밴드 퍼스널 컬러(HANDOFF #2 확정) — 워드클라우드 키워드 색. ALL은 WC_PALETTE 유지.
const BAND_COLORS = {
    poppin_party: '#ff3377', afterglow: '#ee3344', pastel_palettes: '#33ddaa',
    roselia: '#3344aa', hello_happy_world: '#ffdd00', morfonica: '#33aaff',
    raise_a_suilen: '#33cccc', mygo: '#0088bb', ave_mujica: '#881144',
    mugendai_mutype: '#ff7788', millsage: '#aa22ee', ikka_dump_rock: '#ffaa33',
};

// 투톤 밴드의 보조색(키워드 아랫부분에만 살짝). 미정의 밴드는 단색.
const BAND_SUBCOLORS = {
    mugendai_mutype: '#2288dd',
};

/** 한 밴드 키워드를 표시텍스트(ko‖jp)로 병합 → Map(text → weight 합). 心·気→마음 통합. */
function mergeBandKeywords(keywords) {
    const m = new Map();
    (keywords || []).forEach(k => {
        const text = ((k.ko || k.jp) || '').trim();
        if (text) m.set(text, (m.get(text) || 0) + (k.weight || 1));
    });
    return m;
}

/** 표시텍스트별 문서빈도(등장 밴드 수). TF-IDF 차별성용 — 1회 계산 후 캐시. */
let _wcDocFreq = null;
function wordcloudDocFreq(data) {
    if (_wcDocFreq) return _wcDocFreq;
    const df = new Map();
    for (const b in data) {
        for (const text of mergeBandKeywords(data[b].keywords).keys())
            df.set(text, (df.get(text) || 0) + 1);
    }
    _wcDocFreq = df;
    return df;
}

/** currentBand 키워드 목록.
 *  ALL    = 전 밴드 원빈도 합산(뱅드림 IP 공유 정서).
 *  밴드별 = TF-IDF 차별성(IP 공통어 누르고 밴드 고유어 부각). */
function wordcloudList(band) {
    const data = window.WORDCLOUD_DATA || {};
    if (band === 'ALL') {
        const merged = new Map();
        for (const b in data)
            for (const [t, w] of mergeBandKeywords(data[b].keywords))
                merged.set(t, (merged.get(t) || 0) + w);
        return { list: [...merged.entries()].sort((a, b) => b[1] - a[1]), songCount: 0 };
    }
    if (!data[band]) return { list: [], songCount: 0 };

    const df = wordcloudDocFreq(data);
    const N = Object.keys(data).length;
    const merged = mergeBandKeywords(data[band].keywords);
    const list = [...merged.entries()]
        .map(([t, w]) => [t, w * (Math.log((N + 1) / ((df.get(t) || 1) + 1)) + 1)])
        .sort((a, b) => b[1] - a[1]);
    return { list, songCount: data[band].song_count || 0 };
}

/** currentBand 워드클라우드 렌더. 패널이 보일 때만 동작(숨김 시 캔버스 크기 0). */
function renderWordcloud() {
    const wrap = document.getElementById('wordcloud-wrap');
    const canvas = document.getElementById('wordcloud-canvas');
    const empty = document.getElementById('wc-empty');
    if (!wrap || !canvas) return;

    document.getElementById('bi-band-name').textContent =
        (currentBand === 'ALL' ? '전체' : bandDisplay(currentBand)) + ' 워드클라우드';

    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (w === 0 || h === 0) return;     // 숨김 상태 → 탭 전환 시 재호출됨
    canvas.width = w; canvas.height = h;

    const { list, songCount } = wordcloudList(currentBand);
    const subEl = document.getElementById('bi-sub');

    if (!window.WordCloud || list.length === 0) {
        canvas.getContext('2d').clearRect(0, 0, w, h);
        empty.hidden = false;
        subEl.textContent = '';
        return;
    }
    empty.hidden = true;
    subEl.textContent = (currentBand === 'ALL')
        ? `전 밴드 키워드 ${list.length}개 병합`
        : `조회수 TOP10 가사 ${songCount}곡 · 키워드 ${list.length}개`;

    // 상위 40개만(좁은 패널 가독성) + 후렴 반복 완화를 위해 sqrt로 폰트 압축
    const top = list.slice(0, 40);
    const sq = v => Math.sqrt(v);
    const maxW = sq(top[0][1]), minW = sq(top[top.length - 1][1]);
    const span = Math.max(1e-6, maxW - minW);
    const FMIN = Math.max(15, Math.round(h / 15)), FMAX = Math.round(h / 5);
    const items = top.map(([text, wt]) => {
        const t = (sq(wt) - minW) / span;          // 0..1
        return [text, Math.round(FMIN + t * (FMAX - FMIN))];
    });

    // 글로우 적용 임계: 표시 키워드 폰트(t) 분포의 Q2(중앙값) → 상위 절반에 네온
    const tArr = items.map(it => FMAX > FMIN ? (it[1] - FMIN) / (FMAX - FMIN) : 1)
        .sort((a, b) => a - b);
    const _mid = tArr.length >> 1;
    const q2 = tArr.length % 2 ? tArr[_mid] : (tArr[_mid - 1] + tArr[_mid]) / 2;

    // 밴드별 = 퍼스널 컬러(hue 고정) + 빈도 명도 변주 / ALL = 단어 해시 6색 팔레트
    const baseHsl = currentBand === 'ALL' ? null : hexToHsl(BAND_COLORS[currentBand] || '#c084fc');
    const subHsl = baseHsl && BAND_SUBCOLORS[currentBand]
        ? hexToHsl(BAND_SUBCOLORS[currentBand]) : null;
    const ctx = canvas.getContext('2d');
    // hue 고정·빈도(t)로 명도 변주한 hsl. 저빈도는 가라앉히고 고빈도를 강조(35%~82%).
    const lum = t => 35 + 47 * t;
    const tone = (hsl, t) => `hsl(${hsl.h}, ${Math.max(55, hsl.s)}%, ${lum(t)}%)`;

    window.WordCloud(canvas, {
        list: items,
        weightFactor: 1,                            // size = 위에서 계산한 폰트 px
        fontFamily: "'M PLUS Rounded 1c', 'Inter', sans-serif",
        fontWeight: '700',
        color: (word, weight, fontSize) => {
            if (!baseHsl) {                         // ALL → 단어 해시 6색 팔레트
                ctx.shadowBlur = 0;                 // 네온 잔여 차단
                let hsh = 0;
                for (let i = 0; i < word.length; i++) hsh = (hsh * 31 + word.charCodeAt(i)) | 0;
                return WC_PALETTE[Math.abs(hsh) % WC_PALETTE.length];
            }
            // 폰트 px(FMIN~FMAX)를 0~1로 → 고빈도일수록 밝고 선명(다크 배경 가독성)
            const t = FMAX > FMIN ? Math.min(1, Math.max(0, (weight - FMIN) / (FMAX - FMIN))) : 1;
            // 폰트 분포 Q2(중앙값) 이상(상위 절반)에만 같은 색 네온 글로우. 그 외는 해제.
            if (t >= q2) {
                ctx.shadowColor = `hsl(${baseHsl.h}, ${Math.max(55, baseHsl.s)}%, ${lum(t)}%)`;
                ctx.shadowBlur = 8;
            } else {
                ctx.shadowBlur = 0;
            }
            const main = tone(baseHsl, t);
            if (!subHsl) return main;
            // 투톤: textBaseline=middle 기준 위(메인)→아래 끝 ~22%만 보조색 그라데이션
            const size = fontSize || weight;
            const grad = ctx.createLinearGradient(0, -size / 2, 0, size / 2);
            grad.addColorStop(0, main);
            grad.addColorStop(0.78, main);
            grad.addColorStop(1, tone(subHsl, t));
            return grad;
        },
        backgroundColor: 'transparent',
        rotateRatio: 0,                             // 한글 가독성 — 가로 고정
        gridSize: Math.max(8, Math.round(w / 48)),  // 단어 간 여백 확대(과밀 완화)
        drawOutOfBound: false,
        shrinkToFit: true,
        clearCanvas: true,
    });
}

