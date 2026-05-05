/* ===========================
   BanG Dream! Album Sorter
   script.js
   =========================== */

// ───────────────────────────
// 1. Path Utilities
// ───────────────────────────

/**
 * GitHub Pages 경로 문제를 해결하는 핵심 함수.
 * 역슬래시 정규화 + 절대경로 → 상대경로 보정.
 */
function fixPath(path) {
    if (!path) return '';
    if (path.startsWith('http') || path.startsWith('data:')) return path;

    let cleanPath = path.replace(/\\/g, '/').trim();
    if (cleanPath.startsWith('/')) cleanPath = cleanPath.substring(1);

    return './' + cleanPath;
}

// ───────────────────────────
// 2. Tier Sidebar Toggle
// ───────────────────────────

function toggleTier() {
    const wrapper = document.getElementById('tier-wrapper');
    const btn     = document.getElementById('toggle-btn');
    wrapper.classList.toggle('expanded');
    btn.innerText = wrapper.classList.contains('expanded') ? '◀' : '▶';
}

// ───────────────────────────
// 3. Band Navigation
// ───────────────────────────

function switchBand(name, btn) {
    document.querySelectorAll('.band-btn').forEach(x => x.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.band-content').forEach(x => x.classList.remove('active'));
    document.getElementById('b-' + name).classList.add('active');
}

// ───────────────────────────
// 4. YouTube Player
// ───────────────────────────

let player;
let timer;

/** YouTube IFrame API 준비 완료 콜백 (전역 함수명 고정) */
function onYouTubeIframeAPIReady() {
    player = new YT.Player('youtube-player', {
        height: '100%',
        width: '100%',
        playerVars: {
            autoplay: 0,
            modestbranding: 1,
            rel: 0,
            controls: 1,
        },
        events: { onStateChange: onPlayerStateChange },
    });
}

/** URL에서 YouTube 비디오 ID 추출 */
function extractVideoId(url) {
    const regExp = /^.*(?:youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match  = url.match(regExp);
    return (match && match[1].length === 11) ? match[1] : null;
}

/** 영상 로드 및 재생 */
function loadAndPlay(url, title) {
    const videoId = extractVideoId(url);
    if (!videoId || !player) {
        alert('재생할 수 없는 URL입니다.');
        return;
    }
    player.loadVideoById(videoId);

    const videoTitle = document.getElementById('video-title');
    if (videoTitle) videoTitle.innerText = title;
}

/** LP 디스크 회전 상태 동기화 */
function updateLPState() {
    const disc = document.getElementById('lp-disc');
    if (!disc || !player) return;

    if (player.getPlayerState() === YT.PlayerState.PLAYING) {
        disc.classList.add('playing');
    } else {
        disc.classList.remove('playing');
    }
}

function togglePlay() {
    if (!player) return;
    if (player.getPlayerState() === YT.PlayerState.PLAYING) {
        player.pauseVideo();
    } else {
        player.playVideo();
    }
}

function pauseVideo() {
    if (player) player.pauseVideo();
    updateLPState();
}

function stopVideo() {
    if (player) player.stopVideo();
    const timeline = document.getElementById('timeline');
    if (timeline) timeline.value = 0;
    updateLPState();
}

function onPlayerStateChange(event) {
    const toggle = document.getElementById('play-toggle');

    if (event.data === YT.PlayerState.PLAYING) {
        if (toggle) toggle.innerText = '||';
        startTimer();
    } else {
        if (toggle) toggle.innerText = '▶';
        clearInterval(timer);
    }
    updateLPState();
}

function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => {
        if (!player) return;
        const curr = player.getCurrentTime();
        const dur  = player.getDuration();
        if (dur > 0) {
            const prog        = (curr / dur) * 100;
            const timeline    = document.getElementById('timeline');
            const timeDisplay = document.getElementById('time-display');
            if (timeline)    timeline.value       = prog;
            if (timeDisplay) timeDisplay.innerText = `${formatTime(curr)} / ${formatTime(dur)}`;
        }
    }, 1000);
}

function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' + s : s}`;
}

function seekVideo(val) {
    if (!player) return;
    player.seekTo(player.getDuration() * (val / 100), true);
}

// ───────────────────────────
// 5. Album Info Panel
// ───────────────────────────

function showInfo(el) {
    const data = JSON.parse(el.getAttribute('data-json'));

    // 앨범 커버
    const img       = document.getElementById('p-img');
    img.src         = fixPath(data.img_url);
    img.style.display = 'block';

    // 제목
    const titleEl = document.querySelector('.preview-title');
    if (titleEl) titleEl.textContent = data.album_title;

    // 비디오 패널 초기화
    const videoTitle = document.getElementById('video-title');
    if (videoTitle) videoTitle.innerText = '트랙을 선택하면 유튜브 영상이 표시됩니다.';

    // 트랙 목록 렌더링
    const tinfo     = document.getElementById('t-info');
    tinfo.innerHTML = '';

    const list      = document.createElement('div');
    list.className  = 'track-list';

    (data.tracks || []).forEach(track => {
        const item       = document.createElement('div');
        item.className   = 'track-item';
        item.textContent = `${track.track_number}. ${track.name}`;

        if (track.url && track.url !== '-' && extractVideoId(track.url)) {
            item.classList.add('playable');
            item.onclick = () => loadAndPlay(track.url, `${track.track_number}. ${track.name}`);
        } else {
            item.classList.add('disabled');
        }

        list.appendChild(item);
    });

    tinfo.appendChild(list);
}

// ───────────────────────────
// 6. Histogram
// ───────────────────────────

function updateHistogram() {
    const bandButtons = Array.from(document.querySelectorAll('.band-btn'));
    if (!bandButtons.length) return;

    // band-btn 텍스트 → 데이터 키 형식으로 정규화
    const bands  = bandButtons.map(btn =>
        btn.textContent.trim().toLowerCase().replace(/\s+/g, '_')
    );
    const counts = {};

    document.querySelectorAll('#tier-wrapper .tier-row').forEach(row => {
        const tier = row.querySelector('.tier-label')?.textContent.trim();
        if (!tier) return;

        counts[tier] = counts[tier] || {};
        bands.forEach(band => { counts[tier][band] = 0; });

        row.querySelectorAll('.drop-zone > *').forEach(item => {
            const json = item.getAttribute('data-json');
            if (!json) return;
            try {
                const album = JSON.parse(json);
                const band  = (album.band || '').toString().trim().toLowerCase();
                if (band && counts[tier][band] !== undefined) {
                    counts[tier][band] += 1;
                }
            } catch (_) { /* malformed — skip */ }
        });
    });

    // 최대값 계산 (bar width 비율용)
    let maxCount = 1;
    Object.values(counts).forEach(tierCounts =>
        Object.values(tierCounts).forEach(v => { if (v > maxCount) maxCount = v; })
    );

    document.querySelectorAll('.bar-cell').forEach(cell => {
        const band     = cell.dataset.band.toString().trim().toLowerCase();
        const tier     = cell.dataset.tier;
        const value    = counts[tier]?.[band] || 0;
        const widthPct = Math.max(10, (value / maxCount) * 100);

        cell.querySelector('.bar-fill').style.width = `${widthPct}%`;
        cell.querySelector('.bar-label').innerText  = value;
    });
}

// ───────────────────────────
// 7. Drag-and-Drop (Sortable)
// ───────────────────────────

function initSortable() {
    // 앨범 뱅크: 클론 드래그 (원본 유지)
    document.querySelectorAll('.band-content').forEach(container => {
        new Sortable(container, {
            group: { name: 'shared', pull: 'clone', put: false },
            animation: 150,
            sort: false,
        });
    });

    // 티어 드롭존: 드래그 받기 + 정렬
    document.querySelectorAll('.drop-zone').forEach(zone => {
        new Sortable(zone, {
            group: 'shared',
            animation: 150,
            onAdd(e) {
                const item    = e.item;
                item.classList.add('tier-item');
                item.dataset.band = JSON.parse(item.getAttribute('data-json')).band || '';

                // 삭제 버튼 (중복 방지)
                if (!item.querySelector('.del-btn')) {
                    const delBtn     = document.createElement('div');
                    delBtn.className = 'del-btn';
                    delBtn.innerText = '✕';
                    delBtn.onclick   = () => { item.remove(); updateHistogram(); };
                    item.appendChild(delBtn);
                }

                // 이미지 경로 보정
                const img = item.querySelector('img');
                if (img) img.src = fixPath(img.getAttribute('src') || img.getAttribute('data-src'));

                updateHistogram();
            },
            onRemove: updateHistogram,
            onSort:   updateHistogram,
        });
    });
}

// ───────────────────────────
// 8. Export (PNG)
// ───────────────────────────

async function exportTier() {
    const area    = document.getElementById('tier-capture-area');
    const wrapper = document.getElementById('tier-wrapper');

    wrapper.classList.add('expanded');
    document.body.classList.add('capturing');

    await new Promise(r => setTimeout(r, 600));

    domtoimage.toPng(area, { bgcolor: '#ffffff' })
        .then(dataUrl => {
            const link    = document.createElement('a');
            link.download = `tier-${Date.now()}.png`;
            link.href     = dataUrl;
            link.click();
        })
        .finally(() => {
            document.body.classList.remove('capturing');
            wrapper.classList.remove('expanded');
        });
}

// ───────────────────────────
// 9. Initialisation
// ───────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // lazy-load 이미지 경로 보정
    document.querySelectorAll('.lazy-load').forEach(img => {
        img.src = fixPath(img.getAttribute('data-src'));
    });

    initSortable();
    updateHistogram();
});