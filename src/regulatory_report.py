"""
Regulatory Insights Report
"""
import sqlite3
import os
import json
import pandas as pd
import numpy as np

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

def run_regulatory_report():
    os.makedirs(OUT_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM engineered_vehicles", conn)
    conn.close()

    n     = len(df)
    report = {}

    # 1. National fleet overview 
    report["fleet_overview"] = {
        "total_registered_vehicles": n,
        "snapshot_year": 2025,
        "unique_makes":  int(df["make"].nunique()),
        "unique_models": int(df["model"].nunique()),
        "registration_span": f"{int(df['reg_year'].min())} – {int(df['reg_year'].max())}",
    }

    # 2. Fuel/emissions profile
    fuel_counts = df["fuel_type"].value_counts()
    fuel_pct    = (fuel_counts / n * 100).round(2)

    avg_fc_by_fuel = (
        df[df["fc_combined"] > 0]
          .groupby("fuel_type")["fc_combined"]
          .mean()
          .round(2)
          .to_dict()
    )

    report["emissions_profile"] = {
        "fuel_type_counts":    fuel_counts.to_dict(),
        "fuel_type_pct":       fuel_pct.to_dict(),
        "avg_fuel_consumption_by_fuel": avg_fc_by_fuel,
        "zero_emission_pct":   round(df["is_ev"].mean() * 100, 2),
        "hybrid_pct":          round(df["is_hybrid"].mean() * 100, 2),
        "petrol_diesel_pct":   round(
            df["fuel_type"].isin(["PETROL","DIESEL"]).mean() * 100, 2
        ),
    }

    # 3. Fleet age analysis
    age_bands = df["age_band"].value_counts().to_dict()
    report["fleet_age"] = {
        "age_band_counts":    age_bands,
        "median_vehicle_year": int(df["vehicle_year"].median()),
        "mean_fleet_age":     round(float(df["fleet_age"].mean()), 1),
        "pct_over_15_years":  round(float((df["fleet_age"] > 15).mean() * 100), 1),
        "pct_over_20_years":  round(float((df["fleet_age"] > 20).mean() * 100), 1),
        "oldest_vehicle_year": int(df["vehicle_year"].min()),
    }

    # 4. Heavy vehicle compliance
    heavy = df[df["gvm_class"].isin(["HEAVY","EXTRA-HEAVY"])]
    report["heavy_vehicle_compliance"] = {
        "total_heavy_vehicles":     int(len(heavy)),
        "heavy_pct_of_fleet":       round(len(heavy) / n * 100, 2),
        "gvm_class_breakdown":      df["gvm_class"].value_counts().to_dict(),
        "heavy_missing_gvm":        int((heavy["gross_vehicle_mass"] == 0).sum()),
        "heavy_missing_gvm_pct":    round((heavy["gross_vehicle_mass"] == 0).mean() * 100, 2),
        "avg_heavy_gvm_kg":         round(float(heavy[heavy["gross_vehicle_mass"]>0]["gross_vehicle_mass"].mean()), 0),
    }

    # 5. Vehicle usage breakdown
    usage_counts = df["vehicle_usage"].value_counts().to_dict()
    report["vehicle_usage"] = {
        "usage_breakdown":   usage_counts,
        "commercial_pct":    round(
            df["vehicle_usage"].isin([
                "OTHER GOODS","TRANSPORT LICENSED GOODS","TAXI COMMERCIAL PASSENGER"
            ]).mean() * 100, 2
        ),
        "rental_pct": round((df["vehicle_usage"] == "RENTAL").mean() * 100, 2),
    }

    # 6. Regional EV penetration 
    regional_ev = (
        df.groupby("region")
          .agg(total=("objectid","count"), ev=("is_ev","sum"))
          .assign(ev_pct=lambda x: (x["ev"] / x["total"] * 100).round(2))
          .sort_values("ev_pct", ascending=False)
          .reset_index()
    )
    report["regional_ev_penetration"] = regional_ev.to_dict(orient="records")

    # 7. Import status & origin 
    report["import_profile"] = {
        "import_status_counts": df["import_status"].value_counts().to_dict(),
        "top_origin_countries": df["original_country"].value_counts().head(10).to_dict(),
        "nz_new_pct":           round(df["nz_new"].mean() * 100, 2),
        "domestic_assembly_pct":round(df["domestic"].mean() * 100, 2),
    }

    # 8. Policy metric: fuel efficiency compliance 
    fc_df = df[df["fc_combined"] > 0]
    report["fuel_efficiency_policy"] = {
        "vehicles_with_fc_data":    int(len(fc_df)),
        "pct_with_fc_data":         round(len(fc_df) / n * 100, 2),
        "efficiency_tier_breakdown":fc_df["efficiency_tier"].value_counts().to_dict(),
        "avg_fc_all":               round(float(fc_df["fc_combined"].mean()), 2),
        "median_fc_all":            round(float(fc_df["fc_combined"].median()), 2),
        "pct_excellent_or_good":    round(
            fc_df["efficiency_tier"].isin(["EXCELLENT","GOOD"]).mean() * 100, 2
        ),
        "pct_poor":                 round(
            (fc_df["efficiency_tier"] == "POOR").mean() * 100, 2
        ),
    }

    # Save outputs
    json_path = os.path.join(OUT_PATH, "regulatory_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Flat summary CSV for stakeholders
    summary_rows = [
        ("Total Registered Vehicles",     n),
        ("Zero-Emission (EV) %",          report["emissions_profile"]["zero_emission_pct"]),
        ("Hybrid %",                       report["emissions_profile"]["hybrid_pct"]),
        ("Petrol/Diesel %",               report["emissions_profile"]["petrol_diesel_pct"]),
        ("Mean Fleet Age (years)",        report["fleet_age"]["mean_fleet_age"]),
        ("Fleet > 15 years old %",        report["fleet_age"]["pct_over_15_years"]),
        ("Heavy Vehicles %",              report["heavy_vehicle_compliance"]["heavy_pct_of_fleet"]),
        ("NZ New Import %",               report["import_profile"]["nz_new_pct"]),
        ("Avg Fuel Consumption L/100km",  report["fuel_efficiency_policy"]["avg_fc_all"]),
        ("Efficient Vehicles % (≤6.5L)",  report["fuel_efficiency_policy"]["pct_excellent_or_good"]),
    ]
    pd.DataFrame(summary_rows, columns=["Metric","Value"]).to_csv(
        os.path.join(OUT_PATH, "regulatory_summary.csv"), index=False
    )

    print(f"✓ regulatory_report complete")
    print(f"  EV penetration : {report['emissions_profile']['zero_emission_pct']}%")
    print(f"  Mean fleet age : {report['fleet_age']['mean_fleet_age']} years")
    print(f"  Quality score  : saved to regulatory_report.json")
    return report

if __name__ == "__main__":
    run_regulatory_report()
