// ===========================================================
// BanG Dream! Song Sorter — 02-utils.js
// §2 Path/표시 유틸 + TIER_BY_KEY
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 2. Path / 표시 유틸
// ───────────────────────────

/** GitHub Pages 경로 보정 (역슬래시 정규화 + 상대경로화) */
function fixPath(path) {
    if (!path) return '';
    if (path.startsWith('http') || path.startsWith('data:')) return path;
    let clean = path.replace(/\\/g, '/').trim();
    if (clean.startsWith('/')) clean = clean.substring(1);
    return './' + clean;
}

function bandIcon(band) {
    return fixPath('assets/icons/' + band + '.png');
}

/** snake_case 밴드명 → 가독 라벨 */
function bandDisplay(band) {
    if (band === 'ALL') return '전체 밴드';
    return band.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function hexToRgba(hex, a) {
    const m = hex.replace('#', '');
    const r = parseInt(m.substring(0, 2), 16);
    const g = parseInt(m.substring(2, 4), 16);
    const b = parseInt(m.substring(4, 6), 16);
    return `rgba(${r},${g},${b},${a})`;
}

/** #rrggbb → {h(0~360), s(0~100), l(0~100)}. 워드클라우드 명도 변주용. */
function hexToHsl(hex) {
    const m = hex.replace('#', '');
    const r = parseInt(m.substring(0, 2), 16) / 255;
    const g = parseInt(m.substring(2, 4), 16) / 255;
    const b = parseInt(m.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    const l = (max + min) / 2;
    let h = 0, s = 0;
    if (d !== 0) {
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h /= 6;
    }
    return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
}

const TIER_BY_KEY = {};
C.TIERS.forEach(t => { TIER_BY_KEY[t.key] = t; });

