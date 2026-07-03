"""src/content/songs/*.yaml → 음원맵 매니페스트 CSV(idx,band,song,url). 음원맵 전곡 확대(HANDOFF 작업 2 Phase 0-A).

fetch_audio.py(오디오 수집) · build_perceptual_map.py(좌표 빌드) 공통 입력.
재생가능 트랙(url 있음)만, **vid 기준 전역 dedup**(같은 영상 1회). idx = 0..N-1 전역 인덱스.

사용:
  python src/tools/cluster/build_manifest.py                                  # 전곡 → songs_full.csv
  python src/tools/cluster/build_manifest.py --cap 40                         # 밴드당 40곡 상한
  python src/tools/cluster/build_manifest.py --out src/content/cluster/songs_full.csv
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml"); sys.exit(1)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]
SONGS = ROOT / "src" / "content" / "songs"
DEFAULT_OUT = ROOT / "src" / "content" / "cluster" / "songs_full.csv"


def video_id(url: str) -> str | None:
    """youtu.be/<id> · youtube.com/watch?v=<id> · /embed|/shorts/<id> → 11자 id."""
    u = urlparse((url or "").strip())
    host = (u.hostname or "").lower()
    if host in ("youtu.be", "www.youtu.be"):
        vid = u.path.lstrip("/").split("/")[0]
        return vid or None
    if "youtube.com" in host:
        qs = parse_qs(u.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
        m = re.match(r"/(?:embed|shorts)/([^/?&]+)", u.path)
        if m:
            return m.group(1)
    return None


def load_rows(cap: int) -> list[dict]:
    """[{band,song,url,vid}] — 파일명 정렬(밴드 그룹) · 앨범/트랙 순서 보존 · vid dedup · 밴드 캡."""
    seen: set[str] = set()
    per_band: dict[str, int] = defaultdict(int)
    rows: list[dict] = []
    for fn in sorted(SONGS.glob("*.yaml")):
        for al in (yaml.safe_load(fn.read_text(encoding="utf-8")) or []):
            band = al.get("band", "")
            for tr in (al.get("tracks") or []):
                url = str(tr.get("url") or "").strip()
                vid = video_id(url) if url else None
                if not vid or vid in seen:
                    continue
                if cap and per_band[band] >= cap:
                    continue
                seen.add(vid)
                per_band[band] += 1
                rows.append({"band": band, "song": tr.get("name", ""), "url": url, "vid": vid})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="songs/*.yaml → 음원맵 매니페스트 CSV")
    ap.add_argument("--cap", type=int, default=0, help="밴드당 상한(0=제한 없음, 전곡)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="출력 CSV 경로")
    args = ap.parse_args(argv)

    rows = load_rows(args.cap)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "band", "song", "url"])
        for i, r in enumerate(rows):
            w.writerow([i, r["band"], r["song"], r["url"]])

    by_band = defaultdict(int)
    for r in rows:
        by_band[r["band"]] += 1
    print(f"[OK] {out} — {len(rows)}곡 / {len(by_band)}밴드"
          + (f" (밴드당 캡 {args.cap})" if args.cap else " (전곡)"))
    for b in sorted(by_band, key=lambda b: -by_band[b]):
        print(f"  {b:20} {by_band[b]:>4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
