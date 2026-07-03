// ===========================================================
// BanG Dream! Song Sorter — 12-heatmap.js
// §12 히트맵(E)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 12. Heatmap (E)
// ───────────────────────────

function renderHeatmap() {
    const grid = document.getElementById('heatmap-grid');
    const matrix = C.computeHeatmap(dedupedByBand, ranks);

    let globalMax = 1;
    bands.forEach(b => C.TIERS.forEach(t => {
        if (matrix[b][t.key] > globalMax) globalMax = matrix[b][t.key];
    }));

    grid.innerHTML = '';

    // 헤더: 빈칸 + 티어 라벨
    const corner = document.createElement('div');
    corner.className = 'hm-head';
    grid.appendChild(corner);
    C.TIERS.forEach(t => {
        const h = document.createElement('div');
        h.className = 'hm-head';
        h.style.color = t.color;
        h.textContent = t.label;
        grid.appendChild(h);
    });

    // 밴드 행 (좌측 셀렉터와 동일 순서)
    bandsInSelectorOrder().forEach(b => {
        const bandCell = document.createElement('div');
        bandCell.className = 'hm-band';
        bandCell.title = bandDisplay(b);
        const icon = document.createElement('img');
        icon.src = bandIcon(b);
        icon.alt = bandDisplay(b);
        icon.className = 'hm-band-icon';
        icon.onerror = () => { bandCell.textContent = bandDisplay(b).slice(0, 4); };
        bandCell.appendChild(icon);
        grid.appendChild(bandCell);

        C.TIERS.forEach(t => {
            const n = matrix[b][t.key];
            const cell = document.createElement('div');
            cell.className = 'hm-cell';
            cell.textContent = n > 0 ? n : '';
            if (n > 0) {
                const alpha = 0.18 + 0.82 * (n / globalMax);
                cell.style.background = hexToRgba(t.color, alpha);
                cell.style.color = alpha > 0.55 ? '#0e0e14' : t.color;
            }
            grid.appendChild(cell);
        });
    });
}

