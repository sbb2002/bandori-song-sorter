"""1/2/3번 그룹 피쳐의 "유효성"(장르 구분 기여도) 추출.

이전 분석(ANOVA/η², pairwise correlation)은 각 변수를 개별적으로만 봤다. 이번에는:
  1. VIF(분산팽창지수, 직접 계산 — statsmodels 미설치)로 피쳐 간 다중공선성을 먼저 확인
     (loudness-energy처럼 서로 겹치는 신호를 가진 피쳐가 있는지)
  2. RandomForestClassifier(track_genre ~ 14개 피쳐)로 상호작용까지 반영한 분류기를 학습
  3. permutation_importance로 "이 피쳐를 섞으면 정확도가 얼마나 떨어지는가"를 측정
     (impurity 기반 중요도보다 편향이 적어 해석 신뢰도가 높음, RF 기본 feature_importances_도 비교용으로 병기)

VIF와 permutation importance를 같이 봐야 하는 이유: 두 피쳐가 서로 강하게 얽혀 있으면(예: loudness-energy)
모델이 둘 중 하나만 있어도 나머지 정보를 대신 쓸 수 있어 permutation importance가 실제 정보량보다 낮게
나올 수 있다 — 그게 "무효"가 아니라 "중복"이라는 걸 VIF로 구분한다.

환경: pandas/scikit-learn/scipy 필요(base env). 사용: python side-project/spotify-tracks-dataset/feature_validity_rf.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, top_k_accuracy_score

from distribution import cleanse_dataset

dataset = pd.read_csv(r"side-project\spotify-tracks-dataset\data\dataset.csv")
dataset = cleanse_dataset(dataset)

OUT_DIR = Path(r"side-project\spotify-tracks-dataset\fig\feature-validity")
OUT_DIR.mkdir(parents=True, exist_ok=True)

GROUP1 = ["duration_ms", "key", "mode", "loudness", "tempo", "time_signature"]
GROUP2 = ["danceability", "energy", "speechiness", "acousticness", "instrumentalness", "liveness", "valence"]
GROUP3 = ["popularity"]
FEATURES = GROUP1 + GROUP2 + GROUP3
GROUP_OF = {**{f: "1_low-level" for f in GROUP1}, **{f: "2_composite" for f in GROUP2}, **{f: "3_model" for f in GROUP3}}

TARGET = "track_genre"

X = dataset[FEATURES].copy()
y = dataset[TARGET].copy()

# --- 1. VIF (statsmodels 없이 직접 계산: VIF_i = 1 / (1 - R^2_i), R^2_i = 나머지 피쳐로 i를 회귀했을 때 결정계수)
vif_rows = []
for f in FEATURES:
    others = [c for c in FEATURES if c != f]
    reg = LinearRegression().fit(X[others], X[f])
    r2 = reg.score(X[others], X[f])
    vif = 1.0 / (1.0 - r2) if r2 < 0.999999 else np.inf
    vif_rows.append({"feature": f, "group": GROUP_OF[f], "r2_by_others": r2, "VIF": vif})
vif_df = pd.DataFrame(vif_rows).sort_values("VIF", ascending=False)
vif_df.to_csv(OUT_DIR / "vif_summary.csv", index=False)

print("=== VIF (다중공선성, 높을수록 다른 피쳐들로 설명 가능 = 중복) ===")
print(vif_df.to_string(index=False))

# --- 2. RandomForestClassifier(track_genre ~ 14 features)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = RandomForestClassifier(
    n_estimators=150, max_depth=15, min_samples_leaf=10, n_jobs=-1, random_state=42
)
clf.fit(X_train, y_train)

pred = clf.predict(X_test)
proba = clf.predict_proba(X_test)
acc = accuracy_score(y_test, pred)
top5 = top_k_accuracy_score(y_test, proba, k=5, labels=clf.classes_)

n_classes = y.nunique()
print(f"\n=== RandomForestClassifier(track_genre ~ 14 features) ===")
print(f"클래스 수(장르): {n_classes} · chance-level(1/n): {1/n_classes:.4f}")
print(f"Test accuracy: {acc:.4f} · Test top-5 accuracy: {top5:.4f}")

# --- 3. Permutation importance (test set 기준, accuracy 하락폭)
perm = permutation_importance(clf, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1, scoring="accuracy")

importance_df = pd.DataFrame({
    "feature": FEATURES,
    "group": [GROUP_OF[f] for f in FEATURES],
    "perm_importance_mean": perm.importances_mean,
    "perm_importance_std": perm.importances_std,
    "rf_impurity_importance": clf.feature_importances_,
}).sort_values("perm_importance_mean", ascending=False)

importance_df.to_csv(OUT_DIR / "feature_importance_summary.csv", index=False)

print("\n=== Permutation importance (test accuracy 하락폭, 내림차순) ===")
print(importance_df.to_string(index=False))

with open(OUT_DIR / "run_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"n_classes={n_classes}\nchance_level={1/n_classes:.4f}\n")
    f.write(f"test_accuracy={acc:.4f}\ntest_top5_accuracy={top5:.4f}\n")
    f.write(f"n_train={len(X_train)}\nn_test={len(X_test)}\n")

print(f"\n[저장] {OUT_DIR / 'vif_summary.csv'}")
print(f"[저장] {OUT_DIR / 'feature_importance_summary.csv'}")
print(f"[저장] {OUT_DIR / 'run_summary.txt'}")
