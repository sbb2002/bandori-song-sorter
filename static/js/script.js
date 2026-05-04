let player;
let timer;

// YouTube IFrame API 초기화
function onYouTubeIframeAPIReady() {
    player = new YT.Player('youtube-player', {
        height: '0', width: '0',
        events: { 'onStateChange': onPlayerStateChange }
    });
}

function loadAndPlay(url, title) {
    const videoId = extractVideoId(url);
    if (videoId) {
        player.loadVideoById(videoId);
        document.getElementById('current-song-title').innerText = title;
        document.getElementById('master-play').innerText = '||';
    }
}

function extractVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length == 11) ? match[2] : null;
}

function togglePlay() {
    const state = player.getPlayerState();
    if (state === 1) { player.pauseVideo(); } else { player.playVideo(); }
}

function pauseVideo() { player.pauseVideo(); }
function stopVideo() { player.stopVideo(); document.getElementById('timeline').value = 0; }

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        document.getElementById('master-play').innerText = '||';
        startTimer();
    } else {
        document.getElementById('master-play').innerText = '▶';
        clearInterval(timer);
    }
}

function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => {
        const curr = player.getCurrentTime();
        const dur = player.getDuration();
        if (dur > 0) {
            const prog = (curr / dur) * 100;
            document.getElementById('timeline').value = prog;
            document.getElementById('time-display').innerText = formatTime(curr) + " / " + formatTime(dur);
        }
    }, 1000);
}

function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return m + ":" + (s < 10 ? "0" + s : s);
}

function seekVideo(val) {
    const dur = player.getDuration();
    player.seekTo(dur * (val / 100), true);
}

function showInfo(el) {
    const d = JSON.parse(el.getAttribute('data-json'));
    const i = document.getElementById('p-img');
    i.src = './' + d.img_url;
    i.style.display = 'block';

    let html = `<b>${d.album_title}</b><br>`;
    d.tracks.forEach(t => {
        html += `<div onclick="loadAndPlay('${t.url}', '${t.name}')">${t.track_number}. ${t.name}</div>`;
    });
    document.getElementById('t-info').innerHTML = html;
}

function exportTier() {
    const area = document.getElementById('tier-capture-area');
    domtoimage.toPng(area, { bgcolor: '#ffffff' }).then(dataUrl => {
        const link = document.createElement('a');
        link.download = `tier-${Date.now()}.png`;
        link.href = dataUrl;
        link.click();
    });
}

function showBand(band) {
    document.querySelectorAll('.band-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.band === band);
    });
    document.querySelectorAll('.band-albums').forEach(panel => {
        panel.style.display = panel.dataset.band === band ? 'grid' : 'none';
    });
    const activePanel = document.querySelector(`.band-albums[data-band="${band}"]`);
    if (activePanel) {
        activePanel.scrollTop = 0;
    }
}

function updateHistogram() {
    const bandButtons = Array.from(document.querySelectorAll('.band-btn'));
    if (!bandButtons.length) return;

    const bands = bandButtons.map(btn => btn.dataset.band);
    const counts = {};

    document.querySelectorAll('#tier-wrapper .tier-row').forEach(row => {
        const tier = row.querySelector('.tier-label')?.textContent.trim();
        if (!tier) return;
        counts[tier] = counts[tier] || {};
        bands.forEach(band => counts[tier][band] = 0);
        row.querySelectorAll('.drop-zone > *').forEach(item => {
            const json = item.getAttribute('data-json');
            if (!json) return;
            try {
                const album = JSON.parse(json);
                const band = album.band || item.dataset.band;
                if (band && counts[tier][band] !== undefined) {
                    counts[tier][band] += 1;
                }
            } catch (e) {
                // ignore malformed item
            }
        });
    });

    let maxCount = 1;
    Object.values(counts).forEach(tierCounts => {
        Object.values(tierCounts).forEach(value => {
            if (value > maxCount) maxCount = value;
        });
    });

    document.querySelectorAll('.bar-cell').forEach(cell => {
        const band = cell.dataset.band;
        const tier = cell.dataset.tier;
        const value = (counts[tier] && counts[tier][band]) || 0;
        const widthPct = maxCount > 0 ? Math.max(10, (value / maxCount) * 100) : 10;
        cell.querySelector('.bar-fill').style.width = `${widthPct}%`;
        cell.querySelector('.bar-label').innerText = value;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.drop-zone').forEach(z => {
        new Sortable(z, {
            group: 'shared',
            animation: 150,
            onAdd: updateHistogram,
            onSort: updateHistogram,
            onRemove: updateHistogram
        });
    });

    document.querySelectorAll('.band-albums').forEach(panel => {
        new Sortable(panel, {
            group: { name: 'shared', pull: 'clone', put: false },
            animation: 150,
            sort: false
        });
    });

    const firstBtn = document.querySelector('.band-btn.active');
    if (firstBtn) {
        showBand(firstBtn.dataset.band);
    }

    updateHistogram();
});