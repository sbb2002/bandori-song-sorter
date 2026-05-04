let player;
let timer;

function onYouTubeIframeAPIReady() {
    player = new YT.Player('youtube-player', {
        height: '0',
        width: '0',
        events: {
            'onStateChange': onPlayerStateChange
        }
    });
}

function loadAndPlay(url, title) {
    const videoId = extractVideoId(url);
    if (videoId) {
        player.loadVideoById(videoId);
        document.getElementById('current-song-title').innerText = title;
    }
}

function extractVideoId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length == 11) ? match[2] : null;
}

function togglePlay() {
    const state = player.getPlayerState();
    if (state === 1) {
        player.pauseVideo();
    } else {
        player.playVideo();
    }
}

function stopVideo() {
    if(player && player.stopVideo) {
        player.stopVideo();
        document.getElementById('timeline').value = 0;
    }
}

function onPlayerStateChange(event) {
    const btn = document.getElementById('master-play');
    if (event.data == YT.PlayerState.PLAYING) {
        btn.innerText = '||';
        startTimer();
    } else {
        btn.innerText = '▶';
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
    
    let html = `<div class="track-info-wrap"><strong>${d.album_title}</strong><div class="track-list">`;
    if (d.tracks && d.tracks.length > 0) {
        d.tracks.forEach(t => {
            html += `<div onclick="loadAndPlay('${t.url}', '${t.name}')">${t.track_number}. ${t.name}</div>`;
        });
    } else {
        html += `<div>트랙 정보가 없습니다.</div>`;
    }
    html += `</div></div>`;
    document.getElementById('t-info').innerHTML = html;
}

function filterBand(bandName, btn) {
    document.querySelectorAll('.band-content').forEach(c => c.classList.remove('active'));
    // 공백을 하이픈으로 치환하여 ID 매칭
    const targetId = 'band-' + bandName.split(' ').join('-');
    const targetEl = document.getElementById(targetId);
    if (targetEl) targetEl.classList.add('active');
    
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
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

// 드래그 앤 드롭 초기화 함수 분리
function initSortable() {
    const zones = document.querySelectorAll('.drop-zone, .band-content');
    zones.forEach(z => {
        // 기존 인스턴스 파괴 후 재설정 (중복 방지)
        if (Sortable.get(z)) {
            Sortable.get(z).destroy();
        }
        
        new Sortable(z, {
            group: 'shared',
            animation: 150,
            fallbackOnBody: true,
            swapThreshold: 0.65,
            ghostClass: 'sortable-ghost',
            onEnd: function (evt) {
                // 드래그 종료 시 앨범 클릭 이벤트 유지 확인용
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initSortable();
});