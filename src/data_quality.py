"""
Data Quality & Profiling
Produces a machine-readable quality report
"""
import sqlite3
import os
import json
import pandas as pd
import numpy as np

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

# Expected value ranges for numeric columns
NUMERIC_BOUNDS = {
    "vehicle_year":        (1885, 2026),
    "reg_year":            (1950, 2026),
    "cc_rating":           (0,   20000),
    "gross_vehicle_mass":  (0,  200000),
    "number_of_seats":     (0,     200),
    "power_rating":        (0,    2000),
    "fc_combined":         (0,      50),
    "fleet_age":           (0,     140),
    "reg_lag":             (0,      50),
}

# Allowed categorical values 
CATEGORICAL_EXPECTED = {
    "fuel_type":     {"PETROL","DIESEL","ELECTRIC","HYBRID","LPG","UNKNOWN"},
    "import_status": {"NEW","USED","RE-REG","SCRATCH"},
    "nz_assembled":  {"IMPORTED BUILT-UP","LOCALLY ASSEMBLED"},
}

def run_data_quality():
    os.makedirs(OUT_PATH, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql("SELECT * FROM engineered_vehicles", conn)
    conn.close()

    report = {}
    n = len(df)

    # 1. Completeness
    completeness = {}
    for col in df.columns:
        non_null = int(df[col].notna().sum())
        pct      = round(non_null / n * 100, 2)
        completeness[col] = {"non_null": non_null, "null": n - non_null, "completeness_pct": pct}
    report["completeness"] = completeness

    # 2. Uniqueness
    uniqueness = {}
    for col in df.columns:
        nuniq = int(df[col].nunique())
        uniqueness[col] = {"unique_count": nuniq, "unique_pct": round(nuniq / n * 100, 4)}
    report["uniqueness"] = uniqueness

    # 3. Numeric range checks
    range_issues = {}
    for col, (lo, hi) in NUMERIC_BOUNDS.items():
        if col not in df.columns:
            continue
        out_of_range = int(((df[col] < lo) | (df[col] > hi)).sum())
        range_issues[col] = {
            "expected_min": lo, "expected_max": hi,
            "actual_min":   float(df[col].min()),
            "actual_max":   float(df[col].max()),
            "out_of_range_count": out_of_range,
            "out_of_range_pct":   round(out_of_range / n * 100, 3),
        }
    report["range_checks"] = range_issues

    # 4. Categorical consistency ────────────────────────────────────────────
    cat_issues = {}
    for col, valid in CATEGORICAL_EXPECTED.items():
        if col not in df.columns:
            continue
        unexpected = df[col].dropna()
        unexpected = unexpected[~unexpected.isin(valid)]
        cat_issues[col] = {
            "valid_values":        sorted(valid),
            "unexpected_count":    int(len(unexpected)),
            "unexpected_examples": unexpected.value_counts().head(5).to_dict(),
        }
    report["categorical_checks"] = cat_issues

    # 5. Cross-column consistency ───────────────────────────────────────────
    cross = {}

    # EV with positive CC rating (should be 0 for pure EV)
    ev_with_cc = int(((df["fuel_type"] == "ELECTRIC") & (df["cc_rating"] > 0)).sum())
    cross["ev_nonzero_cc"] = {
        "description": "Pure-electric vehicles with a non-zero CC rating",
        "count": ev_with_cc, "pct": round(ev_with_cc / n * 100, 3)
    }

    # Vehicle year AFTER registration year (impossible)
    year_inversion = int((df["vehicle_year"] > df["reg_year"]).sum())
    cross["year_inversion"] = {
        "description": "Vehicle manufactured AFTER NZ registration year",
        "count": year_inversion, "pct": round(year_inversion / n * 100, 3)
    }

    # Heavy vehicles without GVM data
    heavy_no_gvm = int(
        ((df["vehicle_type"].str.contains("TRUCK|HEAVY", na=False)) & (df["gross_vehicle_mass"] == 0)).sum()
    )
    cross["heavy_no_gvm"] = {
        "description": "Heavy vehicles with missing GVM",
        "count": heavy_no_gvm, "pct": round(heavy_no_gvm / n * 100, 3)
    }

    # Fuel consumption reported for electric vehicles (should be 0)
    ev_with_fc = int(((df["fuel_type"] == "ELECTRIC") & (df["fc_combined"] > 0)).sum())
    cross["ev_with_fuel_consumption"] = {
        "description": "Electric vehicles with a reported fuel consumption",
        "count": ev_with_fc, "pct": round(ev_with_fc / n * 100, 3)
    }

    report["cross_column_checks"] = cross

    # 6. Overall quality score
    key_cols         = ["body_type","fuel_type","reg_year","vehicle_year","make","model"]
    avg_completeness = float(np.mean([completeness[c]["completeness_pct"] for c in key_cols if c in completeness]))
    range_penalty    = float(np.mean([v["out_of_range_pct"] for v in range_issues.values()]))
    cross_penalty    = float(np.mean([v["pct"] for v in cross.values()]))
    quality_score    = round(avg_completeness - range_penalty - cross_penalty, 2)
    quality_score    = max(0, min(100, quality_score))

    report["summary"] = {
        "total_rows":              n,
        "total_columns":           len(df.columns),
        "avg_key_col_completeness": round(avg_completeness, 2),
        "range_issue_pct":         round(range_penalty, 3),
        "cross_col_issue_pct":     round(cross_penalty, 3),
        "overall_quality_score":   quality_score,
        "grade": ("A" if quality_score >= 90 else
                  "B" if quality_score >= 75 else
                  "C" if quality_score >= 60 else "D"),
    }

    # Save outputs
    json_path = os.path.join(OUT_PATH, "data_quality_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Flat completeness CSV for dashboards
    comp_df = pd.DataFrame([
        {"column": c, **v} for c, v in completeness.items()
    ])
    comp_df.to_csv(os.path.join(OUT_PATH, "column_completeness.csv"), index=False)

    print(f"✓ data_quality complete")
    print(f"  Total rows           : {n:,}")
    print(f"  Overall quality score: {quality_score} ({report['summary']['grade']})")
    print(f"  Key-col completeness : {avg_completeness:.1f}%")
    print(f"  Cross-col issues     : {cross_penalty:.2f}%")
    return report

if __name__ == "__main__":
    run_data_quality()
