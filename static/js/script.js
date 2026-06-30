/* ===========================
   BanG Dream! Song Sorter
   script.js — UI / 인터랙션 / 지속성

   순수 데이터 로직은 core.js(window.BandoriCore)에 위임한다.
=========================== */

const C = window.BandoriCore;

// ───────────────────────────
// 1. State
// ───────────────────────────

const STORE_KEY = 'bandori-song-ranks-v1';
const COMMENTS_KEY = 'bandori-song-comments-v1';   // 코멘트는 ranks와 별도 저장(스키마 무영향)

const BAND_ORDER = [
    'poppin_party', 'afterglow', 'pastel_palettes', 'roselia',
    'hello_happy_world', 'morfonica', 'raise_a_suilen', 'mygo',
    'ave_mujica', 'mugendai_mutype', 'millsage', 'ikka_dumb_rock'
];

let dedupedByBand = {};     // band -> 중복 제거된 곡 배열
let allSongs = [];          // 전 밴드 평탄화(밴드 순서)
let bands = [];             // 밴드 순서
let ranks = loadRanks();    // { songKey: 1..5 }
let comments = loadComments();  // { songKey: '메모 텍스트' }

let currentBand = 'ALL';
let currentType = 'all';         // 곡 종류 탭: 'all' | 'ori' | 'cover'
let activeFilters = new Set();   // 0=미평가, 1..5=티어. 비어있으면 전체 표시
let currentTab = 'hist';
let nowPlaying = null;           // 현재 재생 중(유튜브 프레임에 뜬) 곡의 songKey, 곡 리스트 강조용

// ───────────────────────────
// 2. Path / 표시 유틸
// ───────────────────────────

/** GitHub Pages 경로 보정 (역슬래시 정규화 + 상대경로화) */
function fixPath(path) {
    if (!path) return '';
    if (path.startsWith('http') || path.startsWith('data:')) return path;
    let clean = path.replace(/\\/g, '/').trim();
    if (clean.startsWith('/')) clean = clean.substring(1);
    return './' + clean;
}

function bandIcon(band) {
    return fixPath('assets/icons/' + band + '.png');
}

/** snake_case 밴드명 → 가독 라벨 */
function bandDisplay(band) {
    if (band === 'ALL') return '전체 밴드';
    return band.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function hexToRgba(hex, a) {
    const m = hex.replace('#', '');
    const r = parseInt(m.substring(0, 2), 16);
    const g = parseInt(m.substring(2, 4), 16);
    const b = parseInt(m.substring(4, 6), 16);
    return `rgba(${r},${g},${b},${a})`;
}

/** #rrggbb → {h(0~360), s(0~100), l(0~100)}. 워드클라우드 명도 변주용. */
function hexToHsl(hex) {
    const m = hex.replace('#', '');
    const r = parseInt(m.substring(0, 2), 16) / 255;
    const g = parseInt(m.substring(2, 4), 16) / 255;
    const b = parseInt(m.substring(4, 6), 16) / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    const l = (max + min) / 2;
    let h = 0, s = 0;
    if (d !== 0) {
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h /= 6;
    }
    return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
}

const TIER_BY_KEY = {};
C.TIERS.forEach(t => { TIER_BY_KEY[t.key] = t; });

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

// ───────────────────────────
// 5. Render: Band selector (A)
// ───────────────────────────

/** 밴드 나열 순서 = BAND_ORDER 우선 + 나머지(various_artists 등)는 뒤.
 *  좌측 셀렉터와 Download 결과가 동일 순서를 쓰도록 공유. */
function bandsInSelectorOrder() {
    const ordered = BAND_ORDER.filter(b => bands.includes(b));
    const rest = bands.filter(b => !BAND_ORDER.includes(b));
    return [...ordered, ...rest];
}

function renderBandSelector() {
    const el = document.getElementById('band-selector');
    el.innerHTML = '';

    el.appendChild(makeBandBtn('ALL', true));

    const divider = document.createElement('div');
    divider.className = 'band-divider';
    el.appendChild(divider);

    bandsInSelectorOrder().forEach(b => el.appendChild(makeBandBtn(b, false)));
}

function makeBandBtn(band, isAll) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'band-btn' + (isAll ? ' all' : '') + (band === currentBand ? ' active' : '');
    btn.title = bandDisplay(band);
    btn.dataset.band = band;

    if (isAll) {
        btn.textContent = 'ALL';
    } else {
        const ring = makeRingSvg();
        btn.appendChild(ring);

        const img = document.createElement('img');
        img.src = bandIcon(band);
        img.alt = bandDisplay(band);
        img.className = 'band-btn-icon';
        // 아이콘 로드 실패 시: img만 교체(링 span은 보존)
        img.onerror = () => {
            img.remove();
            const txt = document.createElement('span');
            txt.className = 'band-btn-fallback';
            txt.textContent = bandDisplay(band).slice(0, 4);
            btn.appendChild(txt);
        };
        btn.appendChild(img);

        applyBandRing(ring, band);
    }

    btn.addEventListener('click', () => selectBand(band));
    return btn;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

/** 진행률 링 SVG(트랙 원 + 채움 원). 벡터 stroke라 둘레가 항상 AA → 계단현상 없음.
 *  채움량(--ring-pct)·색 버킷은 applyBandRing이 설정. pathLength=100이라 pct가 곧 길이. */
function makeRingSvg() {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'band-ring');
    svg.setAttribute('viewBox', '0 0 36 36');
    svg.setAttribute('aria-hidden', 'true');
    ['ring-track', 'ring-fill'].forEach(cls => {
        const c = document.createElementNS(SVG_NS, 'circle');
        c.setAttribute('class', cls);
        c.setAttribute('cx', '18');
        c.setAttribute('cy', '18');
        c.setAttribute('r', '16');
        if (cls === 'ring-fill') c.setAttribute('pathLength', '100');
        svg.appendChild(c);
    });
    return svg;
}

/** 밴드 진행률 링 갱신: 평가율(ranked/total)을 채움 비율·색 버킷에 반영.
 *  0~30% Red(low) / 31~69% Yellow(mid) / 70%~ Green(high). */
function applyBandRing(ring, band) {
    const { ranked, total } = C.countRanked(dedupedByBand[band] || [], ranks);
    const pct = total ? (ranked / total * 100) : 0;
    ring.style.setProperty('--ring-pct', pct.toFixed(1));
    ring.classList.remove('low', 'mid', 'high');
    ring.classList.add(pct >= 70 ? 'high' : pct >= 31 ? 'mid' : 'low');
}

/** 셀렉터를 다시 그리지 않고(아이콘 리로드 방지) 링만 갱신 — 랭크 변경 시 호출. */
function updateBandRings() {
    document.querySelectorAll('#band-selector .band-ring').forEach(ring => {
        const band = ring.parentElement.dataset.band;
        if (band) applyBandRing(ring, band);
    });
}

function selectBand(band) {
    currentBand = band;
    document.querySelectorAll('.band-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.band === band);
    });
    document.getElementById('band-label').textContent = bandDisplay(band);
    document.getElementById('hist-band-name').textContent =
        (band === 'ALL' ? '전체' : bandDisplay(band)) + ' 랭크 분포';
    renderSongList();
    renderHistogram();
    if (currentTab === 'band') renderWordcloud();
}

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
        titleEl.textContent = song.title;
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
}

function songFromRow(row) {
    const band = row.dataset.band;
    const title = row.dataset.title;
    const arr = dedupedByBand[band] || [];
    return arr.find(s => s.title === title) || { band, title, url: row.dataset.url };
}

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

// ───────────────────────────
// 10. YouTube (C)
// ───────────────────────────

let player = null;

function onYouTubeIframeAPIReady() {
    initYouTubePlayer();
}
window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;

function initYouTubePlayer() {
    if (player && typeof player.loadVideoById === 'function') return;
    if (!window.YT || !window.YT.Player) return;
    player = new YT.Player('youtube-player', {
        height: '100%',
        width: '100%',
        playerVars: { autoplay: 0, modestbranding: 1, rel: 0, controls: 1 },
    });
}

function playSong(song) {
    const videoId = C.extractVideoId(song.url);
    if (!videoId) {
        showNowPlaying(song.title + ' — 유튜브 링크가 없어요', true);
        return;
    }
    nowPlaying = C.songKey(song.band, song.title);
    highlightPlaying();
    document.getElementById('yt-placeholder').hidden = true;
    showNowPlaying(song.title, false);

    if (!player || typeof player.loadVideoById !== 'function') {
        let waited = 0;
        const iv = setInterval(() => {
            waited += 150;
            if (player && typeof player.loadVideoById === 'function') {
                clearInterval(iv);
                player.loadVideoById(videoId);
            } else if (waited >= 3000) {
                clearInterval(iv);
                showNowPlaying('플레이어 준비 중… 다시 시도해 주세요', true);
            }
        }, 150);
        return;
    }
    player.loadVideoById(videoId);
}

function showNowPlaying(text, muted) {
    const bar = document.getElementById('yt-now-playing');
    bar.hidden = false;
    bar.classList.toggle('muted', !!muted);
    document.getElementById('yt-song-name').textContent = text;
}

/** 현재 재생 곡(nowPlaying) 행만 .playing 갱신 — 리스트 재렌더 없이(스크롤 유지). */
function highlightPlaying() {
    document.querySelectorAll('#song-list .song-item.playing')
        .forEach(el => el.classList.remove('playing'));
    if (!nowPlaying) return;
    document.querySelectorAll('#song-list .song-item').forEach(row => {
        if (C.songKey(row.dataset.band, row.dataset.title) === nowPlaying) {
            row.classList.add('playing');
        }
    });
}

// ───────────────────────────
// 11. Histogram (D)
// ───────────────────────────

function renderHistogram() {
    const counts = C.computeHistogram(bandSongs(), ranks);
    const max = Math.max(1, ...C.TIERS.map(t => counts[t.key]));
    const rows = document.getElementById('hist-rows');
    rows.innerHTML = '';

    C.TIERS.forEach(t => {
        const n = counts[t.key];
        const row = document.createElement('div');
        row.className = 'hist-row';

        const label = document.createElement('span');
        label.className = 'hist-label';
        label.style.color = t.color;
        label.textContent = t.label;

        const barBg = document.createElement('div');
        barBg.className = 'hist-bar-bg';
        const bar = document.createElement('div');
        bar.className = 'hist-bar';
        bar.style.background = t.color;
        bar.style.width = (n / max * 100) + '%';

        const count = document.createElement('span');
        count.className = 'hist-count';
        count.textContent = n;

        barBg.appendChild(bar);
        row.appendChild(label);
        row.appendChild(barBg);
        row.appendChild(count);
        rows.appendChild(row);
    });
}

// ───────────────────────────
// 12. Heatmap (E)
// ───────────────────────────

function renderHeatmap() {
    const grid = document.getElementById('heatmap-grid');
    const matrix = C.computeHeatmap(dedupedByBand, ranks);

    let globalMax = 1;
    bands.forEach(b => C.TIERS.forEach(t => {
        if (matrix[b][t.key] > globalMax) globalMax = matrix[b][t.key];
    }));

    grid.innerHTML = '';

    // 헤더: 빈칸 + 티어 라벨
    const corner = document.createElement('div');
    corner.className = 'hm-head';
    grid.appendChild(corner);
    C.TIERS.forEach(t => {
        const h = document.createElement('div');
        h.className = 'hm-head';
        h.style.color = t.color;
        h.textContent = t.label;
        grid.appendChild(h);
    });

    // 밴드 행 (좌측 셀렉터와 동일 순서)
    bandsInSelectorOrder().forEach(b => {
        const bandCell = document.createElement('div');
        bandCell.className = 'hm-band';
        bandCell.title = bandDisplay(b);
        const icon = document.createElement('img');
        icon.src = bandIcon(b);
        icon.alt = bandDisplay(b);
        icon.className = 'hm-band-icon';
        icon.onerror = () => { bandCell.textContent = bandDisplay(b).slice(0, 4); };
        bandCell.appendChild(icon);
        grid.appendChild(bandCell);

        C.TIERS.forEach(t => {
            const n = matrix[b][t.key];
            const cell = document.createElement('div');
            cell.className = 'hm-cell';
            cell.textContent = n > 0 ? n : '';
            if (n > 0) {
                const alpha = 0.18 + 0.82 * (n / globalMax);
                cell.style.background = hexToRgba(t.color, alpha);
                cell.style.color = alpha > 0.55 ? '#0e0e14' : t.color;
            }
            grid.appendChild(cell);
        });
    });
}

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

// ───────────────────────────
// 14. Share: 링크 복사 / Download
// ───────────────────────────

function copyLinks() {
    const text = C.buildShareLinks(viewSongs(), comments);
    const btn = document.getElementById('copy-btn');
    const done = (ok) => {
        const orig = btn.innerHTML;
        btn.innerHTML = ok ? '✓ 복사됨' : '복사 실패';
        setTimeout(() => { btn.innerHTML = orig; }, 1500);
    };
    if (!text) { done(false); return; }

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => done(true)).catch(() => fallbackCopy(text, done));
    } else {
        fallbackCopy(text, done);
    }
}

function fallbackCopy(text, done) {
    try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        done(ok);
    } catch (_) {
        done(false);
    }
}

/** Download: 전 밴드 히스토그램 + 히트맵을 오프스크린에 합성 후 PNG 캡처 */
function exportRanking() {
    if (!window.domtoimage) {
        alert('이미지 라이브러리 로드 실패. 잠시 후 다시 시도해 주세요.');
        return;
    }
    const area = document.getElementById('capture-area');
    area.innerHTML = '';
    area.appendChild(buildCaptureDOM());

    const node = area.firstChild;
    const imgs = Array.from(node.querySelectorAll('img'));
    const loads = imgs.map(img =>
        img.complete ? Promise.resolve() :
        new Promise(r => { img.onload = r; img.onerror = r; })
    );

    const scale = 2;
    Promise.all(loads).then(() =>
        domtoimage.toPng(node, {
            bgcolor: '#0e0e14',
            width: node.offsetWidth * scale,
            height: node.offsetHeight * scale,
            style: { transform: `scale(${scale})`, transformOrigin: 'top left' },
        })
    )
        .then(dataUrl => {
            const link = document.createElement('a');
            link.download = `bandori-ranking-${Date.now()}.png`;
            link.href = dataUrl;
            link.click();
        })
        .catch((e) => {
            // file:// 로 열면 이미지 인라인용 XHR이 CORS로 차단됨 → http(s)에서만 동작
            console.error('[download] 이미지 생성 실패:', e);
            alert('이미지 생성에 실패했어요.');
        })
        .finally(() => { area.innerHTML = ''; });
}

/** 신뢰도 막대 투명도 — 연속값 대신 3단계 카테고리(유령/희미/불투명).
 *  투명도는 수치로 안 보이므로 구간화가 직관적. 기준은 w(n)=core.confidence. */
function confidenceAlpha(n) {
    const w = C.confidence(n);
    if (w >= 0.9) return 1.0;   // 불투명: n≳9 (거의 다 평가)
    if (w >= 0.5) return 0.6;   // 희미: n≳3 (부분 평가)
    return 0.15;                // 유령: n≤2 (거의 안 평가)
}

/** 최애(최고 스코어) 밴드 — 산출식은 core.bandScores 참조(docs/comments/ux-02-ex1.md).
 *  various_artists(여러 아티스트 묶음)는 최애 밴드 개념이 없어 1위 후보에서 제외(score/막대 미표시와 일관). */
function findBestBand() {
    const candidates = {};
    Object.keys(dedupedByBand).forEach(b => {
        if (b !== 'various_artists') candidates[b] = dedupedByBand[b];
    });
    return C.bestBand(candidates, ranks);
}

function buildCaptureDOM() {
    const matrix = C.computeHeatmap(dedupedByBand, ranks);
    const scores = C.bandScores(dedupedByBand, ranks);
    const root = document.createElement('div');
    root.style.cssText =
        'width:760px;padding:24px;background:#0e0e14;color:#e8e8f0;font-family:Inter,sans-serif;box-sizing:border-box;';

    const title = document.createElement('div');
    const { ranked, total } = C.countRanked(allSongs, ranks);
    title.style.cssText = 'font-size:20px;font-weight:800;margin-bottom:4px;color:#ff6b9d;';
    title.textContent = 'BanG Dream! Song Sorter';
    root.appendChild(title);
    const sub = document.createElement('div');
    sub.style.cssText = 'font-size:12px;color:#7a7a9a;margin-bottom:18px;';
    sub.textContent = `${ranked} / ${total}곡 평가됨`;
    root.appendChild(sub);

    // 밴드별 히스토그램 (2열)
    const histGrid = document.createElement('div');
    histGrid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:14px 20px;margin-bottom:22px;';
    bandsInSelectorOrder().forEach(b => {
        const counts = matrix[b];
        const max = Math.max(1, ...C.TIERS.map(t => counts[t.key]));
        const block = document.createElement('div');
        const isVarious = b === 'various_artists';   // 여러 아티스트 묶음 — 최애 스코어 개념 없음

        // 밴드명(좌, 항상 풀네임) + 최애 스코어(우, 미평가는 '—'; various는 생략)
        const nameRow = document.createElement('div');
        nameRow.style.cssText = 'display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:6px;';
        const nameText = document.createElement('span');
        nameText.style.cssText = 'font-size:12px;font-weight:700;color:#c084fc;white-space:nowrap;flex-shrink:0;';
        nameText.textContent = bandDisplay(b);
        nameRow.appendChild(nameText);
        const sc = scores[b];
        if (!isVarious) {
            // 점수(우측) + 바로 오른쪽 회색 (n/곡수)
            const scoreWrap = document.createElement('span');
            scoreWrap.style.cssText = 'display:flex;align-items:baseline;gap:4px;flex-shrink:0;';
            const scoreText = document.createElement('span');
            scoreText.style.cssText = 'font-size:12px;font-weight:800;color:#ffd06b;';
            scoreText.textContent = (sc && sc.n > 0) ? sc.score.toFixed(2) : '—';
            const countText = document.createElement('span');
            countText.style.cssText = 'font-size:10px;color:#7a7a9a;';
            countText.textContent = (sc && sc.n > 0) ? `(${sc.n}/${(dedupedByBand[b] || []).length})` : '';
            scoreWrap.appendChild(scoreText);
            scoreWrap.appendChild(countText);
            nameRow.appendChild(scoreWrap);
        }
        block.appendChild(nameRow);

        // 2채널 신뢰도 막대 — 길이=선호도 max(0,R)/4, 투명도=신뢰도 3단계(유령/희미/불투명) (설계: docs/HANDOFF.md #3)
        // 흐린 막대 = 적게 평가해 불확실 / 짧은 막대 = 덜 선호. 점수·1위 선정엔 영향 없음(설명 전용). various는 생략.
        if (!isVarious) {
            const pref = (sc && sc.n > 0) ? Math.max(0, sc.raw) / 4 : 0;
            const barAlpha = (sc && sc.n > 0) ? confidenceAlpha(sc.n) : 0;
            const track = document.createElement('div');
            track.style.cssText = 'height:4px;background:#1e1e2a;border-radius:2px;overflow:hidden;margin-bottom:7px;';
            const fill = document.createElement('div');
            fill.style.cssText =
                `height:100%;width:${pref * 100}%;background:${hexToRgba('#eaeaf2', barAlpha)};border-radius:2px;`;
            track.appendChild(fill);
            block.appendChild(track);
        }

        C.TIERS.forEach(t => {
            const n = counts[t.key];
            const row = document.createElement('div');
            row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:3px;';
            row.innerHTML =
                `<span style="font-size:10px;width:26px;color:${t.color};font-weight:700;">${t.label}</span>` +
                `<div style="flex:1;height:12px;background:#1e1e2a;border-radius:3px;overflow:hidden;">` +
                `<div style="height:100%;width:${n / max * 100}%;background:${t.color};border-radius:3px;"></div></div>` +
                `<span style="font-size:10px;width:14px;text-align:right;color:#7a7a9a;">${n}</span>`;
            block.appendChild(row);
        });
        histGrid.appendChild(block);
    });

    const bestBand = findBestBand();
    if (bestBand) {
        const photoWrap = document.createElement('div');
        photoWrap.style.cssText = 'position:relative;overflow:hidden;border-radius:6px;min-height:100px;background:#111;';
        const img = document.createElement('img');
        img.src = fixPath('assets/bands/' + bestBand + '.png');
        img.style.cssText = 'width:100%;height:100%;object-fit:cover;object-position:center top;display:block;';
        photoWrap.appendChild(img);
        const blur = document.createElement('div');
        blur.style.cssText = 'position:absolute;bottom:0;left:0;right:0;height:50%;background:linear-gradient(to bottom,transparent,#0e0e14);';
        photoWrap.appendChild(blur);
        histGrid.appendChild(photoWrap);
    }

    root.appendChild(histGrid);

    // 히트맵
    let globalMax = 1;
    bands.forEach(b => C.TIERS.forEach(t => { if (matrix[b][t.key] > globalMax) globalMax = matrix[b][t.key]; }));

    const hmTitle = document.createElement('div');
    hmTitle.style.cssText = 'font-size:13px;font-weight:700;color:#ff6b9d;margin-bottom:8px;';
    hmTitle.textContent = '전체 밴드 히트맵';
    root.appendChild(hmTitle);

    const hm = document.createElement('div');
    hm.style.cssText = 'display:grid;grid-template-columns:90px repeat(5,1fr);gap:3px;';
    const head = ['', ...C.TIERS.map(t => t.label)];
    head.forEach((h, i) => {
        const c = document.createElement('div');
        c.style.cssText = `font-size:10px;font-weight:700;text-align:center;padding:2px;color:${i === 0 ? '#7a7a9a' : C.TIERS[i - 1].color};`;
        c.textContent = h;
        hm.appendChild(c);
    });
    bandsInSelectorOrder().forEach(b => {
        const nameCell = document.createElement('div');
        nameCell.style.cssText = 'font-size:10px;color:#7a7a9a;display:flex;align-items:center;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;';
        nameCell.textContent = bandDisplay(b);
        hm.appendChild(nameCell);
        C.TIERS.forEach(t => {
            const n = matrix[b][t.key];
            const cell = document.createElement('div');
            const alpha = n > 0 ? 0.18 + 0.82 * (n / globalMax) : 0;
            cell.style.cssText =
                `height:20px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;` +
                `background:${n > 0 ? hexToRgba(t.color, alpha) : '#1e1e2a'};color:${alpha > 0.55 ? '#0e0e14' : t.color};`;
            cell.textContent = n > 0 ? n : '';
            hm.appendChild(cell);
        });
    });
    root.appendChild(hm);

    return root;
}

// ───────────────────────────
// 14.5 Band wordcloud (F)
// ───────────────────────────

const WC_PALETTE = ['#c084fc', '#ff6b9d', '#ff9f6b', '#ffd06b', '#6bcfff', '#cfd0ea'];

// 밴드 퍼스널 컬러(HANDOFF #2 확정) — 워드클라우드 키워드 색. ALL은 WC_PALETTE 유지.
const BAND_COLORS = {
    poppin_party: '#ff3377', afterglow: '#ee3344', pastel_palettes: '#33ddaa',
    roselia: '#3344aa', hello_happy_world: '#ffdd00', morfonica: '#33aaff',
    raise_a_suilen: '#33cccc', mygo: '#0088bb', ave_mujica: '#881144',
    mugendai_mutype: '#ff7788', millsage: '#aa22ee', ikka_dump_rock: '#ffaa33',
};

// 투톤 밴드의 보조색(키워드 아랫부분에만 살짝). 미정의 밴드는 단색.
const BAND_SUBCOLORS = {
    mugendai_mutype: '#2288dd',
};

/** 한 밴드 키워드를 표시텍스트(ko‖jp)로 병합 → Map(text → weight 합). 心·気→마음 통합. */
function mergeBandKeywords(keywords) {
    const m = new Map();
    (keywords || []).forEach(k => {
        const text = ((k.ko || k.jp) || '').trim();
        if (text) m.set(text, (m.get(text) || 0) + (k.weight || 1));
    });
    return m;
}

/** 표시텍스트별 문서빈도(등장 밴드 수). TF-IDF 차별성용 — 1회 계산 후 캐시. */
let _wcDocFreq = null;
function wordcloudDocFreq(data) {
    if (_wcDocFreq) return _wcDocFreq;
    const df = new Map();
    for (const b in data) {
        for (const text of mergeBandKeywords(data[b].keywords).keys())
            df.set(text, (df.get(text) || 0) + 1);
    }
    _wcDocFreq = df;
    return df;
}

/** currentBand 키워드 목록.
 *  ALL    = 전 밴드 원빈도 합산(뱅드림 IP 공유 정서).
 *  밴드별 = TF-IDF 차별성(IP 공통어 누르고 밴드 고유어 부각). */
function wordcloudList(band) {
    const data = window.WORDCLOUD_DATA || {};
    if (band === 'ALL') {
        const merged = new Map();
        for (const b in data)
            for (const [t, w] of mergeBandKeywords(data[b].keywords))
                merged.set(t, (merged.get(t) || 0) + w);
        return { list: [...merged.entries()].sort((a, b) => b[1] - a[1]), songCount: 0 };
    }
    if (!data[band]) return { list: [], songCount: 0 };

    const df = wordcloudDocFreq(data);
    const N = Object.keys(data).length;
    const merged = mergeBandKeywords(data[band].keywords);
    const list = [...merged.entries()]
        .map(([t, w]) => [t, w * (Math.log((N + 1) / ((df.get(t) || 1) + 1)) + 1)])
        .sort((a, b) => b[1] - a[1]);
    return { list, songCount: data[band].song_count || 0 };
}

/** currentBand 워드클라우드 렌더. 패널이 보일 때만 동작(숨김 시 캔버스 크기 0). */
function renderWordcloud() {
    const wrap = document.getElementById('wordcloud-wrap');
    const canvas = document.getElementById('wordcloud-canvas');
    const empty = document.getElementById('wc-empty');
    if (!wrap || !canvas) return;

    document.getElementById('bi-band-name').textContent =
        (currentBand === 'ALL' ? '전체' : bandDisplay(currentBand)) + ' 워드클라우드';

    const w = wrap.clientWidth, h = wrap.clientHeight;
    if (w === 0 || h === 0) return;     // 숨김 상태 → 탭 전환 시 재호출됨
    canvas.width = w; canvas.height = h;

    const { list, songCount } = wordcloudList(currentBand);
    const subEl = document.getElementById('bi-sub');

    if (!window.WordCloud || list.length === 0) {
        canvas.getContext('2d').clearRect(0, 0, w, h);
        empty.hidden = false;
        subEl.textContent = '';
        return;
    }
    empty.hidden = true;
    subEl.textContent = (currentBand === 'ALL')
        ? `전 밴드 키워드 ${list.length}개 병합`
        : `조회수 TOP10 가사 ${songCount}곡 · 키워드 ${list.length}개`;

    // 상위 40개만(좁은 패널 가독성) + 후렴 반복 완화를 위해 sqrt로 폰트 압축
    const top = list.slice(0, 40);
    const sq = v => Math.sqrt(v);
    const maxW = sq(top[0][1]), minW = sq(top[top.length - 1][1]);
    const span = Math.max(1e-6, maxW - minW);
    const FMIN = Math.max(15, Math.round(h / 15)), FMAX = Math.round(h / 5);
    const items = top.map(([text, wt]) => {
        const t = (sq(wt) - minW) / span;          // 0..1
        return [text, Math.round(FMIN + t * (FMAX - FMIN))];
    });

    // 밴드별 = 퍼스널 컬러(hue 고정) + 빈도 명도 변주 / ALL = 단어 해시 6색 팔레트
    const baseHsl = currentBand === 'ALL' ? null : hexToHsl(BAND_COLORS[currentBand] || '#c084fc');
    const subHsl = baseHsl && BAND_SUBCOLORS[currentBand]
        ? hexToHsl(BAND_SUBCOLORS[currentBand]) : null;
    const ctx = canvas.getContext('2d');
    // hue 고정·빈도(t)로 명도 변주한 hsl. 저빈도는 가라앉히고 고빈도를 강조(35%~82%).
    const tone = (hsl, t) => `hsl(${hsl.h}, ${Math.max(55, hsl.s)}%, ${35 + 47 * t}%)`;

    window.WordCloud(canvas, {
        list: items,
        weightFactor: 1,                            // size = 위에서 계산한 폰트 px
        fontFamily: "'M PLUS Rounded 1c', 'Inter', sans-serif",
        fontWeight: '700',
        color: (word, weight, fontSize) => {
            if (!baseHsl) {                         // ALL → 단어 해시 6색 팔레트
                let hsh = 0;
                for (let i = 0; i < word.length; i++) hsh = (hsh * 31 + word.charCodeAt(i)) | 0;
                return WC_PALETTE[Math.abs(hsh) % WC_PALETTE.length];
            }
            // 폰트 px(FMIN~FMAX)를 0~1로 → 고빈도일수록 밝고 선명(다크 배경 가독성)
            const t = FMAX > FMIN ? Math.min(1, Math.max(0, (weight - FMIN) / (FMAX - FMIN))) : 1;
            const main = tone(baseHsl, t);
            if (!subHsl) return main;
            // 투톤: textBaseline=middle 기준 위(메인)→아래 끝 ~22%만 보조색 그라데이션
            const size = fontSize || weight;
            const grad = ctx.createLinearGradient(0, -size / 2, 0, size / 2);
            grad.addColorStop(0, main);
            grad.addColorStop(0.78, main);
            grad.addColorStop(1, tone(subHsl, t));
            return grad;
        },
        backgroundColor: 'transparent',
        rotateRatio: 0,                             // 한글 가독성 — 가로 고정
        gridSize: Math.max(8, Math.round(w / 48)),  // 단어 간 여백 확대(과밀 완화)
        drawOutOfBound: false,
        shrinkToFit: true,
        clearCanvas: true,
    });
}

// ───────────────────────────
// 15. Tabs / Reset
// ───────────────────────────

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.getElementById('hist-panel').classList.toggle('active', tab === 'hist');
    document.getElementById('heat-panel').classList.toggle('active', tab === 'heat');
    document.getElementById('band-panel').classList.toggle('active', tab === 'band');
    if (tab === 'band') renderWordcloud();
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

// ───────────────────────────
// 17. Init
// ───────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initData();
    renderBandSelector();
    renderFilterPills();
    renderRankButtons();
    selectBand('ALL');     // 리스트 + 히스토그램 렌더 포함
    renderHeatmap();
    renderProgress();
    renderStatChips();
    switchTab('hist');     // 초기 탭 활성화(패널 표시)
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
    // 워드클라우드는 캔버스 픽셀 기준이라 리사이즈 시 재렌더(밴드 탭 활성 시)
    let wcResizeTimer = null;
    window.addEventListener('resize', () => {
        if (currentTab !== 'band') return;
        clearTimeout(wcResizeTimer);
        wcResizeTimer = setTimeout(renderWordcloud, 180);
    });

    // 이미 YT API가 준비된 경우 직접 초기화 (타이밍 역전 방지)
    if (window.YT && window.YT.Player) initYouTubePlayer();
});
