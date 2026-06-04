"""
NZ Vehicle Registration — Streamlit Dashboard
Multi-page analytics dashboard covering the full pipeline output.
"""
import os, json, sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Path helpers
BASE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.join(BASE, "..")
DB    = os.path.join(ROOT, "data", "database.db")
PROC  = os.path.join(ROOT, "data", "processed")

# Colour palette 
PALETTE = px.colors.qualitative.Set2
EV_COLOUR     = "#2ecc71"
PETROL_COLOUR = "#e67e22"
DIESEL_COLOUR = "#e74c3c"
HYBRID_COLOUR = "#3498db"

st.set_page_config(
    page_title="NZ Vehicle Fleet Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS 
st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px 20px;
    border-left: 4px solid #3498db;
    margin-bottom: 8px;
}
.metric-value { font-size: 2rem; font-weight: 700; color: #2c3e50; }
.metric-label { font-size: 0.85rem; color: #7f8c8d; margin-top: 2px; }
.anomaly-badge {
    background: #e74c3c; color: white;
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.75rem; font-weight: 600;
}
.good-badge {
    background: #27ae60; color: white;
    border-radius: 4px; padding: 2px 8px;
    font-size: 0.75rem; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)



# Data loading helpers (cached)

@st.cache_data(ttl=3600)
def load_engineered():
    path = os.path.join(PROC, "engineered_vehicles.parquet")
    return pd.read_parquet(path)

@st.cache_data
def load_csv(filename):
    path = os.path.join(PROC, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

@st.cache_data
def load_json(filename):
    path = os.path.join(PROC, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

@st.cache_data(ttl=3600)
def load_anomalies():
    path = os.path.join(PROC, "advanced_anomalies.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()



# Sidebar Navigation


st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/320px-Flag_of_New_Zealand.svg.png", width=80)
st.sidebar.title("NZ Vehicle Fleet")
st.sidebar.caption("NZTA Open Data Pipeline")
st.sidebar.divider()

PAGES = {
    "Overview":              "overview",
    "Data Quality":          "quality",
    "Fleet Analysis":        "fleet",
    "EV & Sustainability":    "ev",
    "Regional Analysis":     "regional",
    "Anomaly Explorer":      "anomalies",
    "Regulatory Insights":   "regulatory",
    "Pipeline Info":         "pipeline",
}

page = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")
active = PAGES[page]

st.sidebar.divider()
st.sidebar.caption("Data source: NZTA Motor Vehicle Register")
st.sidebar.caption("Pipeline: ETL → Clean → Feature Eng → Anomaly Detection")



# Load core data (shared across pages)


df = load_engineered()
reg_report = load_json("regulatory_report.json")
dq_report  = load_json("data_quality_report.json")



# PAGE: Overview


if active == "overview":
    st.title("NZ Vehicle Fleet — Overview")
    st.caption("National snapshot from the NZTA Motor Vehicle Register · 2025")

    # KPI cards 
    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_style = "background:#f0f4ff;border-radius:8px;padding:14px;text-align:center;border-top:4px solid {color}"

    def kpi(col, label, value, color="#3498db"):
        col.markdown(f"""
        <div style="{kpi_style.format(color=color)}">
            <div style="font-size:1.8rem;font-weight:700;color:#2c3e50">{value}</div>
            <div style="font-size:0.8rem;color:#7f8c8d;margin-top:4px">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi(k1, "Total Registered Vehicles", f"{len(df):,}")
    kpi(k2, "EV Penetration",
        f"{reg_report.get('emissions_profile',{}).get('zero_emission_pct','–')}%", "#2ecc71")
    kpi(k3, "Mean Fleet Age",
        f"{reg_report.get('fleet_age',{}).get('mean_fleet_age','–')} yrs", "#e67e22")
    kpi(k4, "Data Quality Score",
        f"{dq_report.get('summary',{}).get('overall_quality_score','–')} / 100", "#9b59b6")
    kpi(k5, "Anomalies Detected",
        f"{int(df.get('anomaly_composite', pd.Series([0])).sum()):,}", "#e74c3c")

    st.markdown("---")

    # Fuel type donut + body type bar
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fleet by Fuel Type")
        fuel_counts = df["fuel_type"].value_counts().reset_index()
        fuel_counts.columns = ["fuel_type", "count"]
        fig = px.pie(fuel_counts, names="fuel_type", values="count",
                     hole=0.45, color_discrete_sequence=PALETTE)
        fig.update_layout(margin=dict(t=20,b=20), height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 12 Body Types")
        bt = df["body_type"].value_counts().head(12).reset_index()
        bt.columns = ["body_type","count"]
        fig = px.bar(bt, x="count", y="body_type", orientation="h",
                     color="count", color_continuous_scale="Blues")
        fig.update_layout(margin=dict(t=10,b=10), height=350, showlegend=False,
                          yaxis=dict(autorange="reversed"),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Registration trend
    st.subheader("Registrations by Vehicle Year (2000–2025)")
    yr_df = df[df["vehicle_year"].between(2000, 2025)]["vehicle_year"].value_counts().sort_index().reset_index()
    yr_df.columns = ["vehicle_year","count"]
    fig = px.area(yr_df, x="vehicle_year", y="count",
                  color_discrete_sequence=["#3498db"])
    fig.update_layout(margin=dict(t=10,b=10), height=280,
                      xaxis_title="Vehicle Year", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

    # Quick stats table 
    st.subheader("Quick Stats")
    qs_col1, qs_col2, qs_col3 = st.columns(3)
    with qs_col1:
        st.metric("Unique Makes",  int(df["make"].nunique()))
        st.metric("Unique Models", int(df["model"].nunique()))
        st.metric("NZ Regions",    int(df["region"].nunique()))
    with qs_col2:
        st.metric("% New Imports",  f"{reg_report.get('import_profile',{}).get('nz_new_pct','–')}%")
        st.metric("% Hybrid",       f"{reg_report.get('emissions_profile',{}).get('hybrid_pct','–')}%")
        st.metric("Avg FC (L/100km)", f"{reg_report.get('fuel_efficiency_policy',{}).get('avg_fc_all','–')}")
    with qs_col3:
        st.metric("Fleet > 15yrs", f"{reg_report.get('fleet_age',{}).get('pct_over_15_years','–')}%")
        st.metric("Heavy Vehicles", f"{reg_report.get('heavy_vehicle_compliance',{}).get('heavy_pct_of_fleet','–')}%")
        st.metric("Data Quality Grade", dq_report.get("summary",{}).get("grade","–"))



# PAGE: Data Quality


elif active == "quality":
    st.title("Data Quality Profiling")

    summ = dq_report.get("summary", {})
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Overall Score",  f"{summ.get('overall_quality_score','–')} / 100")
    q2.metric("Grade",          summ.get("grade","–"))
    q3.metric("Key-col Completeness", f"{summ.get('avg_key_col_completeness','–')}%")
    q4.metric("Cross-col Issues",     f"{summ.get('cross_col_issue_pct','–')}%")

    st.markdown("---")

    # Column completeness heatmap-style bar 
    st.subheader("Column Completeness (% Non-Null)")
    comp_df = load_csv("column_completeness.csv")
    if not comp_df.empty:
        comp_df = comp_df.sort_values("completeness_pct")
        fig = px.bar(comp_df, x="completeness_pct", y="column", orientation="h",
                     color="completeness_pct",
                     color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
                     range_color=[0,100])
        fig.update_layout(height=900, margin=dict(t=10,b=10),
                          xaxis_title="% Complete", yaxis_title="",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Numeric range checks 
    with col1:
        st.subheader("Numeric Range Issues")
        rc = dq_report.get("range_checks", {})
        rows = []
        for col_name, v in rc.items():
            rows.append({
                "Column": col_name,
                "Expected Min": v["expected_min"],
                "Expected Max": v["expected_max"],
                "Actual Min": v["actual_min"],
                "Actual Max": v["actual_max"],
                "Out of Range": v["out_of_range_count"],
                "% Issue": v["out_of_range_pct"],
            })
        rc_df = pd.DataFrame(rows)
        st.dataframe(rc_df, use_container_width=True, hide_index=True)

    # Cross-column checks 
    with col2:
        st.subheader("Cross-Column Consistency Checks")
        cc = dq_report.get("cross_column_checks", {})
        cc_rows = []
        for check, v in cc.items():
            status = "OK" if v["count"] == 0 else f" {v['count']:,} rows"
            cc_rows.append({
                "Check": check,
                "Description": v["description"],
                "Issues": v["count"],
                "Issue %": v["pct"],
                "Status": status,
            })
        cc_df = pd.DataFrame(cc_rows)
        st.dataframe(cc_df, use_container_width=True, hide_index=True)

    # Quality flags from cleaning
    st.markdown("---")
    st.subheader("Quality Flags from Cleaning Step")
    flag_cols = [c for c in df.columns if c.startswith("flag_")]
    if flag_cols:
        flag_data = {c: int(df[c].sum()) for c in flag_cols}
        flag_df   = pd.DataFrame(flag_data.items(), columns=["Flag", "Count"])
        flag_df["% of Rows"] = (flag_df["Count"] / len(df) * 100).round(3)
        st.dataframe(flag_df, use_container_width=True, hide_index=True)



# PAGE: Fleet Analysis


elif active == "fleet":
    st.title("Fleet Analysis")

    tab1, tab2, tab3, tab4 = st.tabs(["Fuel Trends", "Body Types", "Top Makes", "Vehicle Age"])

    with tab1:
        st.subheader("Fuel Type Share Over Vehicle Year (2000–2025)")
        fuel_trend = load_csv("yearly_fuel_trends.csv")
        if not fuel_trend.empty:
            fuel_trend = fuel_trend[fuel_trend["vehicle_year"].between(2000, 2025)]
            fig = px.area(fuel_trend, x="vehicle_year", y="share_pct", color="fuel_type",
                          color_discrete_map={
                              "ELECTRIC": EV_COLOUR, "PETROL": PETROL_COLOUR,
                              "DIESEL": DIESEL_COLOUR, "HYBRID": HYBRID_COLOUR,
                          })
            fig.update_layout(height=420, xaxis_title="Vehicle Year",
                              yaxis_title="Share (%)", legend_title="Fuel Type")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Absolute Counts by Fuel Type")
            cnt_df = fuel_trend.copy()
            fig2 = px.bar(cnt_df, x="vehicle_year", y="count", color="fuel_type",
                          color_discrete_map={
                              "ELECTRIC": EV_COLOUR, "PETROL": PETROL_COLOUR,
                              "DIESEL": DIESEL_COLOUR, "HYBRID": HYBRID_COLOUR,
                          })
            fig2.update_layout(height=380, barmode="stack")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Body Type Distribution")
        bt_trend = load_csv("body_type_trend.csv")
        if not bt_trend.empty:
            fig = px.line(bt_trend, x="reg_year", y="count", color="body_type",
                          markers=True, color_discrete_sequence=PALETTE)
            fig.update_layout(height=420, xaxis_title="Registration Year",
                              yaxis_title="Count", legend_title="Body Type")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Overall Body Type Counts")
        bt_all = df["body_type"].value_counts().head(20).reset_index()
        bt_all.columns = ["body_type","count"]
        fig2 = px.bar(bt_all, x="body_type", y="count",
                      color="count", color_continuous_scale="Viridis")
        fig2.update_layout(height=380, coloraxis_showscale=False,
                           xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("Top Makes — Market Share Over Time")
        make_df = load_csv("make_market_share.csv")
        if not make_df.empty:
            year_options = sorted(make_df["reg_year"].unique(), reverse=True)
            sel_year = st.selectbox("Select Year", year_options)
            yr_makes = make_df[make_df["reg_year"] == sel_year].nlargest(15, "count")
            fig = px.bar(yr_makes, x="count", y="make", orientation="h",
                         color="count", color_continuous_scale="Blues")
            fig.update_layout(height=460, yaxis=dict(autorange="reversed"),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("All-Time Top 20 Makes")
        top_makes = df["make"].value_counts().head(20).reset_index()
        top_makes.columns = ["make","count"]
        fig2 = px.treemap(top_makes, path=["make"], values="count",
                          color="count", color_continuous_scale="RdBu")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.subheader("Fleet Age Distribution")
        age_df = df[df["fleet_age"].between(0,50)]["fleet_age"]
        fig = px.histogram(age_df, nbins=50, color_discrete_sequence=["#3498db"])
        fig.update_layout(height=360, xaxis_title="Fleet Age (years)",
                          yaxis_title="Number of Vehicles")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Age Band Breakdown")
            ab = df["age_band"].value_counts().reset_index()
            ab.columns = ["Age Band","Count"]
            fig2 = px.pie(ab, names="Age Band", values="Count",
                          color_discrete_sequence=PALETTE)
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            st.subheader("Efficiency Tier Breakdown")
            eff_trend = load_csv("efficiency_trends.csv")
            if not eff_trend.empty:
                eff_total = eff_trend.groupby("efficiency_tier")["count"].sum().reset_index()
                fig3 = px.pie(eff_total, names="efficiency_tier", values="count",
                              color="efficiency_tier",
                              color_discrete_map={
                                  "EXCELLENT":"#2ecc71","GOOD":"#27ae60",
                                  "AVERAGE":"#f39c12","POOR":"#e74c3c","N/A":"#bdc3c7"
                              })
                fig3.update_layout(height=300)
                st.plotly_chart(fig3, use_container_width=True)


# PAGE: EV & Sustainability


elif active == "ev":
    st.title("EV & Sustainability Analysis")

    ev_df = load_csv("ev_adoption.csv")

    if not ev_df.empty:
        # EV adoption line chart 
        st.subheader("EV & Hybrid Adoption Rate (Registration Year)")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=ev_df["reg_year"], y=ev_df["total"],
                             name="Total Registrations", marker_color="#ecf0f1"), secondary_y=False)
        fig.add_trace(go.Scatter(x=ev_df["reg_year"], y=ev_df["ev_share_pct"],
                                 mode="lines+markers", name="EV %",
                                 line=dict(color=EV_COLOUR, width=3)), secondary_y=True)
        fig.add_trace(go.Scatter(x=ev_df["reg_year"], y=ev_df["hybrid_share_pct"],
                                 mode="lines+markers", name="Hybrid %",
                                 line=dict(color=HYBRID_COLOUR, width=2, dash="dash")), secondary_y=True)
        fig.update_layout(height=420, legend=dict(orientation="h", y=1.12),
                          hovermode="x unified")
        fig.update_yaxes(title_text="Registrations", secondary_y=False)
        fig.update_yaxes(title_text="Share (%)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

        # YoY EV growth 
        st.subheader("EV Year-on-Year Growth (%)")
        ev_yoy = ev_df[ev_df["ev_yoy_growth"].notna() & ev_df["reg_year"] >= 2012]
        fig2 = px.bar(ev_yoy, x="reg_year", y="ev_yoy_growth",
                      color="ev_yoy_growth",
                      color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
                      color_continuous_midpoint=0)
        fig2.update_layout(height=320, coloraxis_showscale=False,
                           xaxis_title="Year", yaxis_title="YoY Growth (%)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Fuel efficiency distribution 
    st.subheader("Fuel Consumption Distribution by Body Type")
    body_types = df[df["fc_combined"] > 0]["body_type"].value_counts().head(8).index.tolist()
    fc_df = df[(df["fc_combined"] > 0) & (df["body_type"].isin(body_types))]
    fig3 = px.box(fc_df, x="body_type", y="fc_combined",
                  color="body_type", color_discrete_sequence=PALETTE,
                  points=False)
    fig3.update_layout(height=400, xaxis_title="Body Type",
                       yaxis_title="Fuel Consumption (L/100km)", showlegend=False,
                       xaxis_tickangle=-20)
    st.plotly_chart(fig3, use_container_width=True)

    # EV by region 
    st.subheader("EV Penetration by Region")
    reg_df = load_csv("regional_fleet.csv")
    if not reg_df.empty:
        reg_sorted = reg_df.sort_values("ev_pct", ascending=True)
        fig4 = px.bar(reg_sorted, x="ev_pct", y="region", orientation="h",
                      color="ev_pct", color_continuous_scale="Greens",
                      text="ev_pct")
        fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig4.update_layout(height=480, coloraxis_showscale=False,
                           xaxis_title="EV %", yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

    # Synthetic Greenhouse Gas Refrigerant Usage
    st.subheader("Synthetic Greenhouse Gas Refrigerant Usage")
    ghg_df = df["synthetic_greenhouse_gas"].value_counts().head(10).reset_index()
    ghg_df.columns = ["Refrigerant","Count"]
    ghg_df = ghg_df[ghg_df["Refrigerant"].notna()]
    if not ghg_df.empty:
        fig5 = px.bar(ghg_df, x="Count", y="Refrigerant", orientation="h",
                      color="Count", color_continuous_scale="Reds")
        fig5.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)
        st.caption("HFO-1234YF (R1234YF) has ~1500x lower global warming potential than the legacy HFC-134a (R134a).")


# PAGE: Regional Analysis

elif active == "regional":
    st.title("Regional Fleet Analysis")

    reg_df = load_csv("regional_fleet.csv")

    if not reg_df.empty:
        # Bubble chart: total vehicles vs EV % 
        st.subheader("Regional Fleet Size vs EV Penetration")
        fig = px.scatter(reg_df, x="ev_pct", y="avg_fleet_age",
                         size="total_vehicles", color="region",
                         hover_data=["total_vehicles","avg_fc","new_pct"],
                         text="region",
                         color_discrete_sequence=PALETTE)
        fig.update_traces(textposition="top center")
        fig.update_layout(height=480, xaxis_title="EV Penetration (%)",
                          yaxis_title="Avg Fleet Age (yrs)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Regional comparison table 
        st.subheader("Regional Fleet Metrics")
        display_df = reg_df[["region","total_vehicles","ev_count","ev_pct",
                              "hybrid_count","avg_fleet_age","avg_fc","new_pct"]].copy()
        display_df.columns = ["Region","Total Vehicles","EVs","EV %",
                               "Hybrids","Avg Fleet Age","Avg FC (L/100km)","New Import %"]
        display_df = display_df.sort_values("Total Vehicles", ascending=False)
        st.dataframe(
            display_df.style.background_gradient(subset=["EV %"], cmap="Greens")
                            .background_gradient(subset=["Avg Fleet Age"], cmap="Oranges")
                            .format({"Total Vehicles": "{:,}", "EVs": "{:,}",
                                     "EV %": "{:.1f}%", "Avg Fleet Age": "{:.1f}",
                                     "Avg FC (L/100km)": "{:.2f}", "New Import %": "{:.1f}%"}),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # TLA-level drill-down 
    st.subheader("Drill Down by TLA (Territorial Local Authority)")
    tla_df = (
        df.groupby("tla")
          .agg(count=("objectid","count"),
               ev_pct=("is_ev","mean"),
               avg_age=("fleet_age","mean"),
               avg_fc=("fc_combined", lambda x: x[x>0].mean()))
          .reset_index()
    )
    tla_df["ev_pct"]  = (tla_df["ev_pct"] * 100).round(2)
    tla_df["avg_age"] = tla_df["avg_age"].round(1)
    tla_df["avg_fc"]  = tla_df["avg_fc"].round(2)
    tla_df = tla_df.sort_values("count", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vehicles per TLA (Top 20)")
        top_tla = tla_df.head(20)
        fig2 = px.bar(top_tla, x="count", y="tla", orientation="h",
                      color="count", color_continuous_scale="Blues")
        fig2.update_layout(height=520, yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("EV % by TLA (Top 20)")
        top_ev_tla = tla_df.nlargest(20, "ev_pct")
        fig3 = px.bar(top_ev_tla.sort_values("ev_pct"), x="ev_pct", y="tla",
                      orientation="h", color="ev_pct",
                      color_continuous_scale="Greens", text="ev_pct")
        fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig3.update_layout(height=520, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Full TLA Table")
    st.dataframe(tla_df.rename(columns={
        "tla":"TLA","count":"Vehicles","ev_pct":"EV %",
        "avg_age":"Avg Age","avg_fc":"Avg FC"}),
        use_container_width=True, hide_index=True, height=350)


# PAGE: Anomaly Explorer


elif active == "anomalies":
    st.title("Anomaly Explorer")

    anom_df = load_anomalies()
    n_total = len(df)
    n_anom  = int(df.get("anomaly_composite", pd.Series([0] * n_total)).sum())

    # Summary metrics
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Anomalies",      f"{n_anom:,}")
    c2.metric("% of Fleet",           f"{n_anom/n_total*100:.2f}%")
    c3.metric("IForest Anomalies",    f"{int(df.get('anomaly_iforest', pd.Series(0)).sum()):,}")
    c4.metric("LOF Anomalies",        f"{int(df.get('anomaly_lof', pd.Series(0)).sum()):,}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Anomaly type breakdown 
    with col1:
        st.subheader("Anomaly Detection Method Overlap")
        if "anomaly_iforest" in df.columns:
            method_counts = {
                "Isolation Forest": int(df["anomaly_iforest"].sum()),
                "LOF":              int(df.get("anomaly_lof", pd.Series(0)).sum()),
                "FC Peer Z-score":  int(df.get("anomaly_fc_peer", pd.Series(0)).sum()),
                "Composite":        n_anom,
            }
            fig = px.bar(
                x=list(method_counts.keys()),
                y=list(method_counts.values()),
                color=list(method_counts.keys()),
                color_discrete_sequence=PALETTE,
            )
            fig.update_layout(height=320, showlegend=False,
                              yaxis_title="Count", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    # Rule flag breakdown 
    with col2:
        st.subheader("Expert Rule Flag Counts")
        rule_cols = [c for c in df.columns if c.startswith("rule_")]
        if rule_cols:
            rule_counts = {c.replace("rule_","").replace("_"," ").title(): int(df[c].sum())
                           for c in rule_cols}
            fig2 = px.bar(
                x=list(rule_counts.values()),
                y=list(rule_counts.keys()),
                orientation="h",
                color=list(rule_counts.values()),
                color_continuous_scale="Reds",
            )
            fig2.update_layout(height=320, coloraxis_showscale=False,
                               xaxis_title="Count", yaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

    # Scatter: IForest score vs fleet_age 
    st.subheader("Anomaly Score vs Fleet Age")
    if "anomaly_iforest_score" in df.columns:
        sample = df.sample(min(5000, len(df)), random_state=42)
        fig3 = px.scatter(sample, x="fleet_age", y="anomaly_iforest_score",
                          color="anomaly_composite" if "anomaly_composite" in sample.columns else None,
                          color_continuous_scale=["#3498db","#e74c3c"],
                          opacity=0.4, hover_data=["make","model","fuel_type","body_type"])
        fig3.update_layout(height=380, xaxis_title="Fleet Age (years)",
                           yaxis_title="Isolation Forest Anomaly Score",
                           coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    # Anomaly table 
    st.subheader("Top Anomalies (by Isolation Forest Score)")
    if not anom_df.empty:
        display_cols = ["make","model","fuel_type","body_type","vehicle_year",
                        "reg_year","fleet_age","cc_rating","fc_combined",
                        "anomaly_iforest_score","anomaly_iforest","anomaly_lof",
                        "anomaly_fc_peer","region"]
        display_cols = [c for c in display_cols if c in anom_df.columns]

        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            makes = ["All"] + sorted(anom_df["make"].dropna().unique().tolist())
            sel_make = st.selectbox("Filter by Make", makes)
        with f2:
            fuels = ["All"] + sorted(anom_df["fuel_type"].dropna().unique().tolist())
            sel_fuel = st.selectbox("Filter by Fuel", fuels)
        with f3:
            bodies = ["All"] + sorted(anom_df["body_type"].dropna().unique().tolist())
            sel_body = st.selectbox("Filter by Body Type", bodies)

        filtered = anom_df.copy()
        if sel_make != "All": filtered = filtered[filtered["make"] == sel_make]
        if sel_fuel != "All": filtered = filtered[filtered["fuel_type"] == sel_fuel]
        if sel_body != "All": filtered = filtered[filtered["body_type"] == sel_body]

        st.dataframe(filtered[display_cols].head(500),
                     use_container_width=True, hide_index=True, height=400)
        st.caption(f"Showing up to 500 of {len(filtered):,} filtered anomalies")

        # Download
        csv_bytes = filtered[display_cols].to_csv(index=False).encode()
        st.download_button("Download Filtered Anomalies CSV", csv_bytes,
                           "filtered_anomalies.csv", "text/csv")



# PAGE: Regulatory Insights

elif active == "regulatory":
    st.title("Regulatory Insights")
    st.caption("Summary metrics for infrastructure regulation and transport policy")

    # Key regulatory KPIs
    ep = reg_report.get("emissions_profile", {})
    fa = reg_report.get("fleet_age", {})
    hv = reg_report.get("heavy_vehicle_compliance", {})
    fp = reg_report.get("fuel_efficiency_policy", {})

    r1, r2, r3 = st.columns(3)
    with r1:
        st.subheader("Emissions Profile")
        st.metric("EV Penetration",       f"{ep.get('zero_emission_pct','–')}%")
        st.metric("Hybrid Share",          f"{ep.get('hybrid_pct','–')}%")
        st.metric("Petrol/Diesel Share",   f"{ep.get('petrol_diesel_pct','–')}%")

    with r2:
        st.subheader("Fleet Age")
        st.metric("Mean Fleet Age",        f"{fa.get('mean_fleet_age','–')} years")
        st.metric("Fleet > 15 Years",      f"{fa.get('pct_over_15_years','–')}%")
        st.metric("Fleet > 20 Years",      f"{fa.get('pct_over_20_years','–')}%")
        st.metric("Oldest Vehicle Year",   str(fa.get('oldest_vehicle_year','–')))

    with r3:
        st.subheader("Heavy Vehicles")
        st.metric("Total Heavy Vehicles",  f"{hv.get('total_heavy_vehicles',0):,}")
        st.metric("% of Fleet",            f"{hv.get('heavy_pct_of_fleet','–')}%")
        st.metric("Missing GVM Data",      f"{hv.get('heavy_missing_gvm_pct','–')}%")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Fuel type mix pie 
        st.subheader("National Fuel Mix")
        fuel_counts = ep.get("fuel_type_counts", {})
        if fuel_counts:
            fig = px.pie(names=list(fuel_counts.keys()),
                         values=list(fuel_counts.values()),
                         hole=0.4,
                         color_discrete_map={
                             "ELECTRIC":EV_COLOUR,"PETROL":PETROL_COLOUR,
                             "DIESEL":DIESEL_COLOUR,"HYBRID":HYBRID_COLOUR,
                         })
            fig.update_layout(height=340)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Efficiency tier pie 
        st.subheader("Fuel Efficiency Tier Distribution")
        eff_counts = fp.get("efficiency_tier_breakdown", {})
        if eff_counts:
            fig2 = px.pie(names=list(eff_counts.keys()),
                          values=list(eff_counts.values()),
                          hole=0.4,
                          color=list(eff_counts.keys()),
                          color_discrete_map={
                              "EXCELLENT":"#1abc9c","GOOD":"#2ecc71",
                              "AVERAGE":"#f39c12","POOR":"#e74c3c","N/A":"#95a5a6"
                          })
            fig2.update_layout(height=340)
            st.plotly_chart(fig2, use_container_width=True)

    # Average fuel consumption by fuel type
    st.subheader("Average Fuel Consumption by Fuel Type (L/100km)")
    avg_fc = ep.get("avg_fuel_consumption_by_fuel", {})
    # Remove zero/EV entries
    avg_fc = {k: v for k, v in avg_fc.items() if v and v > 0}
    if avg_fc:
        fig3 = px.bar(x=list(avg_fc.keys()), y=list(avg_fc.values()),
                      color=list(avg_fc.keys()),
                      color_discrete_map={
                          "PETROL":PETROL_COLOUR,"DIESEL":DIESEL_COLOUR,"HYBRID":HYBRID_COLOUR,
                      })
        fig3.update_layout(height=320, showlegend=False,
                           xaxis_title="Fuel Type", yaxis_title="Avg L/100km")
        st.plotly_chart(fig3, use_container_width=True)

    # GVM class breakdown
    st.subheader("GVM Class Breakdown")
    gvm_counts = hv.get("gvm_class_breakdown", {})
    if gvm_counts:
        fig4 = px.bar(x=list(gvm_counts.keys()), y=list(gvm_counts.values()),
                      color=list(gvm_counts.keys()),
                      color_discrete_sequence=PALETTE)
        fig4.update_layout(height=320, showlegend=False,
                           xaxis_title="GVM Class", yaxis_title="Count")
        st.plotly_chart(fig4, use_container_width=True)

    # Top origin countries
    st.subheader("Top Vehicle Origin Countries")
    top_origins = reg_report.get("import_profile", {}).get("top_origin_countries", {})
    if top_origins:
        orig_df = pd.DataFrame(top_origins.items(), columns=["Country","Count"])
        orig_df = orig_df.sort_values("Count", ascending=True)
        fig5 = px.bar(orig_df, x="Count", y="Country", orientation="h",
                      color="Count", color_continuous_scale="Purples")
        fig5.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)

    # Full regulatory summary CSV
    st.subheader("Regulatory Summary Table")
    reg_sum = load_csv("regulatory_summary.csv")
    if not reg_sum.empty:
        st.dataframe(reg_sum, use_container_width=True, hide_index=True)
        csv_bytes = reg_sum.to_csv(index=False).encode()
        st.download_button("⬇️ Download Regulatory Summary", csv_bytes,
                           "regulatory_summary.csv", "text/csv")


# PAGE: Pipeline Info


elif active == "pipeline":
    st.title("Pipeline Architecture")

    st.markdown("""
    ## NZ Infrastructure Data Pipeline & Anomaly Detection

    This project demonstrates an end-to-end production-grade data engineering pipeline
    applied to real New Zealand Transport Agency (NZTA) open data.

    ---

    ### Pipeline Steps
    """)

    steps = [
        ("Project Setup",         "Git repo, folder structure, `requirements.txt`", "✅ OK"),
        ("Extract & Load",         "`extract_load.py` — chunked CSV → SQLite `raw_vehicles`", "✅ OK"),
        ("Data Cleaning",          "`clean_sql.sql` + `run_cleaning.py` — standardise, flag, filter", "✅ OK"),
        ("Basic Anomaly Detection", "Z-score + Isolation Forest on aggregated counts", "✅ OK"),
        ("Pipeline Orchestration", "`main.py` — single command runs all steps", "✅ OK"),
        ("Feature Engineering",    "15+ derived features: fleet_age, reg_lag, region, efficiency_tier, gvm_class…", "✅ OK"),
        ("Data Quality Profiling", "Completeness / range / cross-column checks → quality score + grade", "✅ OK"),
        ("Advanced Anomaly Detection","Row-level Isolation Forest + LOF + expert rules + FC peer z-score", "✅ OK"),
        ("Trend Analysis",         "7 processed CSVs: EV adoption, fuel trends, regional fleet, seasonality…", "✅ OK"),
        ("Regulatory Insights",   "Emissions profile, fleet age, heavy vehicle compliance, efficiency policy", "✅ OK"),
        ("Streamlit Dashboard",   "This app — interactive multi-page analytics", "✅ OK"),
    ]

    for step, desc, status in steps:
        col1, col2, col3 = st.columns([1, 4, 0.5])
        col1.markdown(f"**{step}**")
        col2.markdown(desc)
        col3.markdown(status)

    st.markdown("---")
    st.subheader("Project Structure")
    st.code("""
nz_vehicle_pipeline/
├── data/
│   ├── raw/              Dataset.csv (NZTA source)
│   ├── processed/        All pipeline outputs (CSVs, JSON reports)
│   └── database.db       SQLite (raw_vehicles, cleaned_vehicles, engineered_vehicles)
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
├── main.py                     Full pipeline orchestrator
├── requirements.txt
└── README.md
    """)

    st.subheader("🔧 Tech Stack")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Data & Storage**")
        st.markdown("- Python 3.12\n- Pandas\n- SQLite (via sqlite3)\n- SQLAlchemy")
    with col2:
        st.markdown("**ML & Statistics**")
        st.markdown("- scikit-learn (IForest, LOF)\n- SciPy (Z-score)\n- NumPy")
    with col3:
        st.markdown("**Visualisation & App**")
        st.markdown("- Streamlit\n- Plotly Express\n- Plotly Graph Objects")

    st.markdown("---")
    st.subheader("📊 Dataset")
    st.markdown("""
    - **Source**: NZTA Motor Vehicle Register (Open Data)
    - **Size**: 356,035 vehicles
    - **Columns**: 40 raw → 45 engineered
    - **Coverage**: All currently registered vehicles in NZ (2025 snapshot)
    - **Key fields**: `MAKE`, `MODEL`, `MOTIVE_POWER`, `BODY_TYPE`, `VEHICLE_YEAR`,
      `FIRST_NZ_REGISTRATION_YEAR`, `TLA`, `GVM`, `FC_COMBINED`, `VEHICLE_USAGE`
    """)

    st.subheader("Database Tables")
    try:
        conn = sqlite3.connect(DB)
        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", conn
        )
        for t in tables["name"]:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            cols = len(conn.execute(f"PRAGMA table_info({t})").fetchall())
            st.write(f"**`{t}`** — {cnt:,} rows × {cols} columns")
        conn.close()
    except Exception as e:
        st.warning(f"Could not connect to DB: {e}")
