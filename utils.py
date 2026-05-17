import numpy as np
import pandas as pd
import plotly.express as px

from flask import request
import base64
import requests

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

def load_seg_riders(db_name=None):

    url = (
        "https://drive.google.com/uc?export=download&id="
        "1tWHqT-8taxrMedpIbBGqgmFrCqykl86v"
    )

    try:

        response = requests.get(url)

        text = response.text

        riders = [

            line.strip()

            for line in text.splitlines()

            if line.strip()
        ]

        print("SEG riders:", riders)

        return riders

    except Exception as e:

        print(
            "SEG riders fout:",
            e
        )

        return []

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

            # =========================================
            # HH:MM:SS
            # =========================================

            if len(parts) == 3:

                return (
                    parts[0] * 3600 +
                    parts[1] * 60 +
                    parts[2]
                )

            # =========================================
            # UREN:MINUTEN
            # =========================================

            elif len(parts) == 2:

                return (
                    parts[0] * 3600 +
                    parts[1] * 60
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
    db_name=None,
    show_zscore=False
):

    username = get_current_user()

    allowed_riders = load_seg_riders()

    plot_df = df[[x, y, "naam"]].copy()

    plot_df = plot_df.dropna(
        subset=[x, y]
    )

    # =========================================
    # SEG FILTER
    # =========================================

    if username == "SEG":

        allowed_clean = [

            r.strip().lower()

            for r in allowed_riders
        ]

        plot_df["allowed"] = (

            plot_df["naam"]
            .str.strip()
            .str.lower()
            .isin(allowed_clean)
        )

    else:

        plot_df["allowed"] = True

    plot_df["highlight"] = (
        plot_df["naam"] == selected
    )

    # =========================================
    # SPLIT DATA
    # =========================================

    allowed_df = plot_df[
        plot_df["allowed"]
    ]

    hidden_df = plot_df[
        ~plot_df["allowed"]
    ]

    fig = px.scatter()

    # =========================================
    # HIDDEN RIDERS
    # =========================================

    if len(hidden_df) > 0:

        fig.add_scatter(

            x=hidden_df[x],
            y=hidden_df[y],

            mode="markers",

            marker=dict(
                color="gray",
                size=5,
                opacity=0.25
            ),

            hoverinfo="skip",

            showlegend=False
        )

    # =========================================
    # ALLOWED RIDERS
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

            labels={
                x: xlabel,
                y: ylabel
            }
        )

        for trace in fig2.data:

            fig.add_trace(trace)

    # =========================================
    # TRENDLINE
    # =========================================

    trend_df = plot_df.dropna(
        subset=[x, y]
    )

    if len(trend_df) > 2:

        slope, intercept = np.polyfit(
            trend_df[x],
            trend_df[y],
            1
        )

        x_vals = np.array([
            trend_df[x].min(),
            trend_df[x].max()
        ])

        y_vals = slope * x_vals + intercept

        fig.add_scatter(

            x=x_vals,
            y=y_vals,

            mode="lines",

            line=dict(
                color="black",
                width=2
            ),

            hoverinfo="skip",

            showlegend=False
        )

    # =========================================
    # MARKER SIZES
    # =========================================

    for trace in fig.data:

        if trace.name == "True":

            trace.marker.size = 14

        elif trace.name == "False":

            trace.marker.size = 8

    # =========================================
    # HOVER
    # =========================================

    fig.update_traces(

        hovertemplate=
        "<b>%{hovertext}</b><br>" +
        f"{xlabel}: %{{x}}<br>" +
        f"{ylabel}: %{{y}}<extra></extra>"
    )

    # =========================================
    # LAYOUT
    # =========================================

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

    # =========================================
    # Z-SCORE
    # =========================================

    if selected:

        sel = plot_df[
            plot_df["naam"] == selected
        ]

        if not sel.empty and len(plot_df) > 2:

            x0 = sel.iloc[0][x]
            y0 = sel.iloc[0][y]

            slope, intercept = np.polyfit(
                plot_df[x],
                plot_df[y],
                1
            )

            y_trend = (
                slope * x0 +
                intercept
            )

            fig.add_shape(

                type="line",

                x0=x0,
                y0=y0,

                x1=x0,
                y1=y_trend,

                line=dict(
                    color="red",
                    width=2,
                    dash="dot"
                )
            )

            predicted_all = (
                slope * plot_df[x] +
                intercept
            )

            residuals = (
                plot_df[y] -
                predicted_all
            )

            residual_std = residuals.std()

            if residual_std > 0:

                zscore = (
                    y0 - y_trend
                ) / residual_std

                fig.add_annotation(

                    x=x0,
                    y=y0,

                    text=f"z = {zscore:.2f}",

                    showarrow=False,

                    yshift=18,

                    font=dict(
                        color="red",
                        size=13
                    )
                )

                if show_zscore:

                    fig.update_layout(

                        title=(
                            f"<b>{title} "
                            f"({zscore:+.2f})</b>"
                        )
                    )

    # =========================================
    # FORMAT DUUR AXIS
    # =========================================

    if x == "duur":

        fig.update_xaxes(
            tickformat=".1f"
        )

    return fig
