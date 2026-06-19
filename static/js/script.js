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

const BAND_ORDER = [
    'poppin_party', 'roselia', 'afterglow', 'pastel_palettes',
    'hello_happy_world', 'raise_a_suilen', 'morfonica', 'mygo',
    'ave_mujica', 'mugendai_mutype', 'millsage', 'ikka_dumb_rock'
];

let dedupedByBand = {};     // band -> 중복 제거된 곡 배열
let allSongs = [];          // 전 밴드 평탄화(밴드 순서)
let bands = [];             // 밴드 순서
let ranks = loadRanks();    // { songKey: 1..5 }

let currentBand = 'ALL';
let activeFilters = new Set();   // 0=미평가, 1..5=티어. 비어있으면 전체 표시
let currentTab = 'hist';

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
    return fixPath('assets/icon/' + band + '.png');
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

/** 리스트 표시용 곡 — 밴드 + 활성 티어 필터 적용 */
function viewSongs() {
    let songs = bandSongs();
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

function renderBandSelector() {
    const el = document.getElementById('band-selector');
    el.innerHTML = '';

    el.appendChild(makeBandBtn('ALL', true));

    const divider = document.createElement('div');
    divider.className = 'band-divider';
    el.appendChild(divider);

    const ordered = BAND_ORDER.filter(b => bands.includes(b));
    const rest = bands.filter(b => !BAND_ORDER.includes(b));
    [...ordered, ...rest].forEach(b => el.appendChild(makeBandBtn(b, false)));
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
        const img = document.createElement('img');
        img.src = bandIcon(band);
        img.alt = bandDisplay(band);
        img.className = 'band-btn-icon';
        img.onerror = () => { btn.textContent = bandDisplay(band).slice(0, 4); };
        btn.appendChild(img);
    }

    btn.addEventListener('click', () => selectBand(band));
    return btn;
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
    const songs = viewSongs();
    const frag = document.createDocumentFragment();

    if (songs.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'song-empty';
        empty.textContent = activeFilters.size > 0 ? '해당 조건의 곡이 없어요.' : '곡이 없어요.';
        frag.appendChild(empty);
    }

    songs.forEach((song, i) => {
        const r = getRank(song);
        const showBand = (currentBand === 'ALL');

        const row = document.createElement('div');
        row.className = 'song-item' + (C.isRank(r) ? ' ranked' : '');
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
let longFired = false;
let moved = false;
let rafId = null;

function startProgress(row) {
    const start = performance.now();
    row.style.setProperty('--lp', 0);
    function tick(now) {
        const p = Math.min((now - start) / LONG_PRESS_MS, 1);
        row.style.setProperty('--lp', p);
        if (p < 1) rafId = requestAnimationFrame(tick);
    }
    rafId = requestAnimationFrame(tick);
}

function cancelPress() {
    if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (pressRow) {
        pressRow.classList.remove('pressing');
        pressRow.style.removeProperty('--lp');
    }
    pressRow = null;
}

function initPressHandlers() {
    const list = document.getElementById('song-list');

    list.addEventListener('pointerdown', e => {
        const row = e.target.closest('.song-item');
        if (!row) return;
        if (e.pointerType === 'mouse' && e.button !== 0) return; // 우클릭은 contextmenu가 처리
        pressRow = row;
        pressStartX = e.clientX;
        pressStartY = e.clientY;
        longFired = false;
        moved = false;
        row.classList.add('pressing');
        startProgress(row);
        pressTimer = setTimeout(() => {
            longFired = true;
            const r = pressRow;
            cancelPress();
            openPopup(songFromRow(r));
        }, LONG_PRESS_MS);
    });

    list.addEventListener('pointermove', e => {
        if (!pressRow) return;
        if (Math.abs(e.clientX - pressStartX) > MOVE_TOLERANCE ||
            Math.abs(e.clientY - pressStartY) > MOVE_TOLERANCE) {
            moved = true;
            cancelPress();
        }
    });

    list.addEventListener('pointerup', e => {
        if (!pressRow) return;
        const row = pressRow;
        const fired = longFired;
        const mv = moved;
        cancelPress();
        if (!fired && !mv) playSong(songFromRow(row));
    });

    list.addEventListener('pointerleave', cancelPress);

    // 데스크톱 우클릭 = 랭크 팝업 (+ 모바일 길게눌러 뜨는 기본 메뉴 차단)
    list.addEventListener('contextmenu', e => {
        const row = e.target.closest('.song-item');
        if (!row) return;
        e.preventDefault();
        cancelPress();
        openPopup(songFromRow(row));
    });
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
        btn.addEventListener('click', () => {
            if (popupSong) {
                const cur = getRank(popupSong);
                // 같은 티어 다시 누르면 해제(토글), 아니면 설정
                setRank(popupSong, cur === t.key ? null : t.key);
                refreshAll();
            }
            closePopup();
        });
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
    const popup = document.getElementById('popup');
    popup.hidden = false;
    requestAnimationFrame(() => popup.classList.add('open'));
}

function closePopup() {
    const popup = document.getElementById('popup');
    popup.classList.remove('open');
    popupSong = null;
    setTimeout(() => { popup.hidden = true; }, 200);
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

    // 밴드 행
    bands.forEach(b => {
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
    const text = C.buildShareLinks(viewSongs());
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
    const area = document.getElementById('capture-area');
    area.innerHTML = '';
    area.appendChild(buildCaptureDOM());

    const node = area.firstChild;
    if (!window.domtoimage) {
        alert('이미지 라이브러리 로드 실패. 잠시 후 다시 시도해 주세요.');
        return;
    }
    domtoimage.toPng(node, { bgcolor: '#0e0e14', width: node.offsetWidth, height: node.offsetHeight })
        .then(dataUrl => {
            const link = document.createElement('a');
            link.download = `bandori-ranking-${Date.now()}.png`;
            link.href = dataUrl;
            link.click();
        })
        .catch(() => alert('이미지 생성에 실패했어요.'))
        .finally(() => { area.innerHTML = ''; });
}

function findBestBand() {
    const matrix = C.computeHeatmap(dedupedByBand, ranks);
    const scored = bands.map(b => {
        const counts = matrix[b];
        const total = C.TIERS.reduce((s, t) => s + counts[t.key], 0);
        if (total === 0) return null;
        return { band: b, r1: counts[1]/total, r2: counts[2]/total, r3: counts[3]/total, r5: counts[5]/total };
    }).filter(Boolean);
    if (!scored.length) return null;
    scored.sort((a, b) =>
        b.r1 !== a.r1 ? b.r1 - a.r1 :
        b.r2 !== a.r2 ? b.r2 - a.r2 :
        b.r3 !== a.r3 ? b.r3 - a.r3 :
        a.r5 - b.r5
    );
    return scored[0].band;
}

function buildCaptureDOM() {
    const matrix = C.computeHeatmap(dedupedByBand, ranks);
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
    bands.forEach(b => {
        const counts = matrix[b];
        const max = Math.max(1, ...C.TIERS.map(t => counts[t.key]));
        const block = document.createElement('div');

        const name = document.createElement('div');
        name.style.cssText = 'font-size:12px;font-weight:700;color:#c084fc;margin-bottom:6px;';
        name.textContent = bandDisplay(b);
        block.appendChild(name);

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
        img.src = fixPath('assets/' + bestBand + '/band.png');
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
    bands.forEach(b => {
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
// 15. Tabs / Reset
// ───────────────────────────

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.getElementById('hist-panel').classList.toggle('active', tab === 'hist');
    document.getElementById('heat-panel').classList.toggle('active', tab === 'heat');
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
    document.getElementById('popup').addEventListener('click', e => {
        if (e.target.id === 'popup') closePopup();
    });
    document.querySelectorAll('.tab-btn').forEach(b =>
        b.addEventListener('click', () => switchTab(b.dataset.tab)));

    // 이미 YT API가 준비된 경우 직접 초기화 (타이밍 역전 방지)
    if (window.YT && window.YT.Player) initYouTubePlayer();
});
