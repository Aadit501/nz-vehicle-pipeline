"""
Advanced Anomaly Detection
Detects anomalies at the individual vehicle level using:
  1. Multivariate Isolation Forest on numeric features
  2. Local Outlier Factor (LOF) for density-based detection
  3. Rule-based expert flags
  4. Fuel consumption vs body-type peer comparison
"""
import sqlite3
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from scipy.stats import zscore

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

NUMERIC_FEATURES = [
    "fleet_age", "reg_lag", "cc_rating", "gross_vehicle_mass",
    "number_of_seats", "power_rating", "fc_combined",
]

def run_advanced_anomaly():
    os.makedirs(OUT_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM engineered_vehicles", conn)
    conn.close()

    print(f"  Loaded {len(df):,} rows for anomaly detection …")

    #Prepare numeric matrix
    feat_df = df[NUMERIC_FEATURES].fillna(0).clip(lower=0)
    scaler  = StandardScaler()
    X       = scaler.fit_transform(feat_df)

    # 1. Isolation Forest
    print("  Running Isolation Forest …")
    iso = IsolationForest(n_estimators=200, contamination=0.03, random_state=42, n_jobs=-1)
    df["anomaly_iforest"] = (iso.fit_predict(X) == -1).astype(int)
    df["anomaly_iforest_score"] = -iso.decision_function(X)   # higher = more anomalous

    # 2. Local Outlier Factor
    print("  Running Local Outlier Factor …")
    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.03, n_jobs=-1)
    df["anomaly_lof"] = (lof.fit_predict(X) == -1).astype(int)

    # 3. Rule-based expert flags
    print("  Applying rule-based flags …")

    df["rule_extreme_age"]    = (df["fleet_age"] > 80).astype(int)
    df["rule_huge_reg_lag"]   = (df["reg_lag"] > 20).astype(int)
    df["rule_ev_high_cc"]     = ((df["is_ev"] == 1) & (df["cc_rating"] > 500)).astype(int)
    df["rule_high_seats_car"] = (
        (df["body_type"].isin(["STATION WAGON","SALOON","HATCHBACK"])) &
        (df["number_of_seats"] > 9)
    ).astype(int)
    df["rule_negative_lag"]   = (df["reg_lag"] < 0).astype(int)
    df["rule_fuel_extreme"]   = (
        (df["fc_combined"] > 25) & (df["fc_combined"] > 0)
    ).astype(int)

    # 4. Fuel consumption peer z-score
    print("  Computing peer-group fuel consumption z-scores …")
    has_fc = df["fc_combined"] > 0
    df["fc_peer_zscore"] = np.nan

    for body in df.loc[has_fc, "body_type"].unique():
        mask = has_fc & (df["body_type"] == body)
        if mask.sum() < 5:
            continue
        z = zscore(df.loc[mask, "fc_combined"])
        df.loc[mask, "fc_peer_zscore"] = z

    df["anomaly_fc_peer"] = (df["fc_peer_zscore"].abs() > 3).fillna(False).astype(int)

    # 5. Composite anomaly flag
    rule_cols = [c for c in df.columns if c.startswith("rule_")]
    df["anomaly_composite"] = (
        df["anomaly_iforest"] |
        df["anomaly_lof"]     |
        df["anomaly_fc_peer"] |
        (df[rule_cols].sum(axis=1) >= 2)   # at least 2 rules triggered
    ).astype(int)

    # Save anomaly rows to CSV
    anomaly_df = df[df["anomaly_composite"] == 1].copy()
    # Sort by anomaly score descending
    anomaly_df = anomaly_df.sort_values("anomaly_iforest_score", ascending=False)
    anomaly_df.to_csv(os.path.join(OUT_PATH, "advanced_anomalies.csv"), index=False)

    # Update DB table 
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS engineered_vehicles")
    df.to_sql("engineered_vehicles", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    # Summary
    print(f"✓ advanced_anomaly_detection complete")
    print(f"  Total rows           : {len(df):,}")
    print(f"  IForest anomalies    : {df['anomaly_iforest'].sum():,}")
    print(f"  LOF anomalies        : {df['anomaly_lof'].sum():,}")
    print(f"  FC peer anomalies    : {df['anomaly_fc_peer'].sum():,}")
    print(f"  Composite anomalies  : {df['anomaly_composite'].sum():,}")

    # Rule breakdown
    for col in rule_cols:
        print(f"  {col:<30}: {int(df[col].sum()):,}")

    return anomaly_df

if __name__ == "__main__":
    run_advanced_anomaly()
