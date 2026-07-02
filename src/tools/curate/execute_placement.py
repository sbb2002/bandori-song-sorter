"""
C2 placement 실행기 (HANDOFF #1) — undefined 유일본을 정규/서브유닛 앨범으로 배치.

입력: tools/curate/c2_placement.csv  (band,video_id,type,current_name,official_title,album_FILL,name_FILL)
동작(행별, album_FILL 비어있으면 skip):
  · 소스 트랙을 (band, video_id)로 undef 블록에서 찾는다.
  · 최종 곡명 = name_FILL(있으면) 아니면 current_name.
  · 소스의 현재 album_title == album_FILL  → 이미 올바른 블록(서브유닛). 블록 numbering만
    'undefined' → 'Single'로 교정(de-undef). 곡은 그대로.
  · 그 외(소스가 'undefined' 더미)            → 더미에서 트랙 제거 후 (band,'Single') 'New Singles'
    블록에 append(없으면 신설). track_number는 원래 값 보존.

추가: 음원우선 규칙으로 확정된 중복 MV 2건 삭제(DELETIONS). 정규 음원이 이미 있어 손실 0.

YAML은 youtube_rss의 텍스트 삽입(포맷·따옴표 보존, 순수 추가/삭제)을 재사용한다.
ruamel/안전덤프는 비표준 혼합 들여쓰기를 못 살려 diff가 폭발하므로 쓰지 않는다.

기본은 dry-run(미기록). 실제 기록은 --apply.
  python src/tools/curate/execute_placement.py            # 계획 출력 + 검증(미기록)
  python src/tools/curate/execute_placement.py --apply     # 데이터 기록
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
CSV_PATH = ROOT / "src" / "tools" / "curate" / "c2_placement.csv"

# youtube_rss 는 tools/collect/ 에 있음(공유 모듈).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "collect"))
from youtube_rss import insert_track, video_id, yaml_squote  # 텍스트 헬퍼 재사용

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NEW_SINGLES = ("Single", "New Singles")          # (numbering, album_title)
FALLBACK_IMG = "assets/icons/_fallback.png"      # 기존 New Singles 블록과 동일
SUBUNIT_NUMBERING = "Single"                     # 서브유닛 블록 de-undef 시 numbering(비표시 필드)

# 음원우선 규칙으로 확정된 중복 MV — 정규 음원이 이미 존재 → undef 사본 삭제(손실 0).
DELETIONS = {
    "uab9GICZjy4": "mugendai_mutype Mutant Mutant(MV) — 음원 'みゅーたんとミュータント'(プログレス サイン) 존재",
    "45LUJTzHyek": "poppin_party DOKI DOKI DATE(MV) — 'どきどきデエト' 이미 New Singles에 존재",
}


# ──────────────────────────────────────────────
# 소스 인덱스: undef 블록의 (band, vid) → 위치/메타
# ──────────────────────────────────────────────

def band_files():
    """band -> yaml 파일 경로 (밴드는 한 파일에 산다는 전제)."""
    m = {}
    for fn in sorted(DATA.glob("*.yaml")):
        for al in (yaml.safe_load(fn.read_text(encoding="utf-8")) or []):
            m.setdefault(al.get("band", ""), fn)
    return m


def undef_index():
    """(band, vid) → dict(file, album_title, numbering, track_number, name, url) — undef 블록만."""
    idx = {}
    for fn in sorted(DATA.glob("*.yaml")):
        for al in (yaml.safe_load(fn.read_text(encoding="utf-8")) or []):
            band = al.get("band", "")
            num = al.get("numbering", "")
            atitle = al.get("album_title", "")
            is_undef = num == "undefined" or atitle == "undefined"
            if not is_undef:
                continue
            for tr in (al.get("tracks") or []):
                url = (tr.get("url") or "").strip()
                vid = video_id(url) if url else None
                if vid:
                    idx[(band, vid)] = {
                        "file": fn, "album_title": atitle, "numbering": num,
                        "track_number": tr.get("track_number", ""),
                        "name": tr.get("name", ""), "url": url,
                    }
    return idx


# ──────────────────────────────────────────────
# 텍스트 편집 (포맷 보존, 라인 단위)
# ──────────────────────────────────────────────

def split_text(text):
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n").split("\n"), crlf


def join_text(lines, crlf):
    out = "\n".join(lines)
    return out.replace("\n", "\r\n") if crlf else out


def remove_track_by_vid(lines, vid):
    """트랙 서브블록('    - ...' + 6칸 연속줄) 1건을 url의 vid로 찾아 제거. (없으면 변동 없음)"""
    i = 0
    while i < len(lines):
        if lines[i].startswith("    - "):
            j = i + 1
            while j < len(lines) and lines[j].startswith("      "):
                j += 1
            block = lines[i:j]
            for ln in block:
                s = ln.strip()
                if s.startswith("url:"):
                    u = s[4:].strip()
                    if u and video_id(u) == vid:
                        return lines[:i] + lines[j:], True
            i = j
        else:
            i += 1
    return lines, False


def set_block_numbering(lines, band, album_title, new_num):
    """(band, album_title) 앨범 블록의 'numbering' 줄을 new_num으로 교체."""
    starts = [k for k, ln in enumerate(lines) if ln.startswith("- ")]
    for bi, s in enumerate(starts):
        e = starts[bi + 1] if bi + 1 < len(starts) else len(lines)
        bl = lines[s:e]
        b = a = None
        for ln in bl:
            t = ln.strip()
            if t.startswith("- "):        # 블록 첫 줄 "- band: ..."
                t = t[2:]
            if t.startswith("band:"):
                b = _unq(t[5:])
            elif t.startswith("album_title:"):
                a = _unq(t[12:])
        if b == band and a == album_title:
            for k in range(s, e):
                t = lines[k].strip()
                if t.startswith("numbering:"):
                    lines[k] = f"  numbering: {yaml_squote(new_num)}"
                    return lines, True
    return lines, False


def _unq(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        inner = v[1:-1]
        return inner.replace("''", "'") if v[0] == "'" else inner
    return v


# ──────────────────────────────────────────────
# 계획 수립 + 적용
# ──────────────────────────────────────────────

def build_plan():
    rows = [r for r in csv.DictReader(CSV_PATH.open(encoding="utf-8"))
            if r["album_FILL"].strip()]
    idx = undef_index()
    files = band_files()
    plan = defaultdict(lambda: {"delete": [], "move": [], "deundef": []})
    errors = []

    # 삭제
    for vid, why in DELETIONS.items():
        hit = next((meta for (b, v), meta in idx.items() if v == vid), None)
        if not hit:
            errors.append(f"삭제 대상 vid {vid} 를 undef 블록에서 못 찾음")
            continue
        plan[hit["file"]]["delete"].append((vid, why))

    # 배치
    for r in rows:
        band, vid = r["band"], r["video_id"]
        meta = idx.get((band, vid))
        if not meta:
            errors.append(f"{band}/{vid} 소스 트랙(undef)을 못 찾음 — current={r['current_name']!r}")
            continue
        final = (r["name_FILL"].strip() or r["current_name"]).strip()
        target = r["album_FILL"].strip()
        if meta["album_title"] == target:
            # 이미 올바른 블록 → numbering만 교정
            plan[meta["file"]]["deundef"].append((band, target))
        else:
            plan[meta["file"]]["move"].append({
                "band": band, "vid": vid, "name": final, "url": meta["url"],
                "track_number": meta["track_number"], "target": target,
            })
    return plan, errors, len(rows)


def apply_file(fn, ops, write):
    text = fn.read_text(encoding="utf-8")
    lines, crlf = split_text(text)
    log = []

    for vid, why in ops["delete"]:
        lines, ok = remove_track_by_vid(lines, vid)
        log.append(f"  삭제 {'OK' if ok else 'FAIL'}: {vid}  ({why})")

    for mv in ops["move"]:
        lines, ok = remove_track_by_vid(lines, mv["vid"])
        if not ok:
            log.append(f"  이동 FAIL(소스 제거 실패): {mv['band']}/{mv['vid']}")
            continue
        new_text, action = insert_track(
            join_text(lines, False), mv["band"], NEW_SINGLES[0], NEW_SINGLES[1],
            FALLBACK_IMG, mv["track_number"], mv["name"], mv["url"])
        lines = new_text.split("\n")
        log.append(f"  이동 {action:8}: {mv['band']} → New Singles | {mv['name']!r}")

    for band, atitle in dict.fromkeys(ops["deundef"]):  # 중복 제거(블록 1회)
        lines, ok = set_block_numbering(lines, band, atitle, SUBUNIT_NUMBERING)
        log.append(f"  de-undef {'OK' if ok else 'FAIL'}: {band}/{atitle} numbering→{SUBUNIT_NUMBERING!r}")

    new_text = join_text(lines, crlf)
    # 안전: 재파싱 검증
    try:
        yaml.safe_load(new_text)
    except Exception as ex:
        log.append(f"  ⚠️ 재파싱 실패 — 기록 취소: {ex}")
        return log, False
    if write:
        fn.write_text(new_text, encoding="utf-8")
    return log, True


def main():
    write = "--apply" in sys.argv[1:]
    plan, errors, nrows = build_plan()

    print("=" * 64)
    print(f"C2 placement 실행기 — {'APPLY(기록)' if write else 'DRY-RUN(미기록)'}")
    print("=" * 64)
    if errors:
        print("‼️ 사전 오류:")
        for e in errors:
            print("   -", e)
        print("   → 중단(데이터 무변경).")
        sys.exit(1)

    ok_all = True
    for fn in sorted(plan):
        ops = plan[fn]
        print(f"\n[{fn.name}]  삭제 {len(ops['delete'])} · 이동 {len(ops['move'])} · "
              f"de-undef {len(set(ops['deundef']))}")
        log, ok = apply_file(fn, ops, write)
        ok_all &= ok
        for l in log:
            print(l)

    print("\n" + "=" * 64)
    print(f"행 처리: {nrows} · 삭제: {len(DELETIONS)}")
    if not write:
        print("DRY-RUN 완료 — 이상 없으면 `--apply`로 기록.")
    else:
        print("기록 완료." if ok_all else "⚠️ 일부 파일 기록 실패(위 로그 확인).")


if __name__ == "__main__":
    main()
