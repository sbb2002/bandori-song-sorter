// ===========================================================
// BanG Dream! Song Sorter — 01-state.js
// §1 State + core(C) 참조 · 최상위 공유 상태
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

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
let ranks = {};    // { songKey: 1..5 }
let comments = {};  // { songKey: '메모 텍스트' }

let currentBand = 'ALL';
let currentType = 'all';         // 곡 종류 탭: 'all' | 'ori' | 'cover'
let activeFilters = new Set();   // 0=미평가, 1..5=티어. 비어있으면 전체 표시
let currentTab = 'hist';
let nowPlaying = null;           // 현재 재생 중(유튜브 프레임에 뜬) 곡의 songKey, 곡 리스트 강조용

