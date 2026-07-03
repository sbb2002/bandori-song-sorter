// ===========================================================
// BanG Dream! Song Sorter — 07-song-list.js
// §7 곡 리스트(B) 렌더 + 제목 넘침 마퀴
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 7. Render: Song list (B)
// ───────────────────────────

function renderSongList() {
    const list = document.getElementById('song-list');
    hideCommentTip();   // 행이 새로 그려지면 기존 툴팁 앵커가 무효
    const songs = viewSongs();
    const frag = document.createDocumentFragment();

    if (songs.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'song-empty';
        empty.textContent = (activeFilters.size > 0 || currentType !== 'all') ? '해당 조건의 곡이 없어요.' : '곡이 없어요.';
        frag.appendChild(empty);
    }

    songs.forEach((song, i) => {
        const r = getRank(song);
        const showBand = (currentBand === 'ALL');

        const row = document.createElement('div');
        const playing = nowPlaying && nowPlaying === C.songKey(song.band, song.title);
        row.className = 'song-item' + (C.isRank(r) ? ' ranked' : '') + (playing ? ' playing' : '');
        row.dataset.band = song.band;
        row.dataset.title = song.title;
        row.dataset.url = song.url || '';
        if (C.isRank(r)) row.style.setProperty('--row-tier', TIER_BY_KEY[r].color);

        const num = document.createElement('span');
        num.className = 'song-num';
        num.textContent = i + 1;
        row.appendChild(num);

        const titleEl = document.createElement('span');
        titleEl.className = 'song-title';
        const titleText = document.createElement('span');
        titleText.className = 'st-text';
        titleText.textContent = song.title;
        titleEl.appendChild(titleText);
        row.appendChild(titleEl);

        if (showBand) {
            const sub = document.createElement('span');
            sub.className = 'song-band-tag';
            sub.textContent = bandDisplay(song.band);
            row.appendChild(sub);
        }

        if (!C.isPlayable(song.url)) {
            const noyt = document.createElement('span');
            noyt.className = 'song-noyt';
            noyt.title = '유튜브 링크 없음';
            noyt.textContent = '♪';
            row.appendChild(noyt);
        }

        // 코멘트: 호버/탭 툴팁용으로 행에 보존(티어 무관). 뱃지는 티어 확정 + 코멘트 있을 때만.
        const comment = getComment(song);
        if (comment) {
            row.dataset.comment = comment;
            if (C.isRank(r)) {
                const cbadge = document.createElement('span');
                cbadge.className = 'comment-badge';
                cbadge.title = '메모 보기';
                cbadge.textContent = '💬';
                row.appendChild(cbadge);
            }
        }

        const badge = document.createElement('span');
        badge.className = 'rank-badge ' + (C.isRank(r) ? 'rb-' + r : 'rb-empty');
        badge.textContent = C.isRank(r) ? TIER_BY_KEY[r].icon : '';
        row.appendChild(badge);

        frag.appendChild(row);
    });

    list.innerHTML = '';
    list.appendChild(frag);
    markSongTitleOverflow();
}

/** 곡 이름이 슬롯보다 길면 .is-overflow 부여 + 마퀴 이동량(--st-shift)/속도(--st-dur) 설정.
 *  실제 넘칠 때만 호버/재생 중 마퀴가 돈다(짧은 이름은 그대로 말줄임). 읽기→쓰기 분리로 리플로우 최소화. */
function markSongTitleOverflow() {
    const els = document.querySelectorAll('#song-list .song-title');
    const measures = [];
    els.forEach(el => {
        const txt = el.firstElementChild;               // .st-text
        if (txt) measures.push([el, txt.scrollWidth - el.clientWidth]);
    });
    measures.forEach(([el, shift]) => {
        if (shift > 2) {
            el.classList.add('is-overflow');
            el.style.setProperty('--st-shift', `-${shift + 8}px`);
            el.style.setProperty('--st-dur', `${Math.max(3, (shift + 8) / 45).toFixed(1)}s`);
        } else {
            el.classList.remove('is-overflow');
            el.style.removeProperty('--st-shift');
            el.style.removeProperty('--st-dur');
        }
    });
}

function songFromRow(row) {
    const band = row.dataset.band;
    const title = row.dataset.title;
    const arr = dedupedByBand[band] || [];
    return arr.find(s => s.title === title) || { band, title, url: row.dataset.url };
}

