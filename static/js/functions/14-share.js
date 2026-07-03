// ===========================================================
// BanG Dream! Song Sorter — 14-share.js
// §14 링크 복사 / Download 내보내기
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

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

