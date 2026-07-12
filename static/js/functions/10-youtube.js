// ===========================================================
// BanG Dream! Song Sorter — 10-youtube.js
// §10 YouTube(C) 플레이어
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 10. YouTube (C)
// ───────────────────────────

let player = null;
let nowPlayingUrl = null;   // onError 폴백('YouTube에서 열기') 링크용 — 현재 재생 곡 원본 URL

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
        // origin: IFrame API 공식 권장(enablejsapi 사용 시 임베드 origin 명시). playsinline: 모바일 인라인 재생.
        playerVars: {
            autoplay: 0, modestbranding: 1, rel: 0, controls: 1,
            playsinline: 1, origin: window.location.origin,
        },
        events: { onError: onPlayerError },
    });
}

// 개별 영상 재생 실패(삭제·비공개·임베드 차단·지역락 등) → 안내 + 'YouTube에서 열기' 폴백 링크.
// ⚠ 환경성 'Playback ID' 오버레이는 보통 이 이벤트를 발화시키지 않음(플레이어 내부 표시).
function onPlayerError(e) {
    console.warn('YouTube 재생 오류', e && e.data, 'url', nowPlayingUrl);
    showNowPlaying('이 영상은 여기서 재생할 수 없어요', true);
    const bar = document.getElementById('yt-now-playing');
    if (!bar || !nowPlayingUrl) return;
    let link = document.getElementById('yt-fallback-link');
    if (!link) {
        link = document.createElement('a');
        link.id = 'yt-fallback-link';
        link.className = 'yt-fallback-link';
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = 'YouTube에서 열기';
        bar.appendChild(link);
    }
    link.href = nowPlayingUrl;
    link.hidden = false;
}

function playSong(song) {
    const videoId = C.extractVideoId(song.url);
    if (!videoId) {
        showNowPlaying(song.title + ' — 유튜브 링크가 없어요', true);
        return;
    }
    nowPlaying = C.songKey(song.band, song.title);
    nowPlayingUrl = song.url;               // onError 폴백 링크 대상 갱신
    const fb = document.getElementById('yt-fallback-link');
    if (fb) fb.hidden = true;               // 새 곡 재생 시 이전 폴백 링크 숨김
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
    if (_clusterChart) _clDraw();      // 지도의 재생 중 곡 강조도 동기화(리스트↔지도)
    if (!nowPlaying) return;
    document.querySelectorAll('#song-list .song-item').forEach(row => {
        if (C.songKey(row.dataset.band, row.dataset.title) === nowPlaying) {
            row.classList.add('playing');
        }
    });
}

