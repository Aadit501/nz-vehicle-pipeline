"""
NZ Vehicle Registration Data Pipeline – Main Orchestrator
Run this file to execute the full end-to-end pipeline:
Extract & Load
Data Cleaning
Basic Anomaly Detection
Feature Engineering
Data Quality Profiling
Advanced Row-Level Anomaly Detection
Time-Series & Trend Analysis
Regulatory Insights Report

Usage:
  python main.py                 # full pipeline
  python main.py --skip-load     # skip step 2 (if DB already loaded)
"""
import sys
import time
import argparse
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def banner(msg: str):
    line = "─" * 60
    print(f"\n{line}")
    print(f"  {msg}")
    print(f"{line}")


def run_step(name: str, fn, *args, **kwargs):
    banner(name)
    t0 = time.time()
    result = fn(*args, **kwargs)
    elapsed = time.time() - t0
    print(f"  ⏱  {elapsed:.1f}s")
    return result


def main(skip_load: bool = False):
    print("\n" + "═" * 60)
    print("  NZ Vehicle Registration — Data Pipeline")
    print("═" * 60)

    if not skip_load:
        from extract_load import extract_load
        run_step("Extract & Load", extract_load)

        from run_cleaning import run_cleaning
        run_step("Data Cleaning", run_cleaning)

        from anomaly_detection import run_anomaly_detection
        run_step("Basic Anomaly Detection", run_anomaly_detection)

    from feature_engineering import run_feature_engineering
    run_step("Feature Engineering", run_feature_engineering)

    from data_quality import run_data_quality
    run_step("Data Quality Profiling", run_data_quality)

    from advanced_anomaly import run_advanced_anomaly
    run_step("Advanced Anomaly Detection", run_advanced_anomaly)

    from trend_analysis import run_trend_analysis
    run_step("Trend Analysis", run_trend_analysis)

    from regulatory_report import run_regulatory_report
    run_step("Regulatory Report", run_regulatory_report)

    print("\n" + "═" * 60)
    print("  Pipeline complete!")
    print("  Launch dashboard: streamlit run streamlit_app/app.py")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-load", action="store_true",
                        help="Skip extract/load/clean (use existing DB)")
    args = parser.parse_args()
    main(skip_load=args.skip_load)
