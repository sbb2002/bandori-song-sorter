"""
백필 삽입 (HANDOFF 1-a 오리지널 / 1-b 커버) — `new_songs.csv` 의 행을
각 밴드 앨범(또는 various_artists)으로 추가한다.
- 기본(오리지널): type=original → numbering=Single / album_title="New Singles".
- `--cover`(1-b 커버): type=cover → numbering=Cover / album_title="Covers",
  곡명에 " (Cover)" 접미(클라이언트 커버 탭 판별: album_title='Covers' + 곡명 '(Cover)').

- 발매일(track_number)은 Data API(`fetch_uploads`)로 video_id→published 재조회
  (백필과 동일 출처). 미확인 시 'X0' 폴백(기존 큐레이션 관행과 동일).
- 삽입은 (band, numbering, album_title) 매칭 → various_artists 의 복수 Single
  앨범(Glitter*Green 등)에 잘못 들어가는 것을 방지(`insert_track` 보강판).
- 멱등: 이미 있는 video_id 는 건너뜀. 재실행 안전.
- 재생불가 가드: `tools/curate/invalid_url.csv` 의 곡(지역락 등으로 앱에서 뺀 곡)은
  건너뛴다. 단 그 행의 modified_url 이 채워지면(대체 음원 확보) 그 URL 로 재등록.
  → 삭제한 지역락 곡이 재실행으로 되살아나지 않으면서, 나중에 url 이 생기면 자동 복귀.
- dry-run 기본(파일·데이터 미변경). `--apply` 로 기록.
- comment 라우팅: 'various' 포함 → various_artists(etc.yaml) 로 이동.

  python src/tools/collect/insert_backfill.py                  # 오리지널 dry-run
  python src/tools/collect/insert_backfill.py --apply          # 오리지널 기록
  python src/tools/collect/insert_backfill.py --cover          # 커버 dry-run
  python src/tools/collect/insert_backfill.py --cover --apply  # 커버 기록
  python src/tools/collect/insert_backfill.py roselia          # 특정 밴드만(공백 다수)
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_rss import (DATA_DIR, FALLBACK_IMG, BAND_CHANNELS, video_id,
                         load_existing, _block_field, _track_block, _album_block)
from youtube_api import load_env_key, fetch_uploads, APIError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
CSV = HERE / "new_songs.csv"                              # tools/collect/
INVALID_CSV = HERE.parent / "curate" / "invalid_url.csv"  # 재생불가 가드 목록
NUMBERING = "Single"
ALBUM = "New Singles"
VA_BAND = "various_artists"


def insert_track_strict(text, band, numbering, album_title, img_url,
                        track_number, name, url):
    """`insert_track` 의 (band, numbering, album_title) 3중 매칭판.

    band 만으로는 various_artists 의 여러 Single 앨범을 구분하지 못하므로
    album_title 까지 일치해야 append, 아니면 EOF 에 새 블록 created.
    기존 줄은 절대 재작성하지 않아 diff 가 순수 추가다(원본 insert_track 동일).
    """
    name = str(name).replace("\r", " ").replace("\n", " ").strip()
    lines = text.split("\n")
    starts = [i for i, ln in enumerate(lines) if ln.startswith("- ")]
    blocks = [(s, starts[i + 1] if i + 1 < len(starts) else len(lines))
              for i, s in enumerate(starts)]

    target = None
    for (s, e) in blocks:
        bl = lines[s:e]
        if (_block_field(bl, "band") == band
                and _block_field(bl, "numbering") == numbering
                and _block_field(bl, "album_title") == album_title):
            target = (s, e)
            break

    track_lines = _track_block(track_number, name, url).split("\n")
    if target:
        s, e = target
        ip = e
        while ip - 1 >= s and lines[ip - 1].strip() == "":
            ip -= 1
        return "\n".join(lines[:ip] + track_lines + lines[ip:]), "appended"

    end = len(lines)
    while end - 1 >= 0 and lines[end - 1].strip() == "":
        end -= 1
    block = _album_block(band, numbering, album_title, img_url,
                         track_number, name, url).split("\n")
    return "\n".join(lines[:end] + [""] + block + [""]), "created"


def _track_count(albums):
    return sum(len(a.get("tracks") or []) for a in (albums or []))


def load_invalid():
    """invalid_url.csv → {current_url 의 video_id: modified_url}.

    재생불가(지역락 등)로 앱에서 뺀 곡 목록. modified_url 공란 = 아직 보류(삽입
    건너뜀), 채워짐 = 대체 재생 URL 확보(그 URL 로 재등록). 파일 없으면 {}."""
    if not INVALID_CSV.exists():
        return {}
    out = {}
    for r in csv.DictReader(INVALID_CSV.open(encoding="utf-8-sig")):
        v = video_id((r.get("current_url") or "").strip())
        if v:
            out[v] = (r.get("modified_url") or "").strip()
    return out


def main():
    apply = "--apply" in sys.argv
    cover = "--cover" in sys.argv
    only = {a for a in sys.argv[1:] if not a.startswith("-")}

    want_type = "cover" if cover else "original"
    numbering = "Cover" if cover else NUMBERING
    album = "Covers" if cover else ALBUM

    key = load_env_key()
    if not key:
        print("‼️ .env 에 YOUTUBE_API_KEY 가 없습니다."); sys.exit(1)

    if not CSV.exists():
        print(f"‼️ {CSV} 없음."); sys.exit(1)

    rows = [r for r in csv.DictReader(CSV.open(encoding="utf-8-sig"))
            if r["type"] == want_type and (not only or r["author"] in only)]
    print(f"{want_type} {len(rows)}곡 대상 ({'오리지널 제외' if cover else '커버 제외'})\n")

    # 발매일 매핑 — source 채널(author)별 업로드 전체 조회(백필과 동일 출처)
    authors = sorted({r["author"] for r in rows})
    pub = {}
    print(f"발매일 조회: {len(authors)}개 채널")
    for a in authors:
        ch = BAND_CHANNELS.get(a)
        if not ch:
            print(f"  ⚠️ {a}: Topic 채널 미등록 — 발매일 폴백(X0)"); continue
        try:
            ups = fetch_uploads(ch, key)
            for u in ups:
                pub[u["video_id"]] = u["published"]
        except APIError as e:
            print(f"  ⚠️ {a}: API 오류 — {e}")
    print()

    names_by_band, ids_by_band, band_file = load_existing()
    invalid = load_invalid()

    # 라우팅 + 파일별 그룹화
    by_file = defaultdict(list)      # path -> [(target, row, vid, date, use_url, note)]
    skipped = []
    for r in rows:
        orig_vid = video_id(r["url"])
        target = VA_BAND if "various" in r.get("comment", "").lower() else r["author"]
        path = band_file.get(target) or (DATA_DIR / f"{target}.yaml")

        # 재생불가 가드: invalid_url.csv 에 있으면 modified_url 유무로 분기.
        # 공란=보류(건너뜀), 채워짐=대체 URL 로 재등록 → 지역락 삭제곡이 재실행으로
        # 되살아나지 않으면서, 대체 음원이 생기면 그 URL 로 자동 복귀.
        if orig_vid in invalid:
            repl = invalid[orig_vid]
            if not repl:
                skipped.append((target, r["song_name"], "재생불가·보류(invalid_url.csv)"))
                continue
            use_url, vid, note = repl, video_id(repl), " [재등록]"
        else:
            use_url, vid, note = r["url"], orig_vid, ""

        date = pub.get(vid) or pub.get(orig_vid) or "X0"
        if vid and vid in ids_by_band.get(target, set()):
            skipped.append((target, r["song_name"], "이미 존재(video_id)"))
            continue
        by_file[path].append((target, r, vid, date, use_url, note))

    total = 0
    for path in sorted(by_file, key=lambda p: p.name):
        raw = path.read_bytes()
        crlf = b"\r\n" in raw
        text = raw.decode("utf-8").replace("\r\n", "\n")
        before_n = _track_count(yaml.safe_load(text))

        print(f"=== {path.name} ===")
        items = by_file[path]
        for (target, r, vid, date, use_url, note) in items:
            disp_name = r["song_name"] + " (Cover)" if cover else r["song_name"]
            text, action = insert_track_strict(
                text, target, numbering, album, FALLBACK_IMG, date, disp_name, use_url)
            tgt = f" → {target}" if target != r["author"] else ""
            print(f"   [{action:8}] {date:10} {disp_name}{tgt}{note}  ({vid})")
            total += 1

        after = yaml.safe_load(text)
        after_n = _track_count(after)
        added = len(items)
        loss0 = (after_n == before_n + added)
        all_ids = {video_id(t.get("url"))
                   for a in (after or []) for t in (a.get("tracks") or [])}
        present = all(vid in all_ids for (_, _, vid, _, _, _) in items)
        print(f"   → tracks {before_n} +{added} = {after_n}  "
              f"loss-0={'OK' if loss0 else 'FAIL'}  present={'OK' if present else 'FAIL'}")

        if apply and loss0 and present:
            out = text.replace("\n", "\r\n") if crlf else text
            path.write_bytes(out.encode("utf-8"))
            print("   ✅ 기록 완료")
        elif apply:
            print("   ⛔ 검증 실패 — 이 파일은 기록하지 않음")
        print()

    if skipped:
        print("=== 건너뜀 ===")
        for t, n, why in skipped:
            print(f"   [{t}] {n} — {why}")
        print()

    mode = "적용" if apply else "dry-run"
    print(f"{mode} 완료: 삽입 {total}곡 · 건너뜀 {len(skipped)}곡")
    if not apply:
        print("※ 파일·데이터 미변경. 실제 기록: --apply")


if __name__ == "__main__":
    main()
