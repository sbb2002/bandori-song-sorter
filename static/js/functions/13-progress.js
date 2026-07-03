// ===========================================================
// BanG Dream! Song Sorter — 13-progress.js
// §13 진행률/스탯 칩
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 13. Progress / Stat chips
// ───────────────────────────

function renderProgress() {
    const { ranked, total } = C.countRanked(allSongs, ranks);
    document.getElementById('progress-text').textContent = `${ranked} / ${total}곡 평가됨`;
    const pct = total ? (ranked / total * 100) : 0;
    document.getElementById('progress-fill').style.width = pct + '%';
    document.getElementById('bp-fill').style.width = pct + '%';
    document.getElementById('bp-pct').textContent = pct.toFixed(1) + '%';
}

function renderStatChips() {
    const counts = C.computeHistogram(allSongs, ranks);
    const { ranked, total } = C.countRanked(allSongs, ranks);
    const el = document.getElementById('stat-chips');
    el.innerHTML = '';

    C.TIERS.forEach(t => {
        const chip = document.createElement('div');
        chip.className = 'stat-chip';
        chip.innerHTML =
            `<span class="stat-dot" style="background:${t.color}"></span>${t.label} ${counts[t.key]}곡`;
        el.appendChild(chip);
    });

    const un = document.createElement('div');
    un.className = 'stat-chip stat-chip-muted';
    un.textContent = `미평가 ${total - ranked}곡`;
    el.appendChild(un);
}

