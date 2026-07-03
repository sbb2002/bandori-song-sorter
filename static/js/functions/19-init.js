// ===========================================================
// BanG Dream! Song Sorter — 19-init.js
// §17 Init (+ 분할로 이동된 상태 로드)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 17. Init
// ───────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // 상태 복원 — 분할 전 §1 최상위에서 즉시 로드하던 것을 여기로 이동(파일 간 함수 호이스팅 회피)
    ranks = loadRanks();
    comments = loadComments();

    initData();
    renderBandSelector();
    renderFilterPills();
    renderRankButtons();
    selectBand('ALL');     // 리스트 + 히스토그램 렌더 포함
    renderHeatmap();
    renderProgress();
    renderStatChips();
    switchTab('hist');     // 초기 탭 활성화(패널 표시)
    renderCluster();       // 음원맵: 하단 뷰 독에 상시 표시(밴드 무관 전역 뷰)
    renderWordcloud();     // 워드클라우드: 하단 뷰 독에 상시 표시(선택 밴드/ALL)
    initPressHandlers();

    document.getElementById('copy-btn').addEventListener('click', copyLinks);
    document.getElementById('download-btn').addEventListener('click', exportRanking);
    document.getElementById('reset-btn').addEventListener('click', resetRanks);
    document.getElementById('popup-cancel').addEventListener('click', closePopup);

    // 바깥(배경) 눌러 닫기 — 누른 지점과 뗀 지점이 '둘 다' 오버레이일 때만 닫는다.
    // 텍스트 선택 드래그가 팝업 밖에서 릴리스돼도(또는 그 반대) 닫히지 않게 함.
    const popupOverlay = document.getElementById('popup');
    let pressedOnOverlay = false;
    popupOverlay.addEventListener('pointerdown', e => {
        pressedOnOverlay = (e.target === popupOverlay);
    });
    popupOverlay.addEventListener('pointerup', e => {
        if (pressedOnOverlay && e.target === popupOverlay) closePopup();
        pressedOnOverlay = false;
    });

    document.addEventListener('keydown', e => {
        const popup = document.getElementById('popup');
        if (popup.hidden) return;
        if (e.key === 'Escape') { closePopup(); return; }
        // 메모 입력 중엔 숫자키 티어 단축키 비활성(메모에 숫자 입력 허용)
        if (e.target && e.target.id === 'popup-comment') return;
        const tier = parseInt(e.key);
        if (tier >= 1 && tier <= 5 && popupSong) applyTier(tier);
    });
    document.querySelectorAll('.tab-btn').forEach(b =>
        b.addEventListener('click', () => switchTab(b.dataset.tab)));
    document.querySelectorAll('.type-tab').forEach(b =>
        b.addEventListener('click', () => switchType(b.dataset.type)));

    // 말풍선/툴팁 밖을 누르면 고정 툴팁 닫기. 리사이즈 시에도 위치 어긋나니 숨김.
    document.addEventListener('pointerdown', e => {
        if (e.target.closest('.comment-badge') || e.target.closest('#comment-tip')) return;
        hideCommentTip();
    }, true);
    window.addEventListener('resize', hideCommentTip);
    // 하단 독은 캔버스/차트 픽셀 기준 → 리사이즈 시 워드클라우드 재렌더 + 음원맵 ECharts resize
    let vizResizeTimer = null;
    window.addEventListener('resize', () => {
        clearTimeout(vizResizeTimer);
        vizResizeTimer = setTimeout(() => {
            renderWordcloud();
            if (_clusterChart) _clusterChart.resize();
            markSongTitleOverflow();          // 슬롯 폭 변동 → 곡 이름 넘침 재측정
        }, 180);
    });

    // 이미 YT API가 준비된 경우 직접 초기화 (타이밍 역전 방지)
    if (window.YT && window.YT.Player) initYouTubePlayer();
});
