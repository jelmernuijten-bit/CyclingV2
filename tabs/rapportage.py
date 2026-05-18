# rapportage.py

```python
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_PATH = "Junior_1e_jaars_man.db"


@st.cache_data

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM riders", conn)
    conn.close()
    return df


# --------------------------------------------------
# HELPERS
# --------------------------------------------------


def get_col(row, possible_cols, default=None):
    for col in possible_cols:
        if col in row.index:
            value = row[col]
            if pd.notna(value):
                return value
    return default


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------


df = load_data()

st.title("Rapportage")

if df.empty:
    st.warning("Geen data gevonden")
    st.stop()


# --------------------------------------------------
# RIDER SELECTIE
# --------------------------------------------------

riders = sorted(df["naam"].dropna().unique())
selected_rider = st.selectbox("Selecteer renner", riders)

rider_df = df[df["naam"] == selected_rider]

if rider_df.empty:
    st.warning("Geen data voor deze renner")
    st.stop()


# Beste test kiezen
if "mftp" in rider_df.columns:
    rider = rider_df.sort_values("mftp", ascending=False).iloc[0]
else:
    rider = rider_df.iloc[0]


# --------------------------------------------------
# KPI'S
# --------------------------------------------------

st.subheader("KPI's")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "mFTP",
        get_col(rider, ["mftp", "ftp"], "-")
    )

with col2:
    st.metric(
        "VO2",
        get_col(rider, ["vo2", "vo2max"], "-")
    )

with col3:
    st.metric(
        "1 min",
        get_col(rider, ["okj_1min", "okj_1m"], "-")
    )

with col4:
    st.metric(
        "5 min",
        get_col(rider, ["okj_5min", "okj_5m"], "-")
    )


# --------------------------------------------------
# POWER PROFILE
# --------------------------------------------------

st.subheader("Power Profile")

x_labels = ["1 min", "5 min"]
x = [1, 5]

okj_values = [
    get_col(rider, ["okj_1min", "okj_1m"]),
    get_col(rider, ["okj_5min", "okj_5m"]),
]

kj7_values = [
    get_col(rider, ["7kj_1min", "7kj_1m"]),
    get_col(rider, ["7kj_5min", "7kj_5m"]),
]

kj21_values = [
    get_col(rider, ["21kj_1min", "21kj_1m"]),
    get_col(rider, ["21kj_5min", "21kj_5m"]),
]

kj28_values = [
    get_col(rider, ["28kj_1min", "28kj_1m"]),
    get_col(rider, ["28kj_5min", "28kj_5m"]),
]

fig, ax = plt.subplots(figsize=(8, 5))


# Plot helper

def safe_plot(values, label):
    if any(v is not None for v in values):
        ax.plot(x, values, marker="o", linewidth=2, label=label)


safe_plot(okj_values, "OKJ")
safe_plot(kj7_values, "7 KJ")
safe_plot(kj21_values, "21 KJ")
safe_plot(kj28_values, "28 KJ")


ax.set_xticks(x)
ax.set_xticklabels(x_labels)
ax.set_ylabel("W/kg")
ax.set_title("Power Profile")
ax.grid(True, alpha=0.3)
ax.legend()

st.pyplot(fig)


# --------------------------------------------------
# DATA TABEL
# --------------------------------------------------

st.subheader("Ruwe data")

st.dataframe(rider_df)

```
