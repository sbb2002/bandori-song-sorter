// ===========================================================
// BanG Dream! Song Sorter — 05-band-selector.js
// §5 밴드 셀렉터(A) 렌더 + 링
// ⚠ 로드 순서 고정: 01→…→19 (원본 script.js를 섹션 경계로 분할 · classic 순서 로드)
//   전역 스코프/가변 상태 공유. core.js(window.BandoriCore) 이후 로드.
// ===========================================================

// ───────────────────────────
// 5. Render: Band selector (A)
// ───────────────────────────

/** 밴드 나열 순서 = BAND_ORDER 우선 + 나머지(various_artists 등)는 뒤.
 *  좌측 셀렉터와 Download 결과가 동일 순서를 쓰도록 공유. */
function bandsInSelectorOrder() {
    const ordered = BAND_ORDER.filter(b => bands.includes(b));
    const rest = bands.filter(b => !BAND_ORDER.includes(b));
    return [...ordered, ...rest];
}

function renderBandSelector() {
    const el = document.getElementById('band-selector');
    el.innerHTML = '';

    el.appendChild(makeBandBtn('ALL', true));

    const divider = document.createElement('div');
    divider.className = 'band-divider';
    el.appendChild(divider);

    bandsInSelectorOrder().forEach(b => el.appendChild(makeBandBtn(b, false)));
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
        const ring = makeRingSvg();
        btn.appendChild(ring);

        const img = document.createElement('img');
        img.src = bandIcon(band);
        img.alt = bandDisplay(band);
        img.className = 'band-btn-icon';
        // 아이콘 로드 실패 시: img만 교체(링 span은 보존)
        img.onerror = () => {
            img.remove();
            const txt = document.createElement('span');
            txt.className = 'band-btn-fallback';
            txt.textContent = bandDisplay(band).slice(0, 4);
            btn.appendChild(txt);
        };
        btn.appendChild(img);

        applyBandRing(ring, band);
    }

    btn.addEventListener('click', () => selectBand(band));
    return btn;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

/** 진행률 링 SVG(트랙 원 + 채움 원). 벡터 stroke라 둘레가 항상 AA → 계단현상 없음.
 *  채움량(--ring-pct)·색 버킷은 applyBandRing이 설정. pathLength=100이라 pct가 곧 길이. */
function makeRingSvg() {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'band-ring');
    svg.setAttribute('viewBox', '0 0 36 36');
    svg.setAttribute('aria-hidden', 'true');
    ['ring-track', 'ring-fill'].forEach(cls => {
        const c = document.createElementNS(SVG_NS, 'circle');
        c.setAttribute('class', cls);
        c.setAttribute('cx', '18');
        c.setAttribute('cy', '18');
        c.setAttribute('r', '16');
        if (cls === 'ring-fill') c.setAttribute('pathLength', '100');
        svg.appendChild(c);
    });
    return svg;
}

/** 밴드 진행률 링 갱신: 평가율(ranked/total)을 채움 비율·색 버킷에 반영.
 *  0~30% Red(low) / 31~69% Yellow(mid) / 70%~ Green(high). */
function applyBandRing(ring, band) {
    const { ranked, total } = C.countRanked(dedupedByBand[band] || [], ranks);
    const pct = total ? (ranked / total * 100) : 0;
    ring.style.setProperty('--ring-pct', pct.toFixed(1));
    ring.classList.remove('low', 'mid', 'high');
    ring.classList.add(pct >= 70 ? 'high' : pct >= 31 ? 'mid' : 'low');
}

/** 셀렉터를 다시 그리지 않고(아이콘 리로드 방지) 링만 갱신 — 랭크 변경 시 호출. */
function updateBandRings() {
    document.querySelectorAll('#band-selector .band-ring').forEach(ring => {
        const band = ring.parentElement.dataset.band;
        if (band) applyBandRing(ring, band);
    });
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
    renderWordcloud();      // 워드클라우드=하단 독 상시 → 밴드 바뀔 때마다 갱신
    if (_clusterChart) { _clHover = null; _clDraw(); }   // 음원맵 연동: 밴드 선택=포커스 / ALL=개요
}

