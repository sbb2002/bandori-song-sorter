// ===========================================================
// BanG Dream! Song Sorter — 03-persistence.js
// §3 localStorage 랭크/코멘트 로드·저장
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 3. Persistence
// ───────────────────────────

function loadRanks() {
    try {
        return JSON.parse(localStorage.getItem(STORE_KEY)) || {};
    } catch (_) {
        return {};
    }
}

function saveRanks() {
    try {
        localStorage.setItem(STORE_KEY, JSON.stringify(ranks));
    } catch (_) { /* 사생활 모드 등 — 저장 실패는 무시 */ }
}

function getRank(song) {
    return ranks[C.songKey(song.band, song.title)];
}

function setRank(song, tier) {
    const key = C.songKey(song.band, song.title);
    if (tier == null) {
        delete ranks[key];
    } else {
        ranks[key] = tier;
    }
    saveRanks();
}

function loadComments() {
    try {
        return JSON.parse(localStorage.getItem(COMMENTS_KEY)) || {};
    } catch (_) {
        return {};
    }
}

function saveComments() {
    try {
        localStorage.setItem(COMMENTS_KEY, JSON.stringify(comments));
    } catch (_) { /* 사생활 모드 등 — 저장 실패는 무시 */ }
}

function getComment(song) {
    return comments[C.songKey(song.band, song.title)] || '';
}

/** 코멘트 저장 — 공백뿐이면 키 삭제(빈 코멘트 미보존). 티어와 무관하게 저장됨. */
function setComment(song, text) {
    const key = C.songKey(song.band, song.title);
    const v = (text == null ? '' : String(text)).trim();
    if (v) comments[key] = v;
    else delete comments[key];
    saveComments();
}

