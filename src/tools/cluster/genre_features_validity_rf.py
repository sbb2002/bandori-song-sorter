"""로컬 285곡 프록시 피처의 "유효성"(밴드 구분 기여도) 검증 — Spotify 분석과 동일 방법론.

side-project/spotify-tracks-dataset/feature_validity_rf.py에서 쓴 방법(VIF + RandomForest +
permutation_importance)을 우리 로컬 오디오 프록시(genre-features 분석 산출물)에 그대로 적용한다.
band_anova_summary.csv(단변량 η²)만으로는 acousticness_proxy/instrumentalness_proxy/energy_proxy가
원본 신호(harmonic_ratio, voiced_frac_mix, rms 등)와 겹치는 정보인지 고유 정보인지 구분할 수 없어서,
다변량 관점(VIF로 중복도 확인 + RF permutation importance로 실제 기여도 확인)을 추가한다.

표본이 작으므로(Spotify 114,000행 대비 로컬 최대 270행) RandomForest는 처음부터 가볍게 규제한다
(Spotify 분석에서 과도한 파라미터 때문에 실행이 37분 넘게 걸린 교훈 반영).

표본수 20 미만인 밴드(pastel_palettes=8, various_artists=5, millsage=1, ikka_dumb_rock=1)는
stratified split이 불가능해 제외 — band_anova_summary.csv README에도 명시된 표본 불균형 한계.

환경: pandas/scikit-learn/scipy 필요(base env).
사용: python src/tools/cluster/genre_features_validity_rf.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "docs/working/report/genre-features/song_features_with_proxies.csv"
OUT_DIR = ROOT / "docs/working/report/genre-features"

MIN_BAND_N = 20  # stratified split·유의미한 평가를 위한 최소 표본수

df = pd.read_csv(DATA)

band_counts = df["band"].value_counts()
kept_bands = band_counts[band_counts >= MIN_BAND_N].index.tolist()
dropped = band_counts[band_counts < MIN_BAND_N]
df = df[df["band"].isin(kept_bands)].copy()

print(f"밴드 필터: n>={MIN_BAND_N} 유지 {len(kept_bands)}개 {kept_bands} (총 {len(df)}곡)")
print(f"  제외: {dict(dropped)}")

# 프록시(acousticness/instrumentalness/energy_proxy)는 아래 원본 피처의 정확한 선형결합이라
# (README 참고) 둘 다 포함하면 설계행렬이 완전 특이(rank-deficient)해져 VIF가 전부 inf로 나온다 —
# "중복"이 아니라 산술적으로 당연한 결과라 해석에 쓸모가 없다. 원본 신호처리 피처만 검증 대상으로 삼는다.
FEATURES = [
    "duration_s", "harmonic_ratio", "centroid", "rolloff", "flatness", "contrast",
    "flux", "zcr", "rms", "tempo_excerpt", "mode_score", "voiced_frac_mix",
]
TARGET = "band"

X = df[FEATURES].copy()
y = df[TARGET].copy()

# --- 1. VIF (proxy는 원본 피처의 선형결합이라 매우 높게/inf로 나올 것으로 예상 — 중복 확인용)
vif_rows = []
for f in FEATURES:
    others = [c for c in FEATURES if c != f]
    reg = LinearRegression().fit(X[others], X[f])
    r2 = reg.score(X[others], X[f])
    vif = 1.0 / (1.0 - r2) if r2 < 0.999999 else np.inf
    vif_rows.append({"feature": f, "r2_by_others": r2, "VIF": vif})
vif_df = pd.DataFrame(vif_rows).sort_values("VIF", ascending=False)
vif_df.to_csv(OUT_DIR / "feature_validity_vif.csv", index=False)

print("\n=== VIF (다중공선성) ===")
print(vif_df.to_string(index=False))

# --- 2. RandomForestClassifier(band ~ 15 features) — 표본이 작아 가볍게 규제
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

clf = RandomForestClassifier(
    n_estimators=200, max_depth=6, min_samples_leaf=5, n_jobs=-1, random_state=42
)
clf.fit(X_train, y_train)

pred = clf.predict(X_test)
acc = accuracy_score(y_test, pred)

n_classes = y.nunique()
print(f"\n=== RandomForestClassifier(band ~ {len(FEATURES)} features) ===")
print(f"클래스 수(밴드): {n_classes} · chance-level(1/n): {1/n_classes:.4f}")
print(f"n_train={len(X_train)} · n_test={len(X_test)}")
print(f"Test accuracy: {acc:.4f}")

# --- 3. Permutation importance (표본이 작아 n_repeats를 늘려 안정화)
perm = permutation_importance(clf, X_test, y_test, n_repeats=30, random_state=42, n_jobs=-1, scoring="accuracy")

importance_df = pd.DataFrame({
    "feature": FEATURES,
    "perm_importance_mean": perm.importances_mean,
    "perm_importance_std": perm.importances_std,
    "rf_impurity_importance": clf.feature_importances_,
}).sort_values("perm_importance_mean", ascending=False)

importance_df.to_csv(OUT_DIR / "feature_validity_importance.csv", index=False)

print("\n=== Permutation importance (test accuracy 하락폭, 내림차순) ===")
print(importance_df.to_string(index=False))

with open(OUT_DIR / "feature_validity_run_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"kept_bands={kept_bands}\n")
    f.write(f"dropped_bands={dict(dropped)}\n")
    f.write(f"n_classes={n_classes}\nchance_level={1/n_classes:.4f}\n")
    f.write(f"test_accuracy={acc:.4f}\n")
    f.write(f"n_train={len(X_train)}\nn_test={len(X_test)}\n")

print(f"\n[저장] {OUT_DIR / 'feature_validity_vif.csv'}")
print(f"[저장] {OUT_DIR / 'feature_validity_importance.csv'}")
print(f"[저장] {OUT_DIR / 'feature_validity_run_summary.txt'}")
