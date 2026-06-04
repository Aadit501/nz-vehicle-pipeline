"""
Extract & Load
"""
import pandas as pd
import sqlite3
import os

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "Dataset.csv")
DB_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
CHUNK     = 100_000

def extract_load():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS raw_vehicles")
    conn.commit()

    total = 0
    for i, chunk in enumerate(pd.read_csv(RAW_PATH, chunksize=CHUNK, low_memory=False)):
        chunk.columns = [c.lower() for c in chunk.columns]
        chunk.to_sql("raw_vehicles", conn, if_exists="append", index=False)
        total += len(chunk)
        print(f"  Loaded chunk {i+1}: {total:,} rows so far")

    conn.close()
    print(f"✓ extract_load complete — {total:,} rows in raw_vehicles")
    return total

if __name__ == "__main__":
    extract_load()
