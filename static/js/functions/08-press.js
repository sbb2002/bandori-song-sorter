// ===========================================================
// BanG Dream! Song Sorter — 08-press.js
// §8 통합 프레스(짧게=재생/길게=팝업) + 코멘트 툴팁
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 8. 통합 프레스 (짧게=재생 / 길게=랭크 팝업) — mouse + touch
// ───────────────────────────

const LONG_PRESS_MS = 350;
const MOVE_TOLERANCE = 8;

let pressTimer = null;
let pressRow = null;
let pressStartX = 0;
let pressStartY = 0;
let lastY = 0;
let longFired = false;
let moved = false;

function startProgress(row) {
    void row.offsetWidth; // reflow → ::after가 right:100% 상태에서 transition 시작
    row.classList.add('pressing');
}

function cancelPress() {
    if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
    if (pressRow) pressRow.classList.remove('pressing');
    pressRow = null;
}

function initPressHandlers() {
    const list = document.getElementById('song-list');

    list.addEventListener('pointerdown', e => {
        const cbadge = e.target.closest('.comment-badge');
        if (cbadge) {
            // 말풍선 탭 → 메모 토글. 재생/팝업·스크롤 진입 안 함(캡처 미설정).
            toggleCommentTip(cbadge.closest('.song-item'));
            return;
        }
        const row = e.target.closest('.song-item');
        if (!row) return;
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        list.setPointerCapture(e.pointerId);
        pressRow = row;
        pressStartX = e.clientX;
        pressStartY = lastY = e.clientY;
        longFired = false;
        moved = false;
        startProgress(row);
        pressTimer = setTimeout(() => {
            longFired = true;
            const r = pressRow;
            cancelPress();
            openPopup(songFromRow(r));
        }, LONG_PRESS_MS);
    });

    list.addEventListener('pointermove', e => {
        const dy = e.clientY - lastY;
        lastY = e.clientY;

        if (moved) {
            list.scrollTop -= dy;
            return;
        }
        if (!pressRow) return;
        if (Math.abs(e.clientX - pressStartX) > MOVE_TOLERANCE ||
            Math.abs(e.clientY - pressStartY) > MOVE_TOLERANCE) {
            moved = true;
            cancelPress();
            list.scrollTop -= dy;
        }
    });

    list.addEventListener('pointerup', e => {
        if (moved) { moved = false; return; }
        if (!pressRow) return;
        const row = pressRow;
        const fired = longFired;
        cancelPress();
        if (!fired) playSong(songFromRow(row));
    });

    list.addEventListener('pointerleave', e => {
        moved = false;
        cancelPress();
    });

    // 데스크톱 우클릭 = 랭크 팝업 (+ 모바일 길게눌러 뜨는 기본 메뉴 차단)
    list.addEventListener('contextmenu', e => {
        const row = e.target.closest('.song-item');
        if (!row) return;
        e.preventDefault();
        cancelPress();
        openPopup(songFromRow(row));
    });

    // 스크롤하면 고정 위치 툴팁이 어긋나므로 숨김
    list.addEventListener('scroll', hideCommentTip, { passive: true });

    // 호버 지원 기기(데스크톱)만 — 행에 마우스 올리면 메모 툴팁. 터치는 말풍선 탭으로.
    if (window.matchMedia && window.matchMedia('(hover: hover)').matches) {
        list.addEventListener('mouseover', e => {
            if (tipPinned) return;
            const row = e.target.closest('.song-item');
            if (!row || row === tipRow) return;
            const c = commentForRow(row);
            if (c) showCommentTip(row, c, false);
            else hideCommentTip();
        });
        list.addEventListener('mouseout', e => {
            if (tipPinned) return;
            const row = e.target.closest('.song-item');
            if (!row) return;
            // 같은 행 내부로의 이동이면 유지
            if (e.relatedTarget && row.contains(e.relatedTarget)) return;
            hideCommentTip();
        });
    }
}

// ───────────────────────────
// 8b. 코멘트 툴팁 (호버=데스크톱 / 탭=모바일) — 리스트 overflow 밖(body) 고정 배치
// ───────────────────────────

let tipRow = null;       // 현재 툴팁이 가리키는 행(없으면 null)
let tipPinned = false;   // true=탭으로 고정(호버로 사라지지 않음)

function commentForRow(row) {
    return (row && row.dataset.comment) || '';
}

/** 행 위쪽(공간 없으면 아래)·뷰포트 안에 클램프해 툴팁 표시. */
function showCommentTip(row, text, pinned) {
    const tip = document.getElementById('comment-tip');
    if (!tip) return;
    tip.textContent = text;
    tip.hidden = false;
    tip.style.visibility = 'hidden';     // 크기 측정용 선표시
    const anchor = row.querySelector('.comment-badge') || row;
    const ar = anchor.getBoundingClientRect();
    const tr = tip.getBoundingClientRect();
    let left = ar.left + ar.width / 2 - tr.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tr.width - 8));
    let top = ar.top - tr.height - 8;
    if (top < 8) top = ar.bottom + 8;    // 위 공간 부족하면 아래로
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
    tip.style.visibility = '';
    tipRow = row;
    tipPinned = !!pinned;
}

function hideCommentTip() {
    const tip = document.getElementById('comment-tip');
    if (tip) tip.hidden = true;
    tipRow = null;
    tipPinned = false;
}

/** 말풍선 탭: 같은 행이 이미 고정돼 있으면 닫고, 아니면 고정 표시. */
function toggleCommentTip(row) {
    const c = commentForRow(row);
    if (!c) { hideCommentTip(); return; }
    if (tipPinned && tipRow === row) hideCommentTip();
    else showCommentTip(row, c, true);
}

