"""cluster/songs_top10.csv → 밴드 음원 지도 (cluster/audio_map.json).

HANDOFF #2 후속 — 가사(키워드/문장)로는 밴드가 안 갈렸으나(silhouette≈0),
음악적 특징으로 **밴드 단위** 집계 시 밴드가 구별됨(LOO 최근접-중심 ~61%).
이 스크립트는 TOP10×10 곡의 음원을 특징 벡터화한 뒤,
밴드 중심점 + 곡 좌표를 한 2D 좌표계로 투영해 산점도용 JSON을 만든다.

좌표: 밴드 중심점(고차원)에 PCA(2)를 fit → 곡·중심점을 같은 변환으로 투영.
      (밴드 간 분산 최대화 축 → 중심점은 또렷이 분리, 곡은 그 주위로 흩어짐.)
정직성 지표(LOO 최근접-중심 분류 정확도)는 json.metrics 에 함께 보존·표기.

입력: cluster/songs_top10.csv (idx,band,song,url)  ← 커밋된 매니페스트
음원: cluster/audio_cache/{band}__{idx:03d}.wav     ← gitignore(저작물, 로컬)
       없으면 yt-dlp 로 45~105s(60s) 구간을 16kHz mono 로 추출.
출력: cluster/audio_map.json
       {generated, backend, bands, songs:[{band,song,x,y}],
        centroids:[{band,x,y,n}], metrics:{loo_acc,knn_ratio,silhouette}}

사용:
    python -m pip install -r tools/cluster/requirements-audio.txt
    python tools/cluster/build_audio_map.py            # backend=librosa(기본)
    python tools/cluster/build_audio_map.py --no-download   # 캐시만 사용
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MANIFEST = "cluster/songs_top10.csv"
CACHE = Path("cluster/audio_cache")
OUT = "cluster/audio_map.json"
SECTION = "*45-105"          # 추출 구간(곡당 60초)
CACHE_SR = 48000             # 캐시 음원 샘플레이트(CLAP=48k 필요). librosa는 내부 16k 로드.
LIBROSA_SR = 16000           # librosa 특징 추출용(고역 적음, 통계 직접). CLAP은 48k 네이티브.


# ── 음원 확보 ────────────────────────────────────────────────
def _ffmpeg_location() -> list[str]:
    """PATH ffmpeg 우선, 없으면 imageio-ffmpeg 바이너리를 ffmpeg.exe 로 복사."""
    if shutil.which("ffmpeg"):
        return []
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    bindir = CACHE.parent / "_ffbin"
    bindir.mkdir(parents=True, exist_ok=True)
    tgt = bindir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not tgt.exists():
        shutil.copy(exe, tgt)
    return ["--ffmpeg-location", str(bindir)]


def ensure_audio(rows: list[dict], download: bool) -> list[str]:
    """캐시에 없는 곡을 yt-dlp 로 받는다. 실패/누락 곡 idx 리스트를 반환."""
    CACHE.mkdir(parents=True, exist_ok=True)
    ffloc = _ffmpeg_location() if download else []
    missing = []
    for r in rows:
        out = CACHE / f"{r['band']}__{int(r['idx']):03d}.wav"
        if out.exists() and out.stat().st_size > 1000:
            continue
        if not download:
            missing.append(r["idx"]); continue
        cmd = [sys.executable, "-m", "yt_dlp", "-q", "--no-warnings",
               "-f", "bestaudio/best", "--download-sections", SECTION,
               "-x", "--audio-format", "wav",
               "--postprocessor-args", f"ffmpeg:-ar {CACHE_SR} -ac 1",
               *ffloc, "-o", str(CACHE / (out.stem + ".%(ext)s")), r["url"]]
        subprocess.run(cmd, capture_output=True, text=True)
        if not (out.exists() and out.stat().st_size > 1000):
            missing.append(r["idx"]); print(f"  [miss] {out.stem}")
    return missing


# ── 특징 백엔드(교체식) ───────────────────────────────────────
def feat_librosa(path: str) -> np.ndarray | None:
    """librosa 수제 음악 특징 ~71차원(MFCC·크로마·스펙트럼·템포·에너지)."""
    import librosa
    try:
        y, sr = librosa.load(path, sr=LIBROSA_SR, mono=True)
    except Exception:
        return None
    if len(y) < sr:
        return None
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    roll = librosa.feature.spectral_rolloff(y=y, sr=sr)
    flat = librosa.feature.spectral_flatness(y=y)
    zcr = librosa.feature.zero_crossing_rate(y)
    rms = librosa.feature.rms(y=y)
    tempo = float(np.atleast_1d(librosa.beat.tempo(y=y, sr=sr))[0])
    return np.concatenate([
        mfcc.mean(1), mfcc.std(1), chroma.mean(1), contrast.mean(1),
        [cent.mean(), cent.std(), bw.mean(), bw.std(), roll.mean(), roll.std(),
         flat.mean(), zcr.mean(), zcr.std(), rms.mean(), rms.std(), tempo]]).astype(float)


_clap: dict = {}


def feat_clap(path: str) -> np.ndarray | None:
    """LAION-CLAP 음악 임베딩 512차원(HuggingFace transformers 내장, 48kHz).

    transformers 5.x: get_audio_features → BaseModelOutputWithPooling.pooler_output(512d).
    """
    import librosa
    import torch
    from transformers import ClapModel, ClapFeatureExtractor
    if "model" not in _clap:
        name = "laion/clap-htsat-unfused"
        _clap["model"] = ClapModel.from_pretrained(name).eval()
        _clap["fe"] = ClapFeatureExtractor.from_pretrained(name)
    try:
        y, _ = librosa.load(path, sr=48000, mono=True)
    except Exception:
        return None
    if len(y) < 4800:
        return None
    inp = _clap["fe"](y, sampling_rate=48000, return_tensors="pt")
    with torch.no_grad():
        out = _clap["model"].get_audio_features(**inp)
    return out.pooler_output[0].cpu().numpy().astype(float)


BACKENDS = {"librosa": feat_librosa, "clap": feat_clap}


# ── 좌표·지표 ────────────────────────────────────────────────
def project(X: np.ndarray, labels: np.ndarray, bands: list[str]):
    """밴드 중심점에 PCA(2) fit → 곡·중심점을 같은 2D 로 투영.

    좌표계 원점(0,0) = 곡 전체 평균(='평균적 소리'). 대칭 스케일로 ±50 범위.
    """
    from sklearn.decomposition import PCA
    cent = np.array([X[labels == bi].mean(0) for bi in range(len(bands))])
    pca = PCA(n_components=2).fit(cent)
    sx = pca.transform(X)
    cx = pca.transform(cent)
    origin = sx.mean(0)                         # 곡 평균을 원점으로
    sx = sx - origin; cx = cx - origin
    # 이상치가 전체를 압축(뭉침)하지 않게 95퍼센타일로 스케일 후 ±60 클립
    scale = float(np.percentile(np.abs(np.vstack([sx, cx])), 95)) or 1.0
    clip = lambda a: np.clip(a / scale * 50, -60, 60)
    return clip(sx), clip(cx)


# 해석가능 음향특징(feat_librosa 벡터 인덱스). 축 의미 라벨링용.
AXIS_FEATURES = [
    ("tempo", 70, "빠름", "느림"),
    ("brightness", 59, "밝음", "어두움"),       # 스펙트럼 중심(고역 무게)
    ("energy", 68, "강함", "여림"),             # RMS(음압)
    ("rolloff", 63, "고음 풍부", "저음 위주"),
    ("zcr", 66, "거친 음색", "매끄러운 음색"),
]


def axis_labels(feats_raw, sxy) -> dict:
    """각 축(x,y)이 어떤 해석가능 특징과 가장 상관되는지 → +/− 방향 라벨.

    PCA 축은 추상적이므로, 곡 좌표와 명명된 음향특징의 피어슨 상관으로 의미 부여.
    백엔드가 librosa 일 때만 유효(인덱스 고정).
    """
    F = np.asarray(feats_raw, dtype=float)
    used: set = set(); res: dict = {}
    for ax, key in ((0, "x"), (1, "y")):
        coord = sxy[:, ax]
        best = None
        for name, idx, pos, neg in AXIS_FEATURES:
            if name in used or idx >= F.shape[1]:
                continue
            col = F[:, idx]
            if col.std() == 0:
                continue
            r = float(np.corrcoef(coord, col)[0, 1])
            if best is None or abs(r) > abs(best[0]):
                best = (r, name, pos, neg)
        if best is None:
            continue
        r, name, pos, neg = best; used.add(name)
        res[key] = {"feature": name, "r": round(r, 2),
                    "pos": pos if r >= 0 else neg, "neg": neg if r >= 0 else pos}
    return res


def metrics(X: np.ndarray, labels: np.ndarray, bands: list[str], K=10) -> dict:
    """LOO 최근접-중심 정확도 + kNN 같은-밴드 배율 + silhouette."""
    from sklearn.neighbors import NearestNeighbors
    from sklearn.metrics import silhouette_score
    n = len(X)
    # LOO 최근접-중심
    correct = 0
    for i in range(n):
        cents, bs = [], []
        for bi in range(len(bands)):
            idx = [j for j in range(n) if labels[j] == bi and j != i]
            if idx:
                cents.append(X[idx].mean(0)); bs.append(bi)
        d = np.linalg.norm(np.array(cents) - X[i], axis=1)
        if bs[int(d.argmin())] == labels[i]:
            correct += 1
    loo = correct / n
    # kNN 같은-밴드 배율
    nn = NearestNeighbors(n_neighbors=K + 1).fit(X)
    _, nbr = nn.kneighbors(X)
    same = sum(1 for i in range(n) for j in nbr[i, 1:] if labels[j] == labels[i])
    knn = same / (n * K)
    from collections import Counter
    cnt = Counter(labels.tolist())
    chance = sum((v / n) ** 2 for v in cnt.values())
    sil = float(silhouette_score(X, labels)) if len(bands) > 1 else 0.0
    return {"loo_acc": round(loo, 3), "knn_ratio": round(knn / chance, 2),
            "knn_same": round(knn, 3), "chance": round(chance, 3),
            "silhouette": round(sil, 3), "k": K}


def clap_similar(paths: list[str], topn: int = 6) -> list[list[int]]:
    """CLAP 임베딩 코사인으로 곡별 최근접 topn 인덱스(자기 제외).

    옵션3 유사곡 탐색용. 지도 좌표는 librosa지만 '소리·무드 유사'는 CLAP이 우수
    (docs/report/cluster_audio_clap.md). 추출 실패 곡은 빈 리스트.
    """
    vecs = [feat_clap(p) for p in paths]
    valid = [i for i, v in enumerate(vecs) if v is not None]
    M = np.array([vecs[i] for i in valid], dtype=float)
    M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    sim = M @ M.T
    np.fill_diagonal(sim, -9.0)
    out: list[list[int]] = [[] for _ in vecs]
    for r, i in enumerate(valid):
        order = np.argsort(sim[r])[::-1][:topn]
        out[i] = [valid[j] for j in order]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="librosa", choices=list(BACKENDS))
    ap.add_argument("--sim", default="clap", choices=["clap", "none"],
                    help="곡별 유사곡(CLAP 코사인) 계산 여부. 옵션3용. none=생략(빠름).")
    ap.add_argument("--no-download", action="store_true", help="캐시만 사용(다운로드 생략)")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
    print(f"매니페스트 {len(rows)}곡 · backend={args.backend}")
    missing = ensure_audio(rows, download=not args.no_download)
    if missing:
        print(f"음원 누락 {len(missing)}곡(지역락/비공개 추정) → 제외")

    extract = BACKENDS[args.backend]
    from sklearn.preprocessing import StandardScaler
    feats, keys, paths = [], [], []
    for r in rows:
        p = CACHE / f"{r['band']}__{int(r['idx']):03d}.wav"
        if not p.exists():
            continue
        v = extract(str(p))
        if v is None:
            continue
        feats.append(v); keys.append((r["band"], r["song"])); paths.append(str(p))
    X = StandardScaler().fit_transform(np.array(feats))
    bands = sorted({b for b, _ in keys})
    labels = np.array([bands.index(b) for b, _ in keys])
    print(f"특징 추출 {len(keys)}곡 / {X.shape[1]}차원 / {len(bands)}밴드")

    m = metrics(X, labels, bands)
    print(f"LOO 정확도 {m['loo_acc']*100:.0f}% · kNN {m['knn_ratio']}x · "
          f"silhouette {m['silhouette']:+.3f}")
    sxy, cxy = project(X, labels, bands)
    axes = axis_labels(feats, sxy) if args.backend == "librosa" else {}
    if axes:
        print("축 의미: " + " · ".join(
            f"{k}축 −{v['neg']}↔+{v['pos']}({v['feature']} r={v['r']})" for k, v in axes.items()))

    sims = None
    if args.sim == "clap":
        print("CLAP 유사곡 계산 …")
        sims = clap_similar(paths)
    songs = [{"band": k[0], "song": k[1],
              "x": round(float(sxy[i][0]), 2), "y": round(float(sxy[i][1]), 2),
              **({"sim": sims[i]} if sims else {})}
             for i, k in enumerate(keys)]
    cents = [{"band": b, "n": int((labels == bi).sum()),
              "x": round(float(cxy[bi][0]), 2), "y": round(float(cxy[bi][1]), 2)}
             for bi, b in enumerate(bands)]
    doc = {"generated": _dt.date.today().isoformat(), "backend": args.backend,
           "sim_backend": "clap" if sims else None, "axes": axes,
           "bands": bands, "songs": songs, "centroids": cents, "metrics": m}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(doc, open(args.out, "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"))
    print(f"[OK] {args.out} — 곡 {len(songs)} / 밴드 {len(bands)} / backend {args.backend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
