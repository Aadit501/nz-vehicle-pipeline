"""
Advanced Feature Engineering
New features:
  - fleet_age          : years since vehicle manufacture
  - reg_lag            : years between manufacture and first NZ registration
  - is_ev              : boolean for pure-electric vehicles
  - is_hybrid          : boolean for hybrid vehicles
  - is_zero_emission   : EV or hydrogen
  - efficiency_tier    : 'EXCELLENT' / 'GOOD' / 'AVERAGE' / 'POOR' / 'N/A'
  - gvm_class          : Light / Medium / Heavy / Extra-Heavy
  - age_band           : decade bands (Pre-2000, 2000-2009, 2010-2019, 2020+)
  - region             : NZ regional grouping from TLA
  - nz_new             : 1 if NEW import, else 0
  - domestic           : 1 if NZ-assembled, else 0
  - has_fuel_data      : 1 if fc_combined > 0
"""
import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")

# TLA → Region mapping 
TLA_REGION = {
    # Northland
    "FAR NORTH DISTRICT":"Northland","KAIPARA DISTRICT":"Northland",
    "WHANGAREI DISTRICT":"Northland",
    # Auckland
    "AUCKLAND":"Auckland",
    # Waikato
    "HAMILTON CITY":"Waikato","HAURAKI DISTRICT":"Waikato",
    "MATAMATA-PIAKO DISTRICT":"Waikato","OTOROHANGA DISTRICT":"Waikato",
    "SOUTH WAIKATO DISTRICT":"Waikato","TAUPO DISTRICT":"Waikato",
    "THAMES-COROMANDEL DISTRICT":"Waikato","WAIKATO DISTRICT":"Waikato",
    "WAIPA DISTRICT":"Waikato","WAITOMO DISTRICT":"Waikato",
    # Bay of Plenty
    "KAWERAU DISTRICT":"Bay of Plenty","OPOTIKI DISTRICT":"Bay of Plenty",
    "ROTORUA DISTRICT":"Bay of Plenty","TAURANGA CITY":"Bay of Plenty",
    "WESTERN BAY OF PLENTY DISTRICT":"Bay of Plenty","WHAKATANE DISTRICT":"Bay of Plenty",
    # Gisborne
    "GISBORNE DISTRICT":"Gisborne",
    # Hawke's Bay
    "CENTRAL HAWKE'S BAY DISTRICT":"Hawke's Bay","HASTINGS DISTRICT":"Hawke's Bay",
    "NAPIER CITY":"Hawke's Bay","WAIROA DISTRICT":"Hawke's Bay",
    # Taranaki
    "NEW PLYMOUTH DISTRICT":"Taranaki","SOUTH TARANAKI DISTRICT":"Taranaki",
    "STRATFORD DISTRICT":"Taranaki",
    # Manawatu-Whanganui
    "HOROWHENUA DISTRICT":"Manawatu-Whanganui","MANAWATU DISTRICT":"Manawatu-Whanganui",
    "PALMERSTON NORTH CITY":"Manawatu-Whanganui","RANGITIKEI DISTRICT":"Manawatu-Whanganui",
    "RUAPEHU DISTRICT":"Manawatu-Whanganui","TARARUA DISTRICT":"Manawatu-Whanganui",
    "WHANGANUI DISTRICT":"Manawatu-Whanganui",
    # Wellington
    "CARTERTON DISTRICT":"Wellington","KAPITI COAST DISTRICT":"Wellington",
    "LOWER HUTT CITY":"Wellington","MASTERTON DISTRICT":"Wellington",
    "PORIRUA CITY":"Wellington","SOUTH WAIRARAPA DISTRICT":"Wellington",
    "UPPER HUTT CITY":"Wellington","WELLINGTON CITY":"Wellington",
    # Nelson-Tasman
    "NELSON CITY":"Nelson-Tasman","TASMAN DISTRICT":"Nelson-Tasman",
    # Marlborough
    "MARLBOROUGH DISTRICT":"Marlborough",
    # West Coast
    "BULLER DISTRICT":"West Coast","GREY DISTRICT":"West Coast",
    "WESTLAND DISTRICT":"West Coast",
    # Canterbury
    "CHRISTCHURCH CITY":"Canterbury","HURUNUI DISTRICT":"Canterbury",
    "KAIKOURA DISTRICT":"Canterbury","MACKENZIE DISTRICT":"Canterbury",
    "SELWYN DISTRICT":"Canterbury","TIMARU DISTRICT":"Canterbury",
    "WAIMAKARIRI DISTRICT":"Canterbury","WAIMATE DISTRICT":"Canterbury",
    # Otago
    "CENTRAL OTAGO DISTRICT":"Otago","CLUTHA DISTRICT":"Otago",
    "DUNEDIN CITY":"Otago","QUEENSTOWN-LAKES DISTRICT":"Otago",
    "WAITAKI DISTRICT":"Otago",
    # Southland
    "GORE DISTRICT":"Southland","INVERCARGILL CITY":"Southland",
    "SOUTHLAND DISTRICT":"Southland",
}

def run_feature_engineering():
    conn = sqlite3.connect(DB_PATH)

    print("  Loading cleaned_vehicles …")
    df = pd.read_sql("SELECT * FROM cleaned_vehicles", conn)

    CURRENT_YEAR = 2025

    # Core derived features 
    df["fleet_age"]   = CURRENT_YEAR - df["vehicle_year"].clip(1885, CURRENT_YEAR)
    df["reg_lag"]     = (df["reg_year"] - df["vehicle_year"]).clip(0, 50)

    df["is_ev"]           = (df["fuel_type"] == "ELECTRIC").astype(int)
    df["is_hybrid"]       = (df["fuel_type"] == "HYBRID").astype(int)
    df["is_zero_emission"] = df["is_ev"]   # extend later for H2

    # Efficiency tier (based on combined fuel consumption L/100km)
    def efficiency_tier(fc):
        if fc <= 0:     return "N/A"
        if fc <= 4.5:   return "EXCELLENT"
        if fc <= 6.5:   return "GOOD"
        if fc <= 9.0:   return "AVERAGE"
        return "POOR"

    df["efficiency_tier"] = df["fc_combined"].apply(efficiency_tier)

    # GVM class 
    def gvm_class(gvm):
        if gvm <= 0:      return "UNKNOWN"
        if gvm <= 3500:   return "LIGHT"
        if gvm <= 12000:  return "MEDIUM"
        if gvm <= 25000:  return "HEAVY"
        return "EXTRA-HEAVY"

    df["gvm_class"] = df["gross_vehicle_mass"].apply(gvm_class)

    # Vehicle age band 
    def age_band(yr):
        if yr < 2000:  return "PRE-2000"
        if yr < 2010:  return "2000-2009"
        if yr < 2020:  return "2010-2019"
        return "2020+"

    df["age_band"] = df["vehicle_year"].apply(age_band)

    # Region mapping 
    df["region"] = df["tla"].map(TLA_REGION).fillna("Other/Unknown")

    # Simple binary flags 
    df["nz_new"]       = (df["import_status"] == "NEW").astype(int)
    df["domestic"]     = (df["nz_assembled"] == "LOCALLY ASSEMBLED").astype(int)
    df["has_fuel_data"]= (df["fc_combined"] > 0).astype(int)

    # Write to DB 
    print("  Writing engineered_vehicles …")
    conn.execute("DROP TABLE IF EXISTS engineered_vehicles")
    df.to_sql("engineered_vehicles", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

    print(f"✓ feature_engineering complete — {len(df):,} rows, {len(df.columns)} columns")
    return df

if __name__ == "__main__":
    run_feature_engineering()
