import numpy as np
import pandas as pd
import plotly.express as px

from flask import request
import base64
import os

# =========================================
# CURRENT USER
# =========================================

def get_current_user():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:

        auth_type, credentials = auth_header.split()

        if auth_type.lower() != "basic":
            return None

        decoded = base64.b64decode(
            credentials
        ).decode("utf-8")

        username, password = decoded.split(":", 1)

        return username

    except:
        return None

# =========================================
# LOAD SEG RIDERS
# =========================================

def load_seg_riders():

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    file_path = os.path.join(
        base_dir,
        "allowed_seg_riders.txt"
    )

    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as f:

        return [
            line.strip()
            for line in f.readlines()
            if line.strip()
        ]

# =========================================
# SAFE FLOAT
# =========================================

def safe_float(x):

    try:
        return float(x)

    except:
        return np.nan

# =========================================
# PARSE DUUR
# =========================================

def parse_duur(x):

    try:
        return float(x)

    except:

        try:

            parts = str(x).split(":")
            parts = [float(p) for p in parts]

            if len(parts) == 3:

                return (
                    parts[0] * 3600 +
                    parts[1] * 60 +
                    parts[2]
                )

            elif len(parts) == 2:

                return (
                    parts[0] * 60 +
                    parts[1]
                )

        except:
            return np.nan

    return np.nan

# =========================================
# FIND BEST EXPONENT
# =========================================

def find_best_exponent(df):

    exponents = np.arange(0.30, 1.01, 0.01)

    best_a = 0.7
    best_slope = 999999

    for a in exponents:

        adjusted = df["vo2"] / (
            df["gewicht"] ** a
        )

        temp = pd.DataFrame({
            "gewicht": df["gewicht"],
            "adj": adjusted
        }).dropna()

        if len(temp) < 3:
            continue

        slope, intercept = np.polyfit(
            temp["gewicht"],
            temp["adj"],
            1
        )

        if abs(slope) < best_slope:

            best_slope = abs(slope)
            best_a = a

    return round(best_a, 2)

# =========================================
# SCATTER
# =========================================

def scatter(
    df,
    x,
    y,
    selected,
    title,
    xlabel,
    ylabel,
    show_zscore=False
):

    username = get_current_user()

    allowed_riders = load_seg_riders()

    plot_df = df[[x, y, "naam"]].copy()

    plot_df = plot_df.dropna(
        subset=[x, y]
    )

    # =========================================
    # SEG PRIVACY
    # =========================================

    if username == "SEG":

        plot_df["allowed"] = plot_df["naam"].isin(
            allowed_riders
        )

    else:

        plot_df["allowed"] = True

    plot_df["highlight"] = (
        plot_df["naam"] == selected
    )

    # =========================================
    # ALLOWED RIDERS
    # =========================================

    allowed_df = plot_df[
        plot_df["allowed"]
    ]

    # =========================================
    # HIDDEN RIDERS
    # =========================================

    hidden_df = plot_df[
        ~plot_df["allowed"]
    ]

    fig = px.scatter()

    # =========================================
    # HIDDEN POINTS
    # =========================================

    if len(hidden_df) > 0:

        fig.add_scatter(

            x=hidden_df[x],
            y=hidden_df[y],

            mode="markers",

            marker=dict(
                color="#1f77b4",
                size=8
            ),

            hoverinfo="skip",

            showlegend=False
        )

    # =========================================
    # ALLOWED POINTS
    # =========================================

    if len(allowed_df) > 0:

        fig2 = px.scatter(

            allowed_df,

            x=x,
            y=y,

            color="highlight",

            color_discrete_map={
                True: "red",
                False: "#1f77b4"
            },

            hover_name="naam",

            trendline="ols",

            labels={
                x: xlabel,
                y: ylabel
            }
        )

        for trace in fig2.data:
            fig.add_trace(trace)

    fig.update_traces(

        marker=dict(size=8),

        hovertemplate=
        "<b>%{hovertext}</b><br>" +
        f"{xlabel}: %{{x}}<br>" +
        f"{ylabel}: %{{y}}<extra></extra>"
    )

    fig.update_layout(

        title=f"<b>{title}</b>",

        xaxis_title=xlabel,
        yaxis_title=ylabel,

        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20
        ),

        plot_bgcolor="white",
        paper_bgcolor="#f4f6f8",

        showlegend=False
    )

    return fig
