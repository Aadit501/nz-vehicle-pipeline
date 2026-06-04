"""
Run Data Cleaning
"""
import sqlite3
import os

DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
SQL_PATH = os.path.join(os.path.dirname(__file__), "clean_sql.sql")

def run_cleaning():
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_PATH) as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()

    raw_count     = conn.execute("SELECT COUNT(*) FROM raw_vehicles").fetchone()[0]
    cleaned_count = conn.execute("SELECT COUNT(*) FROM cleaned_vehicles").fetchone()[0]
    flag_count    = conn.execute(
        "SELECT COUNT(*) FROM cleaned_vehicles WHERE flag_invalid_reg_year=1 OR flag_suspect_cc=1"
    ).fetchone()[0]
    conn.close()

    print(f"✓ run_cleaning complete")
    print(f"  Raw rows     : {raw_count:,}")
    print(f"  Cleaned rows : {cleaned_count:,}")
    print(f"  Flagged rows : {flag_count:,}")
    return cleaned_count

if __name__ == "__main__":
    run_cleaning()
