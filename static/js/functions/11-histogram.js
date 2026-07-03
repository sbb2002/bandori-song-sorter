// ===========================================================
// BanG Dream! Song Sorter — 11-histogram.js
// §11 히스토그램(D)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 11. Histogram (D)
// ───────────────────────────

function renderHistogram() {
    const counts = C.computeHistogram(bandSongs(), ranks);
    const max = Math.max(1, ...C.TIERS.map(t => counts[t.key]));
    const rows = document.getElementById('hist-rows');
    rows.innerHTML = '';

    C.TIERS.forEach(t => {
        const n = counts[t.key];
        const row = document.createElement('div');
        row.className = 'hist-row';

        const label = document.createElement('span');
        label.className = 'hist-label';
        label.style.color = t.color;
        label.textContent = t.label;

        const barBg = document.createElement('div');
        barBg.className = 'hist-bar-bg';
        const bar = document.createElement('div');
        bar.className = 'hist-bar';
        bar.style.background = t.color;
        bar.style.width = (n / max * 100) + '%';

        const count = document.createElement('span');
        count.className = 'hist-count';
        count.textContent = n;

        barBg.appendChild(bar);
        row.appendChild(label);
        row.appendChild(barBg);
        row.appendChild(count);
        rows.appendChild(row);
    });
}

