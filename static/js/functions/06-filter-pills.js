// ===========================================================
// BanG Dream! Song Sorter — 06-filter-pills.js
// §6 티어 필터 알약
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 6. Render: Filter pills
// ───────────────────────────

function renderFilterPills() {
    const el = document.getElementById('filter-pills');
    el.innerHTML = '';
    const items = C.TIERS.map(t => ({ key: t.key, label: t.label, color: t.color }))
        .concat([{ key: 0, label: '미평가', color: null }]);

    items.forEach(({ key, label, color }) => {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'pill';
        pill.textContent = label;
        const active = activeFilters.has(key);
        if (active) {
            pill.classList.add('active');
            if (color) {
                pill.style.borderColor = color;
                pill.style.color = color;
                pill.style.background = hexToRgba(color, 0.12);
            } else {
                pill.style.borderColor = 'var(--text-sub)';
                pill.style.color = 'var(--text)';
            }
        }
        pill.addEventListener('click', () => {
            if (activeFilters.has(key)) activeFilters.delete(key);
            else activeFilters.add(key);
            renderFilterPills();
            renderSongList();
        });
        el.appendChild(pill);
    });
}

