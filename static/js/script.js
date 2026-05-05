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
    const isExpanded = wrapper.classList.contains('expanded');
    // PC: ◀/▶, 모바일: ▲/▼
    if (window.innerWidth >= 1024) {
        btn.innerText = isExpanded ? '◀' : '▶';
    } else {
        btn.innerText = isExpanded ? '▲' : '▼';
    }
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
    if (!videoId) {
        alert('재생할 수 없는 URL입니다.');
        return;
    }

    // player가 아직 준비 안 됐으면 최대 3초 대기 후 재시도
    if (!player || typeof player.loadVideoById !== 'function') {
        let waited = 0;
        const interval = setInterval(() => {
            waited += 200;
            if (player && typeof player.loadVideoById === 'function') {
                clearInterval(interval);
                player.loadVideoById(videoId);
                const videoTitle = document.getElementById('video-title');
                if (videoTitle) videoTitle.innerText = title;
            } else if (waited >= 3000) {
                clearInterval(interval);
                alert('유튜브 플레이어가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
            }
        }, 200);
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
// 5-1. 모바일 티어 선택 말풍선
// ───────────────────────────

const TIER_LIST = [
    { label: 'S+', color: '#ff7f7f' },
    { label: 'S',  color: '#ff9999' },
    { label: 'A+', color: '#ffbf7f' },
    { label: 'A',  color: '#ffff7f' },
    { label: 'B+', color: '#bfff7f' },
    { label: 'B',  color: '#7fff7f' },
    { label: 'C+', color: '#7fffff' },
    { label: 'C',  color: '#7f7fff' },
    { label: 'D',  color: '#bf7fff' },
    { label: 'F',  color: '#cccccc' },
];

/**
 * 모바일 전용 long press(300ms) → 랭크 셀렉터 말풍선.
 * - contextmenu(길게 눌러 우클릭 메뉴) 비활성화
 * - touchmove / touchend로 취소 처리
 */
function attachLongPress(item) {
    let pressTimer = null;
    let startX = 0;
    let startY = 0;

    // 브라우저 기본 컨텍스트 메뉴 비활성화 (img 태그 포함)
    item.addEventListener('contextmenu', e => e.preventDefault());
    item.querySelector('img')?.addEventListener('contextmenu', e => e.preventDefault());

    item.addEventListener('touchstart', e => {
        if (window.innerWidth >= 1024) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;

        pressTimer = setTimeout(() => {
            pressTimer = null;
            showTierPopup(item);
        }, 350); // Sortable delay(300ms)보다 늦게 발동하여 경쟁 조건 방지
    }, { passive: true });

    // 손가락이 움직이면 (드래그 의도) 타이머 취소
    item.addEventListener('touchmove', e => {
        if (!pressTimer) return;
        const dx = Math.abs(e.touches[0].clientX - startX);
        const dy = Math.abs(e.touches[0].clientY - startY);
        if (dx > 8 || dy > 8) {
            clearTimeout(pressTimer);
            pressTimer = null;
        }
    }, { passive: true });

    item.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
        pressTimer = null;
    });

    item.addEventListener('touchcancel', () => {
        clearTimeout(pressTimer);
        pressTimer = null;
    });
}

function showTierPopup(bankItem) {
    closeTierPopup();

    const json = bankItem.getAttribute('data-json');

    // 바깥 클릭 시 닫는 오버레이
    const overlay = document.createElement('div');
    overlay.id = 'tier-popup-overlay';
    overlay.onclick = closeTierPopup;

    // 말풍선 본체
    const popup = document.createElement('div');
    popup.id = 'tier-popup';

    TIER_LIST.forEach(({ label, color }) => {
        const btn = document.createElement('button');
        btn.className        = 'tier-popup-btn';
        btn.textContent      = label;
        btn.style.background = color;
        btn.onclick = (e) => {
            e.stopPropagation();
            assignToTier(json, label);
            closeTierPopup();
        };
        popup.appendChild(btn);
    });

    document.body.appendChild(overlay);
    document.body.appendChild(popup);

    // bankItem 위 중앙에 배치
    const rect    = bankItem.getBoundingClientRect();
    const scrollY = window.scrollY;

    // 일단 위쪽에 배치 시도
    popup.style.visibility = 'hidden';
    popup.style.top  = '0px';
    popup.style.left = '0px';

    // 렌더링 후 실제 크기 측정
    requestAnimationFrame(() => {
        const popupH = popup.offsetHeight;
        const popupW = popup.offsetWidth;

        let top  = rect.top + scrollY - popupH - 12;
        let left = rect.left + window.scrollX + rect.width / 2 - popupW / 2;

        // 화면 위로 벗어나면 아래에 표시
        if (top < scrollY + 8) {
            top = rect.bottom + scrollY + 12;
            popup.classList.add('popup-below');
        } else {
            popup.classList.remove('popup-below');
        }

        // 좌우 경계 보정
        left = Math.max(8, Math.min(left, window.innerWidth - popupW - 8));

        popup.style.top        = `${top}px`;
        popup.style.left       = `${left}px`;
        popup.style.visibility = 'visible';
    });
}

function closeTierPopup() {
    document.getElementById('tier-popup-overlay')?.remove();
    document.getElementById('tier-popup')?.remove();
}

/**
 * 선택한 티어의 drop-zone에 앨범 등록.
 * 중복 로직은 드래그와 동일하게 처리.
 */
function assignToTier(json, tierLabel) {
    const allRows   = Array.from(document.querySelectorAll('#tier-capture-area .tier-row'));
    const targetRow = allRows.find(row =>
        row.querySelector('.tier-label')?.textContent.trim() === tierLabel
    );
    if (!targetRow) return;
    const targetZone = targetRow.querySelector('.drop-zone');
    if (!targetZone) return;

    // 중복 감지
    const existing = Array.from(
        document.querySelectorAll('.drop-zone > *')
    ).find(el => el.getAttribute('data-json') === json);

    if (existing) {
        const existingZone = existing.closest('.drop-zone');
        if (existingZone === targetZone) return; // 같은 티어 → 무시
        targetZone.appendChild(existing);         // 다른 티어 → 이동
        updateHistogram();
        return;
    }

    // 신규 등록
    const data = JSON.parse(json);

    const item       = document.createElement('div');
    item.className   = 'tier-item';
    item.setAttribute('data-json', json);
    item.dataset.band = data.band || '';

    const img = document.createElement('img');
    img.src   = fixPath(data.img_url);
    img.alt   = data.album_title || '';
    item.appendChild(img);

    const delBtn     = document.createElement('div');
    delBtn.className = 'del-btn';
    delBtn.innerText = '✕';
    delBtn.onclick   = () => { item.remove(); updateHistogram(); };
    item.appendChild(delBtn);

    targetZone.appendChild(item);
    updateHistogram();
}
// ───────────────────────────
// 6. Histogram
// ───────────────────────────

function updateHistogram() {
    const bandButtons = Array.from(document.querySelectorAll('.band-btn'));
    if (!bandButtons.length) return;

    // band-btn의 data-band 속성에서 밴드명 추출 (img 교체 후 textContent 빈값 방지)
    const bands  = bandButtons.map(btn =>
        (btn.dataset.band || '').trim().toLowerCase()
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

    // 전체 최대값 계산 (색상 강도 기준)
    let maxCount = 1;
    Object.values(counts).forEach(tierCounts =>
        Object.values(tierCounts).forEach(v => { if (v > maxCount) maxCount = v; })
    );

    /**
     * 카운트 값을 흰색(0) → 붉은색(max) 사이의 색상으로 변환
     * white: rgb(255,255,255) → red: rgb(180,0,0)
     */
    function heatColor(value) {
        if (value === 0) return { bg: '#ffffff', text: 'transparent' };
        const t  = value / maxCount;           // 0.0 ~ 1.0
        const r  = 255;
        const g  = Math.round(255 * (1 - t));  // 255 → 0
        const b  = Math.round(255 * (1 - t));  // 255 → 0
        // 값이 충분히 크면(t > 0.5) 숫자를 흰색으로, 작으면 어두운색으로
        const textColor = t > 0.5 ? '#ffffff' : '#660000';
        return { bg: `rgb(${r},${g},${b})`, text: textColor };
    }

    document.querySelectorAll('.heatmap-cell').forEach(cell => {
        const band  = cell.dataset.band.toString().trim().toLowerCase();
        const tier  = cell.dataset.tier;
        const value = counts[tier]?.[band] || 0;
        const { bg, text } = heatColor(value);

        cell.style.backgroundColor = bg;
        cell.style.color            = text;
        cell.innerText              = value > 0 ? value : '';
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
            delay: 300,
            delayOnTouchOnly: true,
        });

        // 모바일 long press → 랭크 셀렉터 말풍선
        container.querySelectorAll('.bank-item').forEach(item => {
            attachLongPress(item);
        });
    });

    // 티어 드롭존: 드래그 받기 + 정렬
    document.querySelectorAll('.drop-zone').forEach(zone => {
        new Sortable(zone, {
            group: 'shared',
            animation: 150,
            delay: 300,
            delayOnTouchOnly: true,
            onAdd(e) {
                const item       = e.item;
                const targetZone = e.to;
                const json       = item.getAttribute('data-json');

                // ── 중복 감지 ──────────────────────────────────────────
                // 모든 drop-zone에서 동일한 data-json을 가진 기존 아이템 탐색
                const duplicate = Array.from(
                    document.querySelectorAll('.drop-zone > *')
                ).find(el => el !== item && el.getAttribute('data-json') === json);

                if (duplicate) {
                    const duplicateZone = duplicate.closest('.drop-zone');

                    if (duplicateZone === targetZone) {
                        // 같은 랭크에 이미 존재 → 새로 드래그한 것만 제거
                        item.remove();
                    } else {
                        // 다른 랭크에 존재 → 기존 아이템을 새 랭크로 이동 후 새 것 제거
                        targetZone.appendChild(duplicate);
                        item.remove();
                    }
                    updateHistogram();
                    return;
                }
                // ───────────────────────────────────────────────────────

                item.classList.add('tier-item');
                item.dataset.band = JSON.parse(json).band || '';

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

/**
 * 캡처 전용 히트맵 미러를 #heatmap-capture-grid에 동기화.
 * 실제 히트맵(.heatmap-cell)의 색상/텍스트를 그대로 복사한다.
 */
function syncHeatmapForCapture() {
    const grid = document.getElementById('heatmap-capture-grid');
    if (!grid) return;

    // 헤더 행 구성: 밴드 이름 수집
    const bandButtons = Array.from(document.querySelectorAll('.band-btn'));
    const bandNames   = bandButtons.map(btn => btn.textContent.trim());

    // 실제 히트맵 행 수집
    const rows = Array.from(document.querySelectorAll('.histogram-row[data-tier]'));

    // grid 스타일: tier열 + band열
    const colCount  = bandNames.length + 1;
    grid.style.display            = 'grid';
    grid.style.gridTemplateColumns = `48px repeat(${bandNames.length}, 1fr)`;
    grid.style.gap                = '3px';

    grid.innerHTML = '';

    // 헤더 행
    const tierHead = document.createElement('div');
    tierHead.textContent  = 'Tier';
    tierHead.style.cssText = 'font-size:0.7rem;font-weight:700;color:#aaa;display:flex;align-items:center;justify-content:center;';
    grid.appendChild(tierHead);

    bandNames.forEach(name => {
        const cell = document.createElement('div');
        cell.textContent  = name;
        cell.style.cssText = 'font-size:0.65rem;font-weight:700;color:#aaa;display:flex;align-items:center;justify-content:center;padding:2px;';
        grid.appendChild(cell);
    });

    // 데이터 행: 실제 .heatmap-cell에서 색상 복사
    rows.forEach(row => {
        const tier      = row.dataset.tier;
        const tierLabel = row.querySelector('.histogram-cell');
        const cells     = Array.from(row.querySelectorAll('.heatmap-cell'));

        // 티어 라벨
        const labelCell = document.createElement('div');
        labelCell.textContent  = tier;
        labelCell.style.cssText = `
            background: ${tierLabel ? tierLabel.style.background : '#eee'};
            color: #000;
            font-size: 0.75rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            min-height: 28px;
        `;
        grid.appendChild(labelCell);

        // 히트맵 데이터 셀
        cells.forEach(src => {
            const dst = document.createElement('div');
            dst.style.cssText = `
                background-color: ${src.style.backgroundColor || '#ffffff'};
                color: ${src.style.color || 'transparent'};
                font-size: 0.75rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                min-height: 28px;
            `;
            dst.textContent = src.innerText;
            grid.appendChild(dst);
        });
    });
}

async function exportTier() {
    const area    = document.getElementById('export-capture-area');
    const wrapper = document.getElementById('tier-wrapper');

    wrapper.classList.add('expanded');
    document.body.classList.add('capturing');

    // 히트맵 미러 동기화
    syncHeatmapForCapture();

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