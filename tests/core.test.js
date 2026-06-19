'use strict';

const test = require('node:test');
const assert = require('node:assert');
const C = require('../static/js/core.js');

const YT1 = 'https://youtu.be/abcdefghijk';      // 유효 (11자)
const YT2 = 'https://youtu.be/zyxwvutsrqp';      // 유효
const YT3 = 'https://www.youtube.com/watch?v=ABCDEFGHIJK';

// ───────────────────────────
// extractVideoId / isPlayable
// ───────────────────────────
test('extractVideoId: 다양한 형식에서 11자리 ID 추출', () => {
  assert.strictEqual(C.extractVideoId(YT1), 'abcdefghijk');
  assert.strictEqual(C.extractVideoId(YT3), 'ABCDEFGHIJK');
  assert.strictEqual(C.extractVideoId('https://youtu.be/abc?si=xyz'), null); // 11자 아님
  assert.strictEqual(C.extractVideoId('-'), null);
  assert.strictEqual(C.extractVideoId(''), null);
  assert.strictEqual(C.extractVideoId(null), null);
});

test('isPlayable: 유효 URL만 true', () => {
  assert.strictEqual(C.isPlayable(YT1), true);
  assert.strictEqual(C.isPlayable('-'), false);
  assert.strictEqual(C.isPlayable(''), false);
});

// ───────────────────────────
// normalizeTitle / songKey
// ───────────────────────────
test('normalizeTitle: trim + lowercase', () => {
  assert.strictEqual(C.normalizeTitle('  Made My Day '), 'made my day');
  assert.strictEqual(C.normalizeTitle('XYZ'), 'xyz');
});

test('songKey: band::title 형식', () => {
  assert.strictEqual(C.songKey('mygo', '迷星叫'), 'mygo::迷星叫');
});

// ───────────────────────────
// dedupSongs
// ───────────────────────────
test('dedupSongs: 밴드 내 제목 중복 제거(대소문자/공백 무시)', () => {
  const out = C.dedupSongs([
    { band: 'a', title: 'Song', url: YT1 },
    { band: 'a', title: ' song ', url: YT2 },  // 중복
    { band: 'a', title: 'Other', url: YT2 },
  ]);
  assert.strictEqual(out.length, 2);
  assert.strictEqual(out[0].title, 'Song');     // 첫 등장 대표 유지
  assert.strictEqual(out[1].title, 'Other');
});

test('dedupSongs: 다른 밴드의 동일 제목은 유지', () => {
  const out = C.dedupSongs([
    { band: 'a', title: 'Same', url: YT1 },
    { band: 'b', title: 'Same', url: YT1 },
  ]);
  assert.strictEqual(out.length, 2);
});

test('dedupSongs: 대표가 재생불가면 중복의 유효 URL로 보강', () => {
  const out = C.dedupSongs([
    { band: 'a', title: 'X', url: '-' },        // 대표(재생불가)
    { band: 'a', title: 'X', url: YT1 },        // 보강원
  ]);
  assert.strictEqual(out.length, 1);
  assert.strictEqual(out[0].url, YT1);
});

test('dedupSongs: 입력 배열/객체를 변형하지 않음', () => {
  const input = [{ band: 'a', title: 'X', url: '-' }, { band: 'a', title: 'X', url: YT1 }];
  C.dedupSongs(input);
  assert.strictEqual(input[0].url, '-');         // 원본 유지
});

// ───────────────────────────
// computeHistogram
// ───────────────────────────
test('computeHistogram: 티어별 카운트 집계', () => {
  const songs = [
    { band: 'a', title: 'A' },
    { band: 'a', title: 'B' },
    { band: 'a', title: 'C' },
    { band: 'a', title: 'D' },
  ];
  const ranks = { 'a::A': 1, 'a::B': 1, 'a::C': 3 };  // D 미평가
  assert.deepStrictEqual(C.computeHistogram(songs, ranks), { 1: 2, 2: 0, 3: 1, 4: 0, 5: 0 });
});

test('computeHistogram: 빈 입력/ranks 안전', () => {
  assert.deepStrictEqual(C.computeHistogram([], {}), { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 });
  assert.deepStrictEqual(C.computeHistogram(null, null), { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 });
});

test('computeHistogram: 잘못된 티어 값은 무시', () => {
  const songs = [{ band: 'a', title: 'A' }, { band: 'a', title: 'B' }];
  const ranks = { 'a::A': 9, 'a::B': 0 };
  assert.deepStrictEqual(C.computeHistogram(songs, ranks), { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 });
});

// ───────────────────────────
// computeHeatmap
// ───────────────────────────
test('computeHeatmap: 밴드 × 티어 매트릭스', () => {
  const songsByBand = {
    a: [{ band: 'a', title: 'A' }, { band: 'a', title: 'B' }],
    b: [{ band: 'b', title: 'C' }],
  };
  const ranks = { 'a::A': 1, 'a::B': 5, 'b::C': 1 };
  const m = C.computeHeatmap(songsByBand, ranks);
  assert.deepStrictEqual(m.a, { 1: 1, 2: 0, 3: 0, 4: 0, 5: 1 });
  assert.deepStrictEqual(m.b, { 1: 1, 2: 0, 3: 0, 4: 0, 5: 0 });
});

// ───────────────────────────
// countRanked
// ───────────────────────────
test('countRanked: 평가/전체', () => {
  const songs = [{ band: 'a', title: 'A' }, { band: 'a', title: 'B' }, { band: 'a', title: 'C' }];
  assert.deepStrictEqual(C.countRanked(songs, { 'a::A': 2 }), { ranked: 1, total: 3 });
  assert.deepStrictEqual(C.countRanked(songs, {}), { ranked: 0, total: 3 });
});

// ───────────────────────────
// buildShareLinks
// ───────────────────────────
test('buildShareLinks: 유효 URL만, 빈 줄 한 줄로 구분', () => {
  const songs = [
    { url: YT1 },
    { url: '-' },        // 제외
    { url: '' },         // 제외
    { url: YT2 },
  ];
  assert.strictEqual(C.buildShareLinks(songs), YT1 + '\n\n' + YT2);
});

test('buildShareLinks: 유효 링크 없으면 빈 문자열', () => {
  assert.strictEqual(C.buildShareLinks([{ url: '-' }, { url: '' }]), '');
  assert.strictEqual(C.buildShareLinks([]), '');
});

// ───────────────────────────
// TIERS 무결성
// ───────────────────────────
test('TIERS: 5단계, key 1..5', () => {
  assert.strictEqual(C.TIERS.length, 5);
  assert.deepStrictEqual(C.TIERS.map(t => t.key), [1, 2, 3, 4, 5]);
  assert.deepStrictEqual(C.TIERS.map(t => t.label), ['최애', '차애', '호', '중간', '불호']);
});
