// ===========================================================
// BanG Dream! Song Sorter — 17-tabs-reset.js
// §15 탭/리셋
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 15. Tabs / Reset
// ───────────────────────────

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.getElementById('hist-panel').classList.toggle('active', tab === 'hist');
    document.getElementById('heat-panel').classList.toggle('active', tab === 'heat');
}

/** 곡 종류 탭 전환 (ALL/Ori/Cover) */
function switchType(type) {
    currentType = type;
    document.querySelectorAll('.type-tab').forEach(b =>
        b.classList.toggle('active', b.dataset.type === type));
    renderSongList();
}

function resetRanks() {
    if (!Object.keys(ranks).length) return;
    if (!confirm('모든 랭크를 초기화할까요? 되돌릴 수 없어요.')) return;
    ranks = {};
    saveRanks();
    refreshAll();
}

