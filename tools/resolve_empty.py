"""
빈url 트랙 정리기 (HANDOFF #1) — undefined 더미 + 미입력 슬롯의 url 빈 트랙 처리.

정책(사용자): "보강 시도 후 잔여 제거".
  · ENRICH 에 매핑된 곡 → url을 확보한 신곡(발매 직후). undef 블록에서 제거 후
    같은 밴드 New Singles 블록에 url과 함께 추가(C2 배치와 동일). track_number=발매일.
  · 그 외 url 빈 트랙 → 행 제거(재생 불가, 공식 음원 미확보 또는 빈 슬롯).
  · 트랙이 0개가 된 undef 블록은 블록째 제거.

ENRICH 후보는 WebSearch로 찾고 oEmbed(author='... - Topic')로 공식 음원임을 검증한 것만.
나머지(게임곡/커버/미발매)는 공식 음원이 없어 제거.

검증(기록 전): 가상 적용 후 재파싱 →
  ① 잔여 빈url == 0,  ② ENRICH 곡이 New Singles에 url과 함께 존재,
  ③ 곡수 == before - 제거수.
실패 시 중단(미기록). 기본 dry-run, 기록은 --apply.
  python tools/resolve_empty.py
  python tools/resolve_empty.py --apply
"""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml"); sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_rss import video_id, insert_track
from execute_placement import split_text, join_text, _unq, FALLBACK_IMG
from delete_redundant import (split_blocks, block_field, block_is_undef,
                              block_has_track, tracks_from_text)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEW_SINGLES = ("Single", "New Singles")

# 보강 확정(WebSearch + oEmbed 'X - Topic' 검증). (band, name) -> (url, track_number=발매일)
# RAS 15th single 'WHAT AN EXPLOSION'(2026-06-10) — 데이터 입력 당시 미발매라 빈url이었음.
ENRICH = {
    ("raise_a_suilen", "WHAT AN EXPLOSION"): ("https://youtu.be/5AL7kBxbMI8", "2026-06-10"),
    ("raise_a_suilen", "RUNAWAY STAR"):      ("https://youtu.be/DkMyx_sLMlk", "2026-06-10"),
}


def process_block_empties(block, band):
    """블록에서 url 빈 트랙 제거. (새 블록, removed[name], enriched[(name,(url,tn))])."""
    i = 0
    while i < len(block) and not block[i].startswith("    - "):
        i += 1
    head = block[:i]
    body, removed, enriched = [], [], []
    while i < len(block):
        if not block[i].startswith("    - "):
            body.append(block[i]); i += 1            # 트랙 사이/후 빈 줄 등 보존
            continue
        j = i + 1
        while j < len(block) and block[j].startswith("      "):
            j += 1
        tb = block[i:j]
        name = url = None
        for ln in tb:
            s = ln.strip()
            if s.startswith("name:"):
                name = _unq(s[5:])
            elif s.startswith("url:"):
                url = s[4:].strip()
        if not url:                                  # 빈url 트랙
            removed.append(name)
            if (band, name) in ENRICH:
                enriched.append((name, ENRICH[(band, name)]))
        else:
            body += tb
        i = j
    return head + body, removed, enriched


def resolve_file(fn):
    """파일 처리 → (new_text, removed[(band,name)], enriched[(band,name,url,tn)])."""
    lines, crlf = split_text(fn.read_text(encoding="utf-8"))
    prefix, blocks = split_blocks(lines)
    out_blocks, removed, enriched = [], [], []
    for block in blocks:
        band = block_field(block, "band") or ""
        nb, rm, en = process_block_empties(block, band)
        removed += [(band, n) for n in rm]
        enriched += [(band, n, u, tn) for (n, (u, tn)) in en]
        if block_is_undef(nb) and not block_has_track(nb):
            continue                                 # 빈 undef 블록 드롭
        out_blocks.append(nb)
    new_lines = list(prefix) + [ln for b in out_blocks for ln in b]
    text = join_text(new_lines, crlf)
    # 보강: 같은 파일 New Singles 블록에 추가(url 포함)
    for band, name, url, tn in enriched:
        text, _ = insert_track(text, band, NEW_SINGLES[0], NEW_SINGLES[1],
                               FALLBACK_IMG, tn, name, url)
    return text, removed, enriched


def main():
    write = "--apply" in sys.argv[1:]

    # before
    before = []
    for fn in sorted(DATA.glob("*.yaml")):
        before += tracks_from_text(fn.read_text(encoding="utf-8"))
    n_before = len(before)
    empties_before = [t for t in before if not t["url"]]

    print("=" * 64)
    print(f"빈url 정리기 — {'APPLY(기록)' if write else 'DRY-RUN(미기록)'}")
    print(f"빈url(before): {len(empties_before)} · 곡수(before): {n_before}")
    print("=" * 64)

    new_texts, all_removed, all_enriched = {}, [], []
    for fn in sorted(DATA.glob("*.yaml")):
        text, removed, enriched = resolve_file(fn)
        if text == fn.read_text(encoding="utf-8"):
            continue
        try:
            yaml.safe_load(text)
        except Exception as ex:
            print(f"[{fn.name}] ⚠️ 재파싱 실패 — 중단: {ex}"); sys.exit(1)
        new_texts[fn.name] = text
        all_removed += removed
        all_enriched += enriched
        print(f"\n[{fn.name}] 제거 {len(removed)} · 보강(New Singles 이동) {len(enriched)}")
        for band, name in removed:
            tag = " → 보강" if any(e[0] == band and e[1] == name for e in enriched) else ""
            print(f"    - 제거 {band}/{name!r}{tag}")
        for band, name, url, tn in enriched:
            print(f"    + 보강 {band}/{name!r}  {url}  (tn {tn})")

    # ── 검증 ──
    after = []
    for fn in sorted(DATA.glob("*.yaml")):
        text = new_texts.get(fn.name) or fn.read_text(encoding="utf-8")
        after += tracks_from_text(text)
    n_after = len(after)
    empties_after = [t for t in after if not t["url"]]

    # 보강곡: undef에서 제거되며 동시에 New Singles로 추가 → 순삭제는 (제거 - 보강)
    n_removed_net = len(all_removed) - len(all_enriched)
    expected = n_before - n_removed_net

    # 보강곡이 New Singles에 url과 함께 존재?
    enrich_ok = []
    for band, name, url, tn in all_enriched:
        vid = video_id(url)
        hit = any(t["band"] == band and t["name"] == name and not t["undef"]
                  and t["vid"] == vid for t in after)
        enrich_ok.append(hit)

    print("\n" + "=" * 64)
    print("검증")
    print(f"  제거 {len(all_removed)} (순삭제 {n_removed_net}) · 보강 {len(all_enriched)}")
    print(f"  곡수: {n_before} → {n_after}  (기대 {expected})  "
          f"{'OK' if n_after == expected else '‼️ 불일치'}")
    print(f"  잔여 빈url: {len(empties_after)}  "
          f"{'OK(0)' if not empties_after else '‼️ ' + str([(t['band'],t['name']) for t in empties_after])}")
    print(f"  보강곡 New Singles 안착: {sum(enrich_ok)}/{len(all_enriched)}  "
          f"{'OK' if all(enrich_ok) else '‼️ 누락'}")

    ok = (n_after == expected and not empties_after and all(enrich_ok))
    if not ok:
        print("\n‼️ 검증 실패 — 기록하지 않음."); sys.exit(1)

    if write:
        for fn_name, txt in new_texts.items():
            (DATA / fn_name).write_text(txt, encoding="utf-8")
        print("\n기록 완료. (build.py 재실행으로 index.html 반영)")
    else:
        print("\nDRY-RUN 완료 — 검증 통과. `--apply`로 기록.")


if __name__ == "__main__":
    main()
