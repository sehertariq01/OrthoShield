import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

FEATURES_CSV = "ml_features.csv"
MODEL_OUTPUT = "isolation_forest_model.pkl"
THRESHOLD_OUTPUT = "anomaly_threshold.txt"

FEATURE_COLUMNS = ["file_size", "entropy", "total_tags", "completeness_ratio", "pixel_header_ratio"]


def main():
    df = pd.read_csv(FEATURES_CSV)
    X = df[FEATURE_COLUMNS].values

    print(f"Training on {len(X)} clean samples with {len(FEATURE_COLUMNS)} features...")

    model = IsolationForest(
        n_estimators=200,       # more trees = more stable scores
        max_samples=64,         # smaller subsamples = shallower trees = more sensitive to outliers
        contamination=0.05,
        random_state=42
    )
    model.fit(X)

    scores = model.decision_function(X)

    # Use the 5th percentile of training scores as the anomaly threshold,
    # rather than relying solely on the default contamination-based label.
    threshold = np.percentile(scores, 5)

    n_flagged = np.sum(scores < threshold)
    print(f"\nOn the training set itself: {n_flagged}/{len(X)} flagged as anomalies")
    print(f"Score range: min={scores.min():.4f}, max={scores.max():.4f}, mean={scores.mean():.4f}")
    print(f"Anomaly threshold (5th percentile): {threshold:.4f}")

    joblib.dump(model, MODEL_OUTPUT)
    with open(THRESHOLD_OUTPUT, "w") as f:
        f.write(str(threshold))

    # ============================================================
    # NEW CODE — Save entropy statistics separately for a
    # univariate safety-net check (added just below)
    # ============================================================
    entropy_mean = df["entropy"].mean()
    entropy_std = df["entropy"].std()
    entropy_max = df["entropy"].max()

    with open("entropy_stats.txt", "w") as f:
        f.write(f"{entropy_mean},{entropy_std},{entropy_max}")

    print(f"Entropy stats saved: mean={entropy_mean:.4f}, std={entropy_std:.4f}, max={entropy_max:.4f}")
    # ============================================================
    # END NEW CODE
    # ============================================================

    print(f"\nModel saved to: {MODEL_OUTPUT}")
    print(f"Threshold saved to: {THRESHOLD_OUTPUT}")


if __name__ == "__main__":
    main()
    