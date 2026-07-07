"""src/content/cluster/songs_full.csv → 지각 축 음원맵 (cluster/audio_map.json). v3 채택본.

축 재정의 결과(docs/working/report/cluster-correlation) 채택:
  x = spectral contrast  → 거칢↔매끄러움 (검증 r=−0.81)
  y = mode_score(장/단조) → 어두움↔밝음  (검증 r=+0.51)

v2(PCA+librosa71d+LOO)와 달리 **두 지각 feature를 좌표축으로 직접** 쓴다.
PCA·f0·Demucs 불필요(믹스 스펙트럼·화성만) → 전곡 확대도 저렴.

좌표: 각 축 z-score 후 스케일. 원점(0,0)=평균 곡(평균 거칢·평균 정서).
  오른쪽=거칢 / 위=밝음. 밴드 중심=그 밴드 곡 평균.
sim(곡 유사곡): 기존 audio_map.json(CLAP)에서 (band,song) 매칭 승계(있으면).

사용: python src/tools/cluster/build_perceptual_map.py [--cache audio_cache|audio_full]
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from perceptual_features import mode_valence  # 재사용(Krumhansl 장/단조)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MANIFEST = Path("src/content/cluster/songs_full.csv")  # 전곡(660). 파일럿 top10은 legacy/ 로 이관됨.
OUT = Path("src/content/cluster/audio_map.json")
SR = 22050
X_R, Y_R = -0.81, 0.51        # 검증 상관(보고서). 표기·기록용.
# 지각 원점 보정(사용자 피드백 2026-07-01): 데이터 평균은 밝은 팝이 많아 밝게 치우침 →
# y 를 위로 올려 지각적 중립에 맞춤. RAS(라우드락, '약간 마이너')를 y≈−5 에 앵커 → +10.
# 순수 상수 가산이라 재계산 불필요. 원점(0,0)=데이터평균이 아니라 '지각적 중립 소리'.
X_SHIFT, Y_SHIFT = 0.0, 10.0

# 밴드 큐레이션 보정(★측정 아님★): feature가 지각을 못 잡는 밴드만 밴드 단위로 nudge.
# 전곡에 균일 적용 → 개별 곡의 실제 장/단조 스프레드는 보존, 밴드 위치만 이동.
# morfonica: 바이올린 음색의 '밝음'이 mode·음향 feature로 안 잡힘(곡별 mode가 −27~+29로
#   퍼져 상수 통용 불가, HPSS 선율밝기도 valence 무상관 — docs/working/report/cluster-correlation).
#   사용자 판단(밴드 B안)으로 밴드를 밝은 쪽에 배치. audio_map.json.overrides 에 투명 기록.
# millsage·ikka: n=1 밴드(곡 1개 = 대표값, 노이즈 미세척) + 축 프록시 한계가 겹쳐 좌표가 귀와
#   어긋남(작업 5, docs/idea/260708-final_comment.md). nudge 크기 = 1지각점≈18좌표(norm k=25·좌표 σ≈24,
#   r 기반 회귀기울기). ★만료 규칙: 신곡 파이프라인으로 n≥5 도달 시 재검토·제거(측정이 대체).
BAND_OVERRIDES = {
    "morfonica": {"dx": 0.0, "dy": 15.0,
                  "why": "violin 음색 밝음 미측정 → 밴드 밝기 큐레이션(측정 아님)"},
    "millsage": {"dx": -18.0, "dy": 0.0,
                 "why": "키보드 편곡의 '매끄러움'이 spectral contrast(음색 대비, 리듬 아님)로 미측정 "
                        "→ n=1 좌표 큐레이션(측정 아님, ≈1지각점). n≥5 도달 시 제거"},
    "ikka_dumb_rock": {"dx": 0.0, "dy": 18.0,
                       "why": "펑크 '경쾌함'(에너지축 energy=0.92 상위8%)이 mode(조성만)로 미측정 "
                              "→ n=1 좌표 큐레이션(측정 아님, ≈1.5지각점). n≥5 도달 시 제거"},
}


def feats(path: str):
    import librosa
    y, sr = librosa.load(path, sr=SR, mono=True)
    if len(y) < sr:
        return None
    contrast = float(librosa.feature.spectral_contrast(y=y, sr=sr).mean())
    mode = float(mode_valence(y, sr)["mode_score"])
    tempo = float(librosa.feature.tempo(y=y, sr=sr)[0])   # [실험] 펄스 주기용 BPM(옥타브 오류 가능)
    return contrast, mode, tempo


def zscale(vals, k=25.0, clip=70.0):
    """z-score 후 k 스케일·clip. 증분 append 재현(pipeline §5)용으로 mean/std/k/clip 도 반환."""
    v = np.asarray(vals, float)
    mean = float(v.mean()); std = float(v.std() or 1.0)
    scaled = np.clip((v - mean) / std * k, -clip, clip)
    return scaled, {"mean": mean, "std": std, "k": k, "clip": clip}


def carry_sim(new_songs: list[dict]) -> None:
    """기존 audio_map.json 의 CLAP sim 을 (band,song) 매칭으로 새 인덱스에 승계."""
    if not OUT.exists():
        return
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except Exception:
        return
    old_songs = old.get("songs", [])
    if not old_songs or "sim" not in (old_songs[0] or {}):
        return
    okey = [(s["band"], s["song"]) for s in old_songs]
    old_sim_keys = {okey[i]: [okey[j] for j in s.get("sim", [])]
                    for i, s in enumerate(old_songs)}
    nidx = {(s["band"], s["song"]): i for i, s in enumerate(new_songs)}
    carried = 0
    for s in new_songs:
        keys = old_sim_keys.get((s["band"], s["song"]))
        if keys:
            s["sim"] = [nidx[k] for k in keys if k in nidx]
            carried += 1
    if carried:
        print(f"sim 승계: {carried}곡 (기존 CLAP 유사곡 재사용)")


def loo_2d(P: np.ndarray, labels: np.ndarray, nb: int) -> float:
    """참고용: (x,y) 2D 최근접-중심 LOO. 지각축이라 밴드분리는 목적 아님(낮아도 정상)."""
    n = len(P); ok = 0
    for i in range(n):
        best, bd = 1e9, -1
        for b in range(nb):
            idx = [j for j in range(n) if labels[j] == b and j != i]
            if not idx:
                continue
            d = np.linalg.norm(P[idx].mean(0) - P[i])
            if d < best:
                best, bd = d, b
        ok += (bd == labels[i])
    return ok / n


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="audio_cache",
                    help="음원 캐시 폴더명(audio_cache=60s / audio_full=전곡)")
    ap.add_argument("--manifest", default=str(MANIFEST),
                    help="입력 매니페스트 CSV(band,idx,song,url). 기본 songs_full.csv(전곡 660)")
    ap.add_argument("--x-shift", type=float, default=X_SHIFT, help="x 원점 보정(거칢+)")
    ap.add_argument("--y-shift", type=float, default=Y_SHIFT, help="y 원점 보정(밝음+)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    cache = Path("src/content/cluster") / args.cache

    rows = list(csv.DictReader(open(args.manifest, encoding="utf-8")))
    recs = []
    for r in rows:
        p = cache / f"{r['band']}__{int(r['idx']):03d}.wav"
        if not p.exists():
            continue
        fv = feats(str(p))
        if fv is None:
            continue
        recs.append({"band": r["band"], "song": r["song"], "url": r["url"],
                     "contrast": fv[0], "mode": fv[1], "bpm": round(fv[2], 1)})
    print(f"특징 추출 {len(recs)}곡 (cache={args.cache})")

    X, xnorm = zscale([-r["contrast"] for r in recs]); X = X + args.x_shift  # 오른쪽=거칢(낮은 contrast)
    Y, ynorm = zscale([r["mode"] for r in recs]);      Y = Y + args.y_shift  # 위=밝음(장조)+원점보정
    xnorm.update(input="neg_contrast", shift=args.x_shift)   # 증분 재현: v=-contrast
    ynorm.update(input="mode", shift=args.y_shift)           # 증분 재현: v=mode
    for i, r in enumerate(recs):                                # 밴드 큐레이션 보정(측정 아님)
        ov = BAND_OVERRIDES.get(r["band"])
        if ov:
            X[i] += ov.get("dx", 0.0); Y[i] += ov.get("dy", 0.0)
    songs = [{"band": r["band"], "song": r["song"], "url": r["url"],
              "x": round(float(X[i]), 2), "y": round(float(Y[i]), 2), "bpm": r["bpm"]}
             for i, r in enumerate(recs)]
    carry_sim(songs)

    bands = sorted({r["band"] for r in recs})
    labels = np.array([bands.index(r["band"]) for r in recs])
    P = np.column_stack([X, Y])
    cents = []
    for bi, b in enumerate(bands):
        m = labels == bi
        cents.append({"band": b, "n": int(m.sum()),
                      "x": round(float(X[m].mean()), 2), "y": round(float(Y[m].mean()), 2)})

    axes = {
        "x": {"feature": "contrast", "r": X_R, "pos": "거칢", "neg": "매끄러움"},
        "y": {"feature": "mode", "r": Y_R, "pos": "밝음", "neg": "어두움"},
    }
    doc = {
        "generated": _dt.date.today().isoformat(), "backend": "perceptual",
        "sim_backend": "clap", "axes": axes, "bands": bands,
        "overrides": BAND_OVERRIDES,        # 큐레이션 보정(측정 아님) 투명 기록
        # 증분 append 동결 파라미터(pipeline §5): 신곡 raw contrast/mode → 이 mean/std/k/clip 로 z변환
        # → +shift(+override) 하면 재다운로드 없이 songs[] 에 얹을 수 있다. 전곡 빌드 = 마지막 튜닝·동결 순간.
        "norm": {"x": xnorm, "y": ynorm, "overrides": BAND_OVERRIDES,
                 "formula": "coord = clip((v-mean)/std*k, -clip, clip) + shift (+override.d[xy])"},
        "songs": songs, "centroids": cents,
        "metrics": {"x_feature": "contrast", "y_feature": "mode",
                    "x_r": X_R, "y_r": Y_R, "n": len(recs),
                    "x_shift": args.x_shift, "y_shift": args.y_shift,
                    "loo_acc": round(loo_2d(P, labels, len(bands)), 3), "chance": 0.1},
    }
    json.dump(doc, open(args.out, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"[OK] {args.out} — 곡 {len(songs)} / 밴드 {len(bands)} / 축 거칢×정서")
    # 밴드별 평균(정합성 육안 확인)
    print("\n밴드 중심(x=거칢+ y=밝음+):")
    for c in sorted(cents, key=lambda c: c["x"]):
        print(f"  {c['band']:18} x{c['x']:+6.1f} y{c['y']:+6.1f} ({c['n']}곡)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
