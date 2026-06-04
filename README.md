# 🚗 NZ Vehicle Registration — Data Pipeline & Anomaly Detection

> End-to-end ETL pipeline and anomaly detection system built on real NZTA open data.


---

## Project Overview

This project builds a lightweight, automated data pipeline that ingests raw New Zealand
Transport Agency (NZTA) vehicle registration data, cleans it, engineers features, detects
anomalies using both statistical and ML methods, and surfaces insights through an interactive
Streamlit dashboard.

**Dataset**: 356,035 currently-registered vehicles · 40 raw columns → 45 engineered features

---

## Pipeline Architecture

```
Find Dataset
    │
    ▼
Extract & Load         - Chunked CSV ingestion to SQLite
    │
    ▼
Data Cleaning          - SQL transforms, standardisation, quality flags
    │
    ▼
Basic Anomaly Detection- Z-score, Isolation Forest on aggregated counts
    │
    ▼
Feature Engineering    -15+ derived features
    │
    ▼
Data Quality Profiling - Completeness, range, cross-column checks score + grade
    │
    ▼
Advanced Anomaly Det.  - Row-level IForest, LOF, expert rules, peer z-score
    │
    ▼
Trend Analysis         - EV adoption, fuel trends, regional fleet, seasonality
    │
    ▼
Regulatory Report     - Emissions, fleet age, heavy vehicles, efficiency policy
    │
    ▼
Streamlit Dashboard   - Interactive 8-page analytics app
```

---

## Project Structure

```
nz_vehicle_pipeline/
├── data/
│   ├── raw/                        Raw NZTA dataset
│   ├── processed/                  All pipeline outputs (CSVs, JSON reports)
│   └── database.db                 SQLite database (3 tables)
├── src/
│   ├── extract_load.py            
│   ├── clean_sql.sql               
│   ├── run_cleaning.py             
│   ├── anomaly_detection.py       
│   ├── feature_engineering.py      
│   ├── data_quality.py            
│   ├── advanced_anomaly.py        
│   ├── trend_analysis.py        
│   └── regulatory_report.py       
├── streamlit_app/
│   └── app.py                    
├── main.py                         Full pipeline orchestrator
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline
```bash
python main.py
```
This will:
- Load 356,035 rows into SQLite in chunks
- Clean and standardise all data
- Run basic anomaly detection (aggregated)
- Engineer 15+ derived features
- Profile data quality (score + grade)
- Run row-level anomaly detection (IForest + LOF + rules)
- Generate 7 trend analysis CSVs
- Produce a regulatory insights report

**Already loaded the database?**
```bash
python main.py --skip-load
```

### 3. Launch the dashboard
```bash
streamlit run streamlit_app/app.py
```

---

## Anomaly Detection Methods

| Method | Level | Description |
|--------|-------|-------------|
| Z-score | Aggregated | Flags registration counts far from mean |
| Isolation Forest (basic) | Aggregated | Unsupervised ML on aggregated groups |
| Isolation Forest (advanced) | Row-level | Multivariate on 7 numeric features |
| Local Outlier Factor | Row-level | Density-based, finds local anomalies |
| Expert Rules | Row-level | Domain logic (e.g. EV with CC rating > 500) |
| FC Peer Z-score | Row-level | Fuel consumption anomalies vs same body type |

---

## Key Findings

- **4.29%** EV penetration in the current registered fleet
- **Mean fleet age: 4 years** (this is a dataset of recent registrations)
- **21,374 composite anomalies** detected (~6% of fleet)
  - 7,203 vehicles with unusually high registration lag (>20 years)
  - 245 EVs with non-zero CC ratings (data inconsistency)
  - 55 extremely old vehicles (fleet age > 80 years)
- **Data quality score: 99.96/100 (Grade A)**
- Station Wagons dominate the fleet (142,700 registered)

---

## Tech Stack

| Category | Libraries |
|----------|-----------|
| Data wrangling | `pandas`, `numpy`, `sqlite3` |
| Statistics | `scipy` (z-score) |
| Machine Learning | `scikit-learn` (IsolationForest, LocalOutlierFactor, StandardScaler) |
| Visualisation | `plotly`, `matplotlib` |
| Dashboard | `streamlit` |

---

## Relevance to Infrastructure Regulation

This project directly demonstrates skills relevant to regulatory data work:

- **Data pipeline design**: reproducible ETL with chunk-based ingestion
- **Data quality**: automated profiling with a quantitative quality score
- **SQL proficiency**: cleaning and transformation in clean_sql.sql
- **Anomaly detection**: multiple methods from statistical to ML
- **Regulatory reporting**: fleet emissions, EV penetration, heavy vehicle compliance
- **Geospatial awareness**: TLA → Region mapping across all 67 NZ TLAs
- **Critical thinking**: expert rule flags based on domain knowledge

---

## Data Source

NZTA Motor Vehicle Register — New Zealand Open Data Portal
Licensed under the Creative Commons Attribution 4.0 International licence.
