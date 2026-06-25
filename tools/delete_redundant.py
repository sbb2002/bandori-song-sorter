"""
C1 redundant 삭제기 (HANDOFF #1) — undefined 더미앨범 중 '정규앨범과 동일 video_id'인
트랙을 삭제한다. 정규앨범에 같은 영상이 이미 있으므로 삭제해도 곡은 사라지지 않는다(손실0).

대상: verify_links.analyze 의 undef_redundant.
규칙:
  · undef 블록 *범위 내에서만* 트랙을 제거한다 → 정규앨범 트랙은 절대 건드리지 않는다
    (같은 vid가 정규앨범에도 있으므로, 파일 전체 첫 매칭 제거는 위험).
  · 트랙이 0개가 된 undef 블록은 블록째 제거한다(빈 더미 잔재 정리).

손실0 검증(기록 전 필수): 가상 적용 후 재파싱 →
  ① 삭제한 각 vid가 여전히 '비-undef' 트랙으로 같은 밴드에 존재
  ② 곡수 == before - 삭제수,  ③ undef_redundant == 0.
하나라도 실패하면 중단(미기록).

YAML은 텍스트 단위 제거(포맷·따옴표 보존). 기본 dry-run, 기록은 --apply.
  python tools/delete_redundant.py
  python tools/delete_redundant.py --apply
"""
import sys
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml"); sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_links as v
from youtube_rss import video_id
from execute_placement import split_text, join_text, remove_track_by_vid, _unq

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ──────────────────────────────────────────────
# 블록 분해/판정 (텍스트, 포맷 보존)
# ──────────────────────────────────────────────

def split_blocks(lines):
    """('- '로 시작하는 앨범 블록' 단위로 분해. prefix=첫 블록 이전 줄들."""
    starts = [k for k, ln in enumerate(lines) if ln.startswith("- ")]
    if not starts:
        return lines, []
    prefix = lines[:starts[0]]
    blocks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(lines)
        blocks.append(lines[s:e])
    return prefix, blocks


def block_field(block, key):
    pre = key + ":"
    for ln in block:
        t = ln.strip()
        if t.startswith("- "):          # 블록 첫 줄 "- band: ..."
            t = t[2:]
        if t.startswith(pre):
            return _unq(t[len(pre):])
    return None


def block_is_undef(block):
    return (block_field(block, "numbering") == "undefined"
            or block_field(block, "album_title") == "undefined")


def block_has_track(block):
    return any(ln.startswith("    - ") for ln in block)


def process_lines(lines, vids_by_band):
    """undef 블록 안에서만 vids 제거. 빈 undef 블록은 드롭. (새 lines, removed, dropped)."""
    prefix, blocks = split_blocks(lines)
    out = list(prefix)
    removed, dropped = [], []
    for block in blocks:
        if block_is_undef(block):
            band = block_field(block, "band") or ""
            for vid in list(vids_by_band.get(band, [])):
                block, ok = remove_track_by_vid(block, vid)
                if ok:
                    removed.append((band, vid))
            if not block_has_track(block):
                dropped.append(band)
                continue                 # 빈 undef 블록 → 블록째 제거
        out.extend(block)
    return out, removed, dropped


# ──────────────────────────────────────────────
# 검증용: 텍스트 → 트랙(평탄)
# ──────────────────────────────────────────────

def tracks_from_text(text):
    out = []
    for al in (yaml.safe_load(text) or []):
        band = al.get("band", "")
        num = al.get("numbering", "")
        at = al.get("album_title", "")
        undef = num == "undefined" or at == "undefined"
        for tr in (al.get("tracks") or []):
            u = tr.get("url")
            us = str(u).strip() if u is not None else ""
            out.append({"band": band, "name": tr.get("name", ""), "url": us,
                        "vid": video_id(us) if us else None, "undef": undef})
    return out


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────

def main():
    write = "--apply" in sys.argv[1:]
    tracks = v.load_tracks()
    A = v.analyze(tracks)
    redundant = A["undef_redundant"]
    n_before = len(tracks)

    by_file = defaultdict(lambda: defaultdict(set))   # fn -> band -> {vid}
    for t in redundant:
        by_file[t["file"]][t["band"]].add(t["vid"])

    print("=" * 64)
    print(f"C1 redundant 삭제기 — {'APPLY(기록)' if write else 'DRY-RUN(미기록)'}")
    print(f"대상 redundant: {len(redundant)}건 · 곡수(before): {n_before}")
    print("=" * 64)

    new_texts = {}
    all_removed, all_dropped = [], []
    for fn_name in sorted(by_file):
        path = DATA / fn_name
        lines, crlf = split_text(path.read_text(encoding="utf-8"))
        new_lines, removed, dropped = process_lines(lines, by_file[fn_name])
        new_text = join_text(new_lines, crlf)
        try:
            yaml.safe_load(new_text)              # 재파싱(개별 파일)
        except Exception as ex:
            print(f"[{fn_name}] ⚠️ 재파싱 실패 — 중단: {ex}")
            sys.exit(1)
        new_texts[fn_name] = new_text
        all_removed += removed
        all_dropped += dropped
        tail = f" · 빈블록 드롭 {len(dropped)}" if dropped else ""
        print(f"\n[{fn_name}] 삭제 {len(removed)}{tail}")
        for b, vid in removed:
            print(f"    - {b}/{vid}")

    # ── 손실0 검증 (변경 파일은 new_text, 나머지는 디스크) ──
    after = []
    for fn in sorted(DATA.glob("*.yaml")):
        text = new_texts.get(fn.name) or fn.read_text(encoding="utf-8")
        after += tracks_from_text(text)
    n_after = len(after)

    real_vids = defaultdict(set)
    for t in after:
        if not t["undef"] and t["vid"]:
            real_vids[t["band"]].add(t["vid"])

    lost = [(b, vid) for (b, vid) in all_removed if vid not in real_vids[b]]
    after_redundant = [t for t in after
                       if t["undef"] and t["vid"] and t["vid"] in real_vids[t["band"]]]
    expected_after = n_before - len(all_removed)

    print("\n" + "=" * 64)
    print("검증")
    print(f"  삭제 처리: {len(all_removed)}/{len(redundant)}  "
          f"(미발견 {len(redundant) - len(all_removed)})")
    print(f"  빈 undef 블록 드롭: {len(all_dropped)}  {all_dropped}")
    print(f"  곡수: {n_before} → {n_after}  (기대 {expected_after})  "
          f"{'OK' if n_after == expected_after else '‼️ 불일치'}")
    print(f"  손실(삭제 vid가 비-undef로 미존재): {len(lost)}  "
          f"{'OK(손실0)' if not lost else '‼️ ' + str(lost)}")
    print(f"  잔여 undef_redundant: {len(after_redundant)}  "
          f"{'OK' if not after_redundant else '‼️ 잔존'}")

    ok = (not lost and n_after == expected_after
          and not after_redundant and len(all_removed) == len(redundant))
    if not ok:
        print("\n‼️ 검증 실패 — 기록하지 않음.")
        sys.exit(1)

    if write:
        for fn_name, txt in new_texts.items():
            (DATA / fn_name).write_text(txt, encoding="utf-8")
        print("\n기록 완료. (build.py 재실행으로 index.html 반영)")
    else:
        print("\nDRY-RUN 완료 — 검증 통과. `--apply`로 기록.")


if __name__ == "__main__":
    main()
