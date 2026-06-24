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

test('buildShareLinks: 코멘트 있으면 URL 다음 줄에 추가(곡 사이 빈 줄)', () => {
  const songs = [
    { band: 'a', title: 'A', url: YT1 },
    { band: 'a', title: 'B', url: YT2 },   // 코멘트 없음 → URL만
  ];
  const comments = { 'a::A': '최고의 곡' };
  assert.strictEqual(
    C.buildShareLinks(songs, comments),
    YT1 + '\n최고의 곡' + '\n\n' + YT2
  );
});

test('buildShareLinks: 코멘트 공백/없음은 URL만, comments 인자 생략도 하위호환', () => {
  const songs = [{ band: 'a', title: 'A', url: YT1 }, { band: 'a', title: 'B', url: YT2 }];
  assert.strictEqual(C.buildShareLinks(songs, { 'a::A': '   ' }), YT1 + '\n\n' + YT2); // 공백뿐 → 제외
  assert.strictEqual(C.buildShareLinks(songs), YT1 + '\n\n' + YT2);                    // 인자 생략
});

// ───────────────────────────
// TIERS 무결성
// ───────────────────────────
test('TIERS: 5단계, key 1..5', () => {
  assert.strictEqual(C.TIERS.length, 5);
  assert.deepStrictEqual(C.TIERS.map(t => t.key), [1, 2, 3, 4, 5]);
  assert.deepStrictEqual(C.TIERS.map(t => t.label), ['최애', '차애', '호', '중간', '불호']);
});

test('TIERS: 티어별 점수 매핑(최애+4 … 불호-4)', () => {
  assert.deepStrictEqual(C.TIERS.map(t => t.score), [4, 3, 2, 1, -4]);
});

// ───────────────────────────
// confidence (신뢰도 가중치 w(n))
// ───────────────────────────
test('confidence: w(n)=1-exp(-n/τ), 경계·단조 증가', () => {
  assert.strictEqual(C.confidence(0), 0);          // n=0 → 0
  assert.strictEqual(C.confidence(-3), 0);         // n<0 → 0
  // n=τ → 1-e^-1
  assert.ok(Math.abs(C.confidence(C.SCORE_TAU) - (1 - Math.exp(-1))) < 1e-12);
  assert.ok(C.confidence(2) < C.confidence(20));   // 표본 클수록 신뢰↑
  assert.ok(C.confidence(1000) > 0.999 && C.confidence(1000) <= 1);
  // 커스텀 τ: n=τ면 항상 1-e^-1
  assert.ok(Math.abs(C.confidence(5, 5) - (1 - Math.exp(-1))) < 1e-12);
});

test('bandScores: score = max(0,R)·confidence(n)와 일치', () => {
  const out = C.bandScores(
    { a: [{ band: 'a', title: 'X' }, { band: 'a', title: 'Y' }, { band: 'a', title: 'Z' }] },
    { 'a::X': 1, 'a::Y': 1, 'a::Z': 3 }   // raw=(4+4+2)/3>0
  ).a;
  assert.ok(out.raw > 0);
  assert.ok(Math.abs(out.score - out.raw * C.confidence(out.n)) < 1e-12);
});

// ───────────────────────────
// bandScores / bestBand (최애 스코어링)
// ───────────────────────────
test('bandScores: 가중 평균 R_k = Σ(s_t·c)/n (설계 예시 1.8)', () => {
  // 10곡: 최애5, 호3, 불호2 → R = (4·5 + 2·3 - 4·2)/10 = 1.8
  const songs = [];
  for (let i = 0; i < 10; i++) songs.push({ band: 'a', title: 'S' + i });
  const ranks = {};
  for (let i = 0; i < 5; i++) ranks['a::S' + i] = 1;   // 최애
  for (let i = 5; i < 8; i++) ranks['a::S' + i] = 3;   // 호
  for (let i = 8; i < 10; i++) ranks['a::S' + i] = 5;  // 불호
  const out = C.bandScores({ a: songs }, ranks);
  assert.ok(Math.abs(out.a.raw - 1.8) < 1e-9);
  assert.strictEqual(out.a.n, 10);
  const expected = 1.8 * (1 - Math.exp(-10 / C.SCORE_TAU));
  assert.ok(Math.abs(out.a.score - expected) < 1e-9);
});

test('bandScores: n=0 밴드는 {score:0, raw:0, n:0}', () => {
  const out = C.bandScores({ a: [{ band: 'a', title: 'X' }] }, {});
  assert.deepStrictEqual(out.a, { score: 0, raw: 0, n: 0 });
});

test('bandScores: 음수 raw는 0으로 클램핑', () => {
  // 전부 불호 → raw=-4 → score=max(0,…)=0
  const out = C.bandScores(
    { a: [{ band: 'a', title: 'X' }, { band: 'a', title: 'Y' }] },
    { 'a::X': 5, 'a::Y': 5 }
  );
  assert.strictEqual(out.a.raw, -4);
  assert.strictEqual(out.a.score, 0);
});

test('bandScores: 같은 raw면 표본 큰 쪽이 높은 score (소표본 수축)', () => {
  const mk = (n) => {
    const songs = [], ranks = {};
    for (let i = 0; i < n; i++) { songs.push({ band: 'a', title: 'S' + i }); ranks['a::S' + i] = 1; }
    return C.bandScores({ a: songs }, ranks).a;
  };
  const small = mk(2), big = mk(20);
  assert.strictEqual(small.raw, 4);
  assert.strictEqual(big.raw, 4);
  assert.ok(big.score > small.score);
  assert.ok(small.score > 0 && big.score <= 4);
});

test('bestBand: 최고 score 밴드, n=0 제외, 없으면 null', () => {
  const songsByBand = {
    a: [{ band: 'a', title: 'A1' }, { band: 'a', title: 'A2' }],  // 최애2 → raw 4
    b: [{ band: 'b', title: 'B1' }, { band: 'b', title: 'B2' }],  // 호2   → raw 2
    c: [{ band: 'c', title: 'C1' }],                              // 미평가(n=0)
  };
  const ranks = { 'a::A1': 1, 'a::A2': 1, 'b::B1': 3, 'b::B2': 3 };
  assert.strictEqual(C.bestBand(songsByBand, ranks), 'a');
  assert.strictEqual(C.bestBand(songsByBand, {}), null);  // 전부 미평가
});

test('bestBand: 동점은 입력(밴드) 순서 우선', () => {
  const songsByBand = {
    x: [{ band: 'x', title: 'X1' }],
    y: [{ band: 'y', title: 'Y1' }],
  };
  const ranks = { 'x::X1': 1, 'y::Y1': 1 };  // 동일 score
  assert.strictEqual(C.bestBand(songsByBand, ranks), 'x');
});
