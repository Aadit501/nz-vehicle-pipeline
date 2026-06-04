"""
Time-Series & Trend Analysis
"""
import sqlite3
import os
import pandas as pd
import numpy as np

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

def run_trend_analysis():
    os.makedirs(OUT_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM engineered_vehicles", conn)
    conn.close()

    # 1. Fuel type composition over vehicle_year
    fuel_pivot = (
        df[df["vehicle_year"] >= 2000]
          .groupby(["vehicle_year", "fuel_type"])
          .size()
          .reset_index(name="count")
    )
    total_by_year = fuel_pivot.groupby("vehicle_year")["count"].transform("sum")
    fuel_pivot["share_pct"] = (fuel_pivot["count"] / total_by_year * 100).round(2)
    fuel_pivot.to_csv(os.path.join(OUT_PATH, "yearly_fuel_trends.csv"), index=False)

    # 2. EV adoption trajectory 
    ev_df = (
        df[df["reg_year"] >= 2010]
          .groupby("reg_year")
          .agg(
              total=("objectid","count"),
              ev_count=("is_ev","sum"),
              hybrid_count=("is_hybrid","sum"),
          )
          .reset_index()
    )
    ev_df["ev_share_pct"]     = (ev_df["ev_count"]     / ev_df["total"] * 100).round(2)
    ev_df["hybrid_share_pct"] = (ev_df["hybrid_count"] / ev_df["total"] * 100).round(2)
    ev_df["zero_em_pct"]      = ev_df["ev_share_pct"]

    # YoY growth
    ev_df["ev_yoy_growth"]    = ev_df["ev_count"].pct_change() * 100
    ev_df.to_csv(os.path.join(OUT_PATH, "ev_adoption.csv"), index=False)

    # 3. Monthly registration seasonality ───────────────────────────────────
    monthly = (
        df[df["reg_year"] >= 2020]
          .groupby(["reg_year", "reg_month"])
          .size()
          .reset_index(name="registrations")
    )
    monthly.to_csv(os.path.join(OUT_PATH, "monthly_registrations.csv"), index=False)

    # 4. Regional fleet composition ─────────────────────────────────────────
    regional = (
        df.groupby("region")
          .agg(
              total_vehicles=("objectid","count"),
              ev_count=("is_ev","sum"),
              hybrid_count=("is_hybrid","sum"),
              avg_fleet_age=("fleet_age","mean"),
              avg_fc=("fc_combined", lambda x: x[x > 0].mean()),
              new_count=("nz_new","sum"),
          )
          .reset_index()
    )
    regional["ev_pct"]  = (regional["ev_count"]  / regional["total_vehicles"] * 100).round(2)
    regional["new_pct"] = (regional["new_count"] / regional["total_vehicles"] * 100).round(2)
    regional["avg_fleet_age"] = regional["avg_fleet_age"].round(1)
    regional["avg_fc"]        = regional["avg_fc"].round(2)
    regional.to_csv(os.path.join(OUT_PATH, "regional_fleet.csv"), index=False)

    # 5. Top make market share (recent years) ───────────────────────────────
    top_makes = (
        df[df["reg_year"] >= 2015]
          .groupby(["reg_year","make"])
          .size()
          .reset_index(name="count")
    )
    # Keep only makes that appear in top-15 for at least one year
    top15 = (
        top_makes.groupby("reg_year")
                 .apply(lambda g: g.nlargest(15, "count"))
                 .reset_index(drop=True)
    )
    top15.to_csv(os.path.join(OUT_PATH, "make_market_share.csv"), index=False)

    # 6. Efficiency tier breakdown by year ──────────────────────────────────
    eff_df = (
        df[df["has_fuel_data"] == 1]
          .groupby(["vehicle_year","efficiency_tier"])
          .size()
          .reset_index(name="count")
    )
    eff_df.to_csv(os.path.join(OUT_PATH, "efficiency_trends.csv"), index=False)

    # 7. Body type trend ────────────────────────────────────────────────────
    body_trend = (
        df[df["reg_year"] >= 2015]
          .groupby(["reg_year","body_type"])
          .size()
          .reset_index(name="count")
    )
    # Top 8 body types
    top_bodies = df["body_type"].value_counts().head(8).index.tolist()
    body_trend = body_trend[body_trend["body_type"].isin(top_bodies)]
    body_trend.to_csv(os.path.join(OUT_PATH, "body_type_trend.csv"), index=False)

    print(f"✓ trend_analysis complete — 7 CSVs written to {OUT_PATH}")
    return {
        "fuel_years":   len(fuel_pivot),
        "ev_years":     len(ev_df),
        "regions":      len(regional),
        "top_makes":    len(top15),
    }

if __name__ == "__main__":
    run_trend_analysis()
