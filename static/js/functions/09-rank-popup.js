// ===========================================================
// BanG Dream! Song Sorter — 09-rank-popup.js
// §9 랭크 팝업(모달)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 9. Rank popup (modal)
// ───────────────────────────

let popupSong = null;

function renderRankButtons() {
    const wrap = document.getElementById('rank-buttons');
    wrap.innerHTML = '';
    C.TIERS.forEach(t => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'rank-btn';
        btn.dataset.tier = t.key;
        btn.innerHTML =
            `<span class="rk-icon">${t.icon}</span><span class="rk-label" style="color:${t.color}">${t.label}</span>`;
        // 같은 티어 다시 누르면 해제(토글), 아니면 설정 — applyTier가 메모 커밋까지 처리
        btn.addEventListener('click', () => applyTier(t.key));
        wrap.appendChild(btn);
    });
}

function openPopup(song) {
    popupSong = song;
    document.getElementById('popup-band').textContent = bandDisplay(song.band);
    document.getElementById('popup-title').textContent = song.title;
    const cur = getRank(song);
    document.querySelectorAll('.rank-btn').forEach(b => {
        b.classList.toggle('active', Number(b.dataset.tier) === cur);
    });
    const ta = document.getElementById('popup-comment');
    if (ta) ta.value = getComment(song);
    const popup = document.getElementById('popup');
    popup.hidden = false;
    requestAnimationFrame(() => popup.classList.add('open'));
}

/** 팝업의 메모 textarea → comments 저장. 닫힘·티어선택 시 호출(티어 없어도 메모 보존).
 *  실제로 값이 바뀌었으면 true 반환(호출부가 리스트 갱신 여부 판단). */
function commitComment() {
    if (!popupSong) return false;
    const ta = document.getElementById('popup-comment');
    if (!ta) return false;
    const before = getComment(popupSong);
    const after = ta.value.trim();
    if (before === after) return false;
    setComment(popupSong, after);
    return true;
}

/** 티어 적용(토글) 공통 경로 — 메모 먼저 커밋해 리스트 뱃지에 즉시 반영. */
function applyTier(tier) {
    if (popupSong) {
        commitComment();
        const cur = getRank(popupSong);
        setRank(popupSong, cur === tier ? null : tier);
        refreshAll();
    }
    closePopup();
}

function closePopup() {
    // 취소/Esc/오버레이로 닫아도 메모는 저장. 변경됐으면 리스트(뱃지·툴팁)도 즉시 갱신.
    // (티어 경로는 applyTier가 이미 커밋·refreshAll → 여기선 false 반환되어 중복 렌더 없음)
    const commentChanged = popupSong ? commitComment() : false;
    const popup = document.getElementById('popup');
    popup.classList.remove('open');
    popupSong = null;
    setTimeout(() => { popup.hidden = true; }, 200);
    if (commentChanged) renderSongList();
}

