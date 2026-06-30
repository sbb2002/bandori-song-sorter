"""wordcloud/*.yaml → 키워드 2D 임베딩 좌표 (cluster/keywords_2d.json).

HANDOFF #2 — 키워드 의미공간 2D 클러스터의 데이터 파이프라인.
각 **고유 키워드(jp 원문)** 를 다국어 문장임베딩(sentence-transformers)으로 벡터화한 뒤
UMAP 으로 2D 투영한다. 점 1개 = 키워드 1개(곡 아님).

입력은 워드클라우드 yaml(밴드 단위 집계)뿐이라 **가사 원문은 불필요**.
출력 keywords_2d.json 스키마:
    {
      "model": "...", "generated": "YYYY-MM-DD",
      "bands": [밴드 stem ...],
      "keywords": [
        {jp, ko, x, y, total, bands:{band: weight}, senti}
      ]
    }
  - x/y: UMAP 2D 좌표(0~100 정규화).
  - total: 전 밴드 빈도 합(점 크기). bands: 밴드별 빈도(공유어=다중 밴드 → 아이콘/하이라이트).
  - senti: senti_lexicon.yaml 룩업(표시텍스트 ko‖jp 기준, 미등재=0=중립).

사용:
    python -m pip install -r tools/cluster/requirements.txt
    python tools/cluster/build_embeddings.py
    python tools/cluster/build_embeddings.py --model distiluse-base-multilingual-cased-v2
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import sys
from pathlib import Path

import yaml

try:                                    # Windows 콘솔(cp949) 유니코드 출력 보호
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WC_DIR = "wordcloud"
SENTI_PATH = "tools/wordcloud/senti_lexicon.yaml"
OUT_PATH = "cluster/keywords_2d.json"
DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def load_keywords(wc_dir: str) -> dict[str, dict]:
    """wordcloud/*.yaml → {jp: {jp, ko, bands:{band:weight}, total}}.

    같은 jp가 여러 밴드에 등장하면 한 점으로 합치고 밴드별 빈도를 모은다(공유어).
    ko는 밴드마다 다를 수 있어 최다 빈도 밴드의 표기를 대표로 채택.
    """
    kw: dict[str, dict] = {}
    ko_votes: dict[str, dict[str, int]] = {}
    for f in sorted(glob.glob(os.path.join(wc_dir, "*.yaml"))):
        doc = yaml.safe_load(open(f, encoding="utf-8"))
        if not doc or not doc.get("keywords"):
            continue
        band = doc.get("band") or Path(f).stem
        for k in doc["keywords"]:
            jp = k.get("jp")
            if not jp:
                continue
            ko = (k.get("ko") or "").strip()
            w = k.get("weight", 1)
            e = kw.setdefault(jp, {"jp": jp, "ko": "", "bands": {}, "total": 0})
            e["bands"][band] = e["bands"].get(band, 0) + w
            e["total"] += w
            if ko:                              # ko 표기 투표(빈도 가중) → 대표 1개 선정
                ko_votes.setdefault(jp, {})
                ko_votes[jp][ko] = ko_votes[jp].get(ko, 0) + w
    for jp, e in kw.items():
        votes = ko_votes.get(jp)
        e["ko"] = max(votes, key=votes.get) if votes else ""
    return kw


def load_senti(path: str) -> dict[str, int]:
    if not os.path.exists(path):
        return {}
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    return (doc or {}).get("words", {}) or {}


def embed_2d(texts: list[str], model_name: str, seed: int):
    """텍스트 리스트 → UMAP 2D 좌표(np.ndarray, shape [N,2])."""
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import umap

    model = SentenceTransformer(model_name)
    vecs = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    n = len(texts)
    # 표본이 적을 때 n_neighbors 가 표본수를 넘으면 UMAP 오류 → 상한 보정.
    n_neighbors = max(2, min(15, n - 1))
    reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors, min_dist=0.1,
                        metric="cosine", random_state=seed)
    return np.asarray(reducer.fit_transform(vecs))


def normalize_xy(xy):
    """좌표를 0~100 으로 정규화(ECharts 축 편의)."""
    import numpy as np
    mn, mx = xy.min(0), xy.max(0)
    span = np.where(mx - mn == 0, 1, mx - mn)
    return (xy - mn) / span * 100


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL, help="sentence-transformers 모델명")
    ap.add_argument("--seed", type=int, default=42, help="UMAP random_state(재현성)")
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args(argv)

    kw = load_keywords(WC_DIR)
    if not kw:
        print("키워드 없음 — wordcloud/*.yaml 확인", file=sys.stderr)
        return 1
    senti = load_senti(SENTI_PATH)

    items = list(kw.values())
    for e in items:
        text = e["ko"] or e["jp"]
        e["senti"] = senti.get(text, 0)

    texts = [e["jp"] for e in items]            # 일본어 원문으로 임베딩(번역 손실 회피)
    print(f"키워드 {len(texts)}개 임베딩 → UMAP 2D …")
    xy = normalize_xy(embed_2d(texts, args.model, args.seed))
    for e, (x, y) in zip(items, xy):
        e["x"] = round(float(x), 2)
        e["y"] = round(float(y), 2)

    items.sort(key=lambda e: e["total"], reverse=True)   # 큰 점 먼저(라벨 우선순위)
    bands = sorted({b for e in items for b in e["bands"]})
    doc = {
        "model": args.model,
        "generated": _dt.date.today().isoformat(),
        "bands": bands,
        "keywords": items,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[OK] {args.out} — 키워드 {len(items)}개 / 밴드 {len(bands)} / 모델 {args.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
