"""
Anomaly Detection (Statistical + ML)
"""
import sqlite3
import os
import pandas as pd
import numpy as np
from scipy.stats import zscore
from sklearn.ensemble import IsolationForest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

def run_anomaly_detection():
    os.makedirs(OUT_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT reg_year, fuel_type, body_type, COUNT(*) AS count
        FROM cleaned_vehicles
        GROUP BY reg_year, fuel_type, body_type
    """, conn)
    conn.close()

    # Z-score
    df["z_score"] = zscore(df["count"])
    df["stat_anomaly"] = df["z_score"].abs() > 3

    # Isolation Forest
    iso = IsolationForest(contamination=0.05, random_state=42)
    df["ml_anomaly"] = iso.fit_predict(df[["count"]]) == -1

    df["anomaly"] = df["stat_anomaly"] | df["ml_anomaly"]

    anomalies = df[df["anomaly"]].copy()
    anomalies.to_csv(os.path.join(OUT_PATH, "anomalies.csv"), index=False)

    # Body-type bar chart
    top_bodies = (
        df.groupby("body_type")["count"].sum()
          .sort_values(ascending=False)
          .head(15)
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    top_bodies.plot(kind="bar", ax=ax, color="steelblue")
    ax.set_title("Top 15 Body Types by Registration Count")
    ax.set_xlabel("Body Type")
    ax.set_ylabel("Count")
    plt.tight_layout()
    fig.savefig(os.path.join(OUT_PATH, "body_type_distribution.png"), dpi=150)
    plt.close()

    print(f"✓ anomaly_detection complete")
    print(f"  Total grouped rows : {len(df):,}")
    print(f"  Anomalies found    : {len(anomalies):,}")
    return anomalies

if __name__ == "__main__":
    run_anomaly_detection()
