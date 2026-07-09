"""[실험] 음원맵 재생 펄스 — 전곡 배치 파이프라인.

songs_full.csv 순회: audio_full 의 각 곡 →(demucs 드럼분리)→ audio_drums
→(beat 그리드)→ onsets/<band>__<idx>.json. 멱등(이미 있으면 스킵).

⚠️ demucs 는 CPU 곡당 ~45s → 전곡(수백 곡)은 수 시간. 오디오 수집 완료 후 무인 배치 권장.
⚠️ 전곡이면 onsets 총량이 커진다 → index.html 인라인(build.py) 대신 **곡별 lazy fetch**
   로 전환 필요(side-project/emoi-map-pulse 참조). 지금 파일럿(7곡)은 인라인.

사용: python src/tools/cluster/build_pulse_all.py [--limit N] [--force]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import separate_drums          # noqa: E402
import build_beat_track        # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = Path("src/content/cluster")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=str(BASE / "songs_full.csv"))
    ap.add_argument("--cache", default="audio_full")
    ap.add_argument("--drums", default="audio_drums")
    ap.add_argument("--limit", type=int, default=0, help="처리할 최대 곡 수(0=무제한)")
    ap.add_argument("--force", action="store_true", help="기존 onsets 도 재생성")
    a = ap.parse_args(argv)

    rows = list(csv.DictReader(open(a.manifest, encoding="utf-8")))
    onsets = BASE / "onsets"
    onsets.mkdir(exist_ok=True)
    done = skip = miss = 0

    for r in rows:
        band, idx = r["band"], int(r["idx"])
        full = BASE / a.cache / f"{band}__{idx:03d}.wav"
        if not full.exists():                      # 아직 수집 안 된 곡
            miss += 1
            continue
        out = onsets / f"{band}__{idx:03d}.json"
        if out.exists() and not a.force:
            skip += 1
            continue
        drums = BASE / a.drums / f"{band}__{idx:03d}.wav"
        if not drums.exists():
            separate_drums.separate(str(full), str(drums))        # demucs 드럼 분리
        doc = build_beat_track.build(str(drums))                  # beat 그리드 트랙
        json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        done += 1
        print(f"[{done}] {band}__{idx:03d}  tempo≈{doc['tempo']}  박 {doc['levels'][0]['n']}개")
        if a.limit and done >= a.limit:
            break

    print(f"\n완료 {done} · 스킵(기존) {skip} · 미수집 {miss} / 매니페스트 {len(rows)}곡")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
