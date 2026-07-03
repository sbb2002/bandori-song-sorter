// ===========================================================
// BanG Dream! Song Sorter — 18-refresh.js
// §16 집계 뷰 갱신
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 16. Refresh aggregate views
// ───────────────────────────

function refreshAll() {
    renderSongList();
    renderHistogram();
    renderHeatmap();
    renderProgress();
    renderStatChips();
    updateBandRings();
}

