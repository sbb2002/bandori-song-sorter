"""
fix_url.csv 적용기 — docs/working/urgent.md 재생불가(지역락) 곡 URL 교체/삭제.

입력: tools/curate/fix_url.csv  [song_name, current_url, modified_url, plb]
동작(행별, current_url 의 video_id 로 src/content/songs/*.yaml 에서 트랙을 찾는다):
  · modified_url 있음 → 그 url 줄을 modified_url 로 교체(텍스트 단위, 포맷·따옴표 보존).
  · modified_url 공란 → 해당 트랙 삭제(없는 곡 — docs/working/urgent.md 규약).

YAML 은 텍스트 라인 단위로만 손대 기존 따옴표/들여쓰기/정렬을 보존한다
(youtube_rss/execute_placement 와 동일 원칙 — 재직렬화 금지).

기록 전 loss 검증(하나라도 실패하면 중단):
  ① 각 행이 정확히 1곳에서 매칭됐는가(0=미발견, 2+=중복 → 중단).
  ② 재파싱(yaml.safe_load) 성공.
  ③ 교체행: old_vid 사라지고 new_vid 가 같은 밴드에 존재. 삭제행: vid 사라짐.
  ④ 곡수 == before - 삭제수.

기본 dry-run(미기록). 실제 기록은 --apply.
  python src/tools/curate/apply_fix_url.py
  python src/tools/curate/apply_fix_url.py --apply
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml"); sys.exit(1)

ROOT = Path(__file__).resolve().parents[3]   # src/tools/curate/<file> → repo root
DATA = ROOT / "src" / "content" / "songs"
CSV_PATH = ROOT / "src" / "tools" / "curate" / "fix_url.csv"

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                     # 같은 폴더: execute_placement
sys.path.insert(0, str(HERE.parent / "collect"))  # 공유 모듈: youtube_rss
from youtube_rss import video_id
from execute_placement import split_text, join_text, remove_track_by_vid

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def replace_url_by_vid(lines, old_vid, new_url):
    """url 줄(현재 vid==old_vid)의 값을 new_url 로 교체. (새 lines, 교체수)."""
    out, n = [], 0
    for ln in lines:
        s = ln.strip()
        if s.startswith("url:"):
            u = s[4:].strip()
            if u and video_id(u) == old_vid:
                indent = ln[:len(ln) - len(ln.lstrip())]
                out.append(f"{indent}url: {new_url}")
                n += 1
                continue
        out.append(ln)
    return out, n


def load_rows():
    """[(song, old_vid, new_url|'')]. old_vid 없으면 에러로 모은다."""
    rows, bad = [], []
    for r in csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")):
        old = video_id((r.get("current_url") or "").strip())
        new = (r.get("modified_url") or "").strip()
        name = (r.get("song_name") or "").strip()
        if not old:
            bad.append(name)
            continue
        rows.append((name, old, new))
    return rows, bad


def tracks_from_text(text):
    out = []
    for al in (yaml.safe_load(text) or []):
        band = al.get("band", "")
        for tr in (al.get("tracks") or []):
            u = tr.get("url")
            us = str(u).strip() if u is not None else ""
            out.append({"band": band, "vid": video_id(us) if us else None})
    return out


def main():
    write = "--apply" in sys.argv[1:]
    rows, bad = load_rows()
    if bad:
        print(f"‼️ current_url 파싱 실패 {len(bad)}건: {bad} — 중단"); sys.exit(1)

    repl = [(n, ov, nu) for n, ov, nu in rows if nu]
    dele = [(n, ov) for n, ov, nu in rows if not nu]

    # before 스냅샷
    before = []
    for fn in sorted(DATA.glob("*.yaml")):
        before += tracks_from_text(fn.read_text(encoding="utf-8"))
    n_before = len(before)

    print("=" * 64)
    print(f"fix_url 적용기 — {'APPLY(기록)' if write else 'DRY-RUN(미기록)'}")
    print(f"교체 {len(repl)} · 삭제 {len(dele)} · 곡수(before) {n_before}")
    print("=" * 64)

    match_count = defaultdict(int)   # old_vid -> 매칭된 횟수(전 파일 합)
    new_texts = {}

    for fn in sorted(DATA.glob("*.yaml")):
        lines, crlf = split_text(fn.read_text(encoding="utf-8"))
        changed = False
        for name, ov, nu in repl:
            lines, c = replace_url_by_vid(lines, ov, nu)
            if c:
                match_count[ov] += c
                changed = True
                print(f"  [교체] {fn.name}: {name}  {ov} → {video_id(nu)}")
        for name, ov in dele:
            lines, ok = remove_track_by_vid(lines, ov)
            if ok:
                match_count[ov] += 1
                changed = True
                print(f"  [삭제] {fn.name}: {name}  {ov}")
        if changed:
            text = join_text(lines, crlf)
            try:
                yaml.safe_load(text)
            except Exception as ex:
                print(f"[{fn.name}] ⚠️ 재파싱 실패 — 중단: {ex}"); sys.exit(1)
            new_texts[fn.name] = text

    # ── 검증 ──
    print("\n" + "=" * 64); print("검증")
    miss = [(n, ov) for n, ov, _ in rows if match_count[ov] == 0]
    dup = [(ov, match_count[ov]) for _, ov, _ in rows if match_count[ov] > 1]
    print(f"  매칭: {sum(1 for r in rows if match_count[r[1]] == 1)}/{len(rows)} "
          f"(미발견 {len(miss)} · 중복 {len(dup)})")
    if miss: print(f"    ‼️ 미발견: {miss}")
    if dup:  print(f"    ‼️ 중복매칭: {dup}")

    after = []
    for fn in sorted(DATA.glob("*.yaml")):
        text = new_texts.get(fn.name) or fn.read_text(encoding="utf-8")
        after += tracks_from_text(text)
    n_after = len(after)
    by_band_vids = defaultdict(set)
    for t in after:
        if t["vid"]:
            by_band_vids[t["band"]].add(t["vid"])
    all_vids_after = {t["vid"] for t in after if t["vid"]}

    # 교체: old 사라지고 new 존재 / 삭제: old 사라짐
    repl_ok = all(video_id(nu) in all_vids_after and ov not in all_vids_after
                  for _, ov, nu in repl)
    dele_ok = all(ov not in all_vids_after for _, ov in dele)
    expected = n_before - len(dele)
    count_ok = n_after == expected

    print(f"  곡수: {n_before} → {n_after} (기대 {expected}) {'OK' if count_ok else '‼️ 불일치'}")
    print(f"  교체 검증(old 제거·new 존재): {'OK' if repl_ok else '‼️ 실패'}")
    print(f"  삭제 검증(vid 제거): {'OK' if dele_ok else '‼️ 실패'}")

    ok = (not miss and not dup and count_ok and repl_ok and dele_ok)
    if not ok:
        print("\n‼️ 검증 실패 — 기록하지 않음."); sys.exit(1)

    if write:
        for fn_name, txt in new_texts.items():
            (DATA / fn_name).write_text(txt, encoding="utf-8")
        print(f"\n기록 완료 ({len(new_texts)}개 파일). build.py 재실행으로 index.html 반영.")
    else:
        print("\nDRY-RUN 완료 — 검증 통과. `--apply`로 기록.")


if __name__ == "__main__":
    main()
