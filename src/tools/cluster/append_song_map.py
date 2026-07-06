"""신곡 1곡을 emoi-map(audio_map.json)에 **증분 append** — 동결 norm 기반 (pipeline §5).

전곡 빌드(build_perceptual_map.py)는 모집단 mean/std 로 z-score 하므로 매번 전체 캐시가
필요하다. 여기서는 그 빌드가 audio_map.json 에 **동결 저장한 `norm`**(x/y 각각 mean·std·k·
clip·shift + overrides)을 재사용해, 신곡 1곡의 raw contrast/mode 만 뽑아 **재다운로드·재계산
없이** 좌표를 얹는다. 좌표를 append 하면 클라이언트가 그대로 읽는 **centroid(baked)**는 안
움직이므로, 해당 밴드 centroid 를 여기서 재계산한다(focus/재생 HUD 가 이 값을 읽음).

⚠️ idx 는 onset/wav 파일명(<band>__<idx:03d>)에 baked 된 **전역 인덱스**다. 신곡은 반드시
   songs_full.csv 끝에 **idx=max+1** 로 append 되어야 하며(build_manifest.py 재실행은 전역
   재번호 → 기존 onset 파일명 붕괴), 이 스크립트는 그 idx 의 wav 를 읽는다.

사용:
  python src/tools/cluster/append_song_map.py --band afterglow --idx 660 \
      --song "새 곡" --url https://youtu.be/xxxxxxxxxxx
  # --song/--url 생략 시 songs_full.csv 에서 (band,idx) 로 조회
  python src/tools/cluster/append_song_map.py --band afterglow --idx 0 --dry-run
  # 기존 곡으로 동결 norm 공식이 baked 좌표를 재현하는지 검증
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# feats(): 신곡 raw contrast/mode/bpm 추출(build_perceptual_map 와 동일 로직 재사용)
sys.path.insert(0, str(Path(__file__).parent))
from build_perceptual_map import feats  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]          # src/tools/cluster/<file> → repo root
CLUSTER = ROOT / "src" / "content" / "cluster"
DEFAULT_MAP = CLUSTER / "audio_map.json"
DEFAULT_MANIFEST = CLUSTER / "songs_full.csv"


def _apply_norm(v: float, p: dict) -> float:
    """동결 파라미터로 z-score·스케일·clip·shift. build_perceptual_map.zscale 와 동일 공식."""
    std = p["std"] or 1.0
    z = (v - p["mean"]) / std * p["k"]
    z = max(-p["clip"], min(p["clip"], z))
    return z + p.get("shift", 0.0)


def _norm_input(feat: dict, which: str) -> float:
    """norm.x/y 의 input 라벨('neg_contrast'|'contrast'|'mode')을 raw feature 로 매핑."""
    if which == "neg_contrast":
        return -feat["contrast"]
    if which == "contrast":
        return feat["contrast"]
    if which == "mode":
        return feat["mode"]
    raise ValueError(f"알 수 없는 norm input: {which!r}")


def compute_coords(contrast: float, mode: float, norm: dict) -> tuple[float, float]:
    """raw (contrast, mode) → 동결 norm 좌표 (x, y). override(밴드 큐레이션)는 호출부에서."""
    feat = {"contrast": contrast, "mode": mode}
    x = _apply_norm(_norm_input(feat, norm["x"].get("input", "neg_contrast")), norm["x"])
    y = _apply_norm(_norm_input(feat, norm["y"].get("input", "mode")), norm["y"])
    return x, y


# ── 오케스트레이터용 granular API (feats 1회 → 펄스 → 맵 반영 단계 분리) ──

def load_map(map_path: Path = DEFAULT_MAP) -> dict:
    doc = json.loads(Path(map_path).read_text(encoding="utf-8"))
    if not doc.get("norm"):
        raise RuntimeError(f"{map_path} 에 동결 norm 없음 — 전곡 빌드 산출물이 아님(pipeline §5).")
    return doc


def write_map(doc: dict, map_path: Path = DEFAULT_MAP) -> None:
    """커밋된 pretty-print(4-space, ensure_ascii=False) 유지 → diff = 신곡 + centroid 만."""
    Path(map_path).write_text(json.dumps(doc, ensure_ascii=False, indent=4), encoding="utf-8")


def feats_of(band: str, idx: int, cache: str = "audio_full") -> tuple[float, float, float]:
    """신곡 wav → (contrast, mode, tempo). librosa 1회 추출."""
    wav = CLUSTER / cache / f"{band}__{idx:03d}.wav"
    if not wav.exists():
        raise FileNotFoundError(f"wav 없음: {wav} (fetch_audio 로 먼저 수집)")
    fv = feats(str(wav))
    if fv is None:
        raise RuntimeError(f"특징 추출 실패(길이<1s?): {wav}")
    return fv


def build_entry(band: str, song: str, url: str,
                contrast: float, mode: float, tempo: float, norm: dict) -> dict:
    """raw feature → songs[] 항목({band,song,url,x,y,bpm}). override 적용·좌표 반올림."""
    x, y = compute_coords(contrast, mode, norm)
    ov = (norm.get("overrides") or {}).get(band)
    if ov:
        x += ov.get("dx", 0.0)
        y += ov.get("dy", 0.0)
    return {"band": band, "song": song, "url": url,
            "x": round(x, 2), "y": round(y, 2), "bpm": round(tempo, 1)}


def apply_entry(doc: dict, entry: dict) -> dict:
    """songs[] append + 해당 밴드 centroid 재계산 + metrics.n 갱신. centroid dict 반환."""
    band = entry["band"]
    songs = doc.setdefault("songs", [])
    songs.append(entry)
    band_pts = [(s["x"], s["y"]) for s in songs if s["band"] == band]
    cx = round(sum(p[0] for p in band_pts) / len(band_pts), 2)
    cy = round(sum(p[1] for p in band_pts) / len(band_pts), 2)
    cents = doc.setdefault("centroids", [])
    cent = next((c for c in cents if c["band"] == band), None)
    if cent is None:
        cents.append({"band": band, "n": len(band_pts), "x": cx, "y": cy})
    else:
        cent.update(n=len(band_pts), x=cx, y=cy)
    if band not in doc.setdefault("bands", []):
        doc["bands"].append(band)
        doc["bands"].sort()
    doc.setdefault("metrics", {})["n"] = len(songs)
    return {"x": cx, "y": cy, "n": len(band_pts)}


def _lookup_manifest(band: str, idx: int, manifest: Path) -> tuple[str, str] | None:
    if not manifest.exists():
        return None
    with open(manifest, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["band"] == band and int(row["idx"]) == idx:
                return row["song"], row["url"]
    return None


def append_song(band: str, idx: int, song: str, url: str, *,
                cache: str = "audio_full", map_path: Path = DEFAULT_MAP,
                dry_run: bool = False) -> dict:
    """신곡 1곡을 audio_map.json 에 append(+centroid 재계산). 산출 좌표/centroid dict 반환.

    dry_run=True 면 계산만 하고 파일을 쓰지 않는다(검증·미리보기).
    """
    contrast, mode, tempo = feats_of(band, idx, cache)
    doc = load_map(map_path)
    entry = build_entry(band, song, url, contrast, mode, tempo, doc["norm"])
    cent = apply_entry(doc, entry)

    result = {"band": band, "idx": idx, "song": song, "url": url,
              "x": entry["x"], "y": entry["y"], "bpm": entry["bpm"],
              "contrast": round(contrast, 3), "mode": round(mode, 3),
              "centroid": cent}
    if not dry_run:
        write_map(doc, map_path)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="신곡 1곡 emoi-map 증분 append(동결 norm)")
    ap.add_argument("--band", required=True)
    ap.add_argument("--idx", type=int, required=True)
    ap.add_argument("--song", default=None, help="곡명(생략 시 songs_full.csv 조회)")
    ap.add_argument("--url", default=None, help="url(생략 시 songs_full.csv 조회)")
    ap.add_argument("--cache", default="audio_full")
    ap.add_argument("--map", default=str(DEFAULT_MAP))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--dry-run", action="store_true", help="계산만(파일 미기록)")
    a = ap.parse_args(argv)

    song, url = a.song, a.url
    if song is None or url is None:
        found = _lookup_manifest(a.band, a.idx, Path(a.manifest))
        if not found:
            print(f"‼️ songs_full.csv 에 ({a.band}, idx={a.idx}) 없음 — --song/--url 직접 지정 필요")
            return 1
        song = song or found[0]
        url = url or found[1]

    res = append_song(a.band, a.idx, song, url, cache=a.cache,
                      map_path=Path(a.map), dry_run=a.dry_run)
    tag = "[dry-run 계산만]" if a.dry_run else "[append 완료]"
    print(f"{tag} {res['band']} · {res['song']}")
    print(f"  raw   contrast={res['contrast']} mode={res['mode']} bpm={res['bpm']}")
    print(f"  좌표  x={res['x']} y={res['y']}")
    print(f"  {res['band']} centroid → x={res['centroid']['x']} y={res['centroid']['y']} "
          f"(n={res['centroid']['n']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
