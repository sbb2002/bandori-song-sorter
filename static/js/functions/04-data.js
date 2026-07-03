// ===========================================================
// BanG Dream! Song Sorter — 04-data.js
// §4 Data init (dedupe/flatten)
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 4. Data init
// ───────────────────────────

function initData() {
    const data = window.SONG_DATA || { bands: [], songsByBand: {} };
    bands = data.bands.slice();
    dedupedByBand = {};
    allSongs = [];
    bands.forEach(b => {
        dedupedByBand[b] = C.dedupSongs(data.songsByBand[b] || []);
        allSongs = allSongs.concat(dedupedByBand[b]);
    });
}

/** 현재 밴드(또는 ALL)의 곡 — 히스토그램/진행률 등 분포 계산용(필터 무시) */
function bandSongs() {
    return currentBand === 'ALL' ? allSongs : (dedupedByBand[currentBand] || []);
}

/** 커버곡 판별 — RSS 반영분은 album_title 'Covers' + 곡명에 '(Cover)' 표기 */
function isCover(song) {
    return song.album === 'Covers' || /\(cover\)/i.test(song.title);
}

/** 리스트 표시용 곡 — 밴드 + 곡 종류(ALL/Ori/Cover) + 활성 티어 필터 적용 */
function viewSongs() {
    let songs = bandSongs();
    if (currentType === 'ori') songs = songs.filter(s => !isCover(s));
    else if (currentType === 'cover') songs = songs.filter(isCover);
    if (activeFilters.size > 0) {
        songs = songs.filter(s => {
            const r = getRank(s);
            const unranked = !C.isRank(r);
            if (activeFilters.has(0) && unranked) return true;
            return !unranked && activeFilters.has(r);
        });
    }
    return songs;
}

