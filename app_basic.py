import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Realisasi Anggaran",
    page_icon="📊",
    layout="wide"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .stMetric { background-color: #FFFFFF; padding: 1rem; border-radius: 8px; border: 1px solid #E2E8F0; }
    h1 { color: #1D4ED8; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data_anggaran.csv")
    bulan_order = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                   "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    df["bulan"] = pd.Categorical(df["bulan"], categories=bulan_order, ordered=True)
    return df

df_raw = load_data()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filter Data")

    all_units = sorted(df_raw["unit_kerja"].unique().tolist())
    selected_units = st.multiselect(
        "Unit Kerja",
        options=all_units,
        default=all_units
    )

    all_programs = sorted(df_raw["program"].unique().tolist())
    selected_programs = st.multiselect(
        "Program",
        options=all_programs,
        default=all_programs
    )

    all_bulan = df_raw["bulan"].cat.categories.tolist()
    available_bulan = [b for b in all_bulan if b in df_raw["bulan"].unique()]
    selected_bulan = st.multiselect(
        "Bulan",
        options=available_bulan,
        default=available_bulan
    )

    st.divider()
    st.markdown("### 📁 Tentang Data")
    st.caption("Data anggaran fiktif Kanwil DJPb | 6 unit kerja | 5 program | 6 bulan")

# ─── Filter Data ──────────────────────────────────────────────────────────────
df = df_raw[
    df_raw["unit_kerja"].isin(selected_units) &
    df_raw["program"].isin(selected_programs) &
    df_raw["bulan"].isin(selected_bulan)
].copy()

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("📊 Dashboard Realisasi Anggaran")
st.caption("Kantor Wilayah DJPb — Data Anggaran 2024")

if df.empty:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih. Silakan ubah filter di sidebar.")
    st.stop()

# ─── Helper ───────────────────────────────────────────────────────────────────
def fmt_rp(x):
    if x >= 1_000_000_000:
        return f"Rp {x/1_000_000_000:.1f} M"
    return f"Rp {x/1_000_000:.0f} jt"

# ─── KPI Metrics ──────────────────────────────────────────────────────────────
st.subheader("📌 Ringkasan Utama")

total_pagu      = df["pagu_anggaran"].sum()
total_realisasi = df["realisasi"].sum()
total_sisa      = df["sisa_anggaran"].sum()
avg_persen      = df["persen_realisasi"].mean()
persen_overall  = (total_realisasi / total_pagu * 100) if total_pagu > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pagu",        fmt_rp(total_pagu))
col2.metric("Total Realisasi",   fmt_rp(total_realisasi), f"{persen_overall:.1f}% dari pagu")
col3.metric("Sisa Anggaran",     fmt_rp(total_sisa))
col4.metric("Rata-rata % Real.", f"{avg_persen:.1f}%")

st.divider()

# ─── Chart 1: Realisasi per Unit Kerja ────────────────────────────────────────
st.subheader("🏢 Realisasi per Unit Kerja")

df_unit = (
    df.groupby("unit_kerja", as_index=False)
    .agg(pagu=("pagu_anggaran","sum"), realisasi=("realisasi","sum"))
)
df_unit["persen"] = (df_unit["realisasi"] / df_unit["pagu"] * 100).round(1)
df_unit = df_unit.sort_values("realisasi", ascending=True)

fig_unit = go.Figure()
fig_unit.add_trace(go.Bar(
    y=df_unit["unit_kerja"], x=df_unit["pagu"],
    name="Pagu", orientation="h",
    marker_color="#BFDBFE",
    text=df_unit["pagu"].apply(fmt_rp),
    textposition="outside"
))
fig_unit.add_trace(go.Bar(
    y=df_unit["unit_kerja"], x=df_unit["realisasi"],
    name="Realisasi", orientation="h",
    marker_color="#1D4ED8",
    text=df_unit["realisasi"].apply(fmt_rp),
    textposition="inside", textfont_color="white"
))
fig_unit.update_layout(
    barmode="overlay", height=380,
    margin=dict(l=0, r=120, t=10, b=10),
    legend=dict(orientation="h", y=1.08),
    plot_bgcolor="white",
    xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
    yaxis=dict(showgrid=False)
)
st.plotly_chart(fig_unit, use_container_width=True)

st.divider()

# ─── Chart 2: Tren Realisasi per Bulan ────────────────────────────────────────
st.subheader("📅 Tren Realisasi per Bulan")

df_bulan = (
    df.groupby("bulan", as_index=False, observed=True)
    .agg(pagu=("pagu_anggaran","sum"), realisasi=("realisasi","sum"))
)
df_bulan["persen"] = (df_bulan["realisasi"] / df_bulan["pagu"] * 100).round(1)
df_bulan = df_bulan.sort_values("bulan")

fig_tren = go.Figure()
fig_tren.add_trace(go.Scatter(
    x=df_bulan["bulan"].astype(str), y=df_bulan["realisasi"],
    mode="lines+markers+text",
    name="Realisasi",
    line=dict(color="#1D4ED8", width=2.5),
    marker=dict(size=8, color="#1D4ED8"),
    text=df_bulan["realisasi"].apply(fmt_rp),
    textposition="top center"
))
fig_tren.add_trace(go.Scatter(
    x=df_bulan["bulan"].astype(str), y=df_bulan["pagu"],
    mode="lines",
    name="Pagu",
    line=dict(color="#93C5FD", width=1.5, dash="dash"),
))
fig_tren.update_layout(
    height=340, margin=dict(l=0, r=20, t=20, b=10),
    legend=dict(orientation="h", y=1.08),
    plot_bgcolor="white",
    yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
    xaxis=dict(showgrid=False)
)
st.plotly_chart(fig_tren, use_container_width=True)

st.divider()

# ─── Chart 3: Heatmap % Realisasi Unit vs Bulan ───────────────────────────────
st.subheader("🗺️ Peta Panas — % Realisasi per Unit & Bulan")

df_heat = (
    df.groupby(["unit_kerja", "bulan"], observed=True, as_index=False)
    .agg(pagu=("pagu_anggaran","sum"), realisasi=("realisasi","sum"))
)
df_heat["persen"] = (df_heat["realisasi"] / df_heat["pagu"] * 100).round(1)
pivot = df_heat.pivot(index="unit_kerja", columns="bulan", values="persen")
pivot = pivot.reindex(columns=[c for c in df_raw["bulan"].cat.categories if c in pivot.columns])

fig_heat = px.imshow(
    pivot,
    color_continuous_scale=["#FEF3C7", "#F59E0B", "#1D4ED8"],
    zmin=0, zmax=100,
    text_auto=".1f",
    aspect="auto",
    labels=dict(color="% Realisasi")
)
fig_heat.update_layout(
    height=300, margin=dict(l=0, r=0, t=10, b=10),
    coloraxis_colorbar=dict(title="% Real.")
)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ─── Chart 4: Realisasi per Program ──────────────────────────────────────────
st.subheader("📋 Realisasi per Program")

df_prog = (
    df.groupby("program", as_index=False)
    .agg(pagu=("pagu_anggaran","sum"), realisasi=("realisasi","sum"))
)
df_prog["persen"] = (df_prog["realisasi"] / df_prog["pagu"] * 100).round(1)
df_prog = df_prog.sort_values("persen", ascending=False)

fig_prog = px.bar(
    df_prog, x="program", y="persen",
    color="persen",
    color_continuous_scale=["#FEF3C7", "#F59E0B", "#1D4ED8"],
    range_color=[0, 100],
    text="persen",
    labels={"persen": "% Realisasi", "program": "Program"},
)
fig_prog.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_prog.update_layout(
    height=320, margin=dict(l=0, r=0, t=20, b=10),
    showlegend=False, plot_bgcolor="white",
    yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#F1F5F9"),
    xaxis=dict(showgrid=False),
    coloraxis_showscale=False
)
st.plotly_chart(fig_prog, use_container_width=True)

st.divider()

# ─── Raw Data Table ───────────────────────────────────────────────────────────
with st.expander("🗂️ Lihat Data Mentah"):
    df_display = df.copy()
    df_display["pagu_anggaran"]    = df_display["pagu_anggaran"].apply(fmt_rp)
    df_display["realisasi"]        = df_display["realisasi"].apply(fmt_rp)
    df_display["sisa_anggaran"]    = df_display["sisa_anggaran"].apply(fmt_rp)
    df_display["persen_realisasi"] = df_display["persen_realisasi"].astype(str) + "%"
    st.dataframe(df_display, use_container_width=True, hide_index=True)

st.caption("Dashboard dibuat dengan Streamlit + Plotly")
