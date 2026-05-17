
import numpy as np
import pandas as pd
import plotly.express as px


def safe_float(x):

    try:
        return float(x)

    except:
        return np.nan


def parse_duur(x):

    try:
        return float(x)

    except:

        try:
            parts = str(x).split(":")
            parts = [float(p) for p in parts]

            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]

            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]

        except:
            return np.nan

    return np.nan


def find_best_exponent(df):

    exponents = np.arange(0.30, 1.01, 0.01)

    best_a = 0.7
    best_slope = 999999

    for a in exponents:

        adjusted = df["vo2"] / (df["gewicht"] ** a)

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


def scatter(df, x, y, selected, title, xlabel, ylabel, show_zscore=False):

    plot_df = df[[x, y, "naam"]].copy()

    plot_df = plot_df.dropna(subset=[x, y])

    plot_df["highlight"] = plot_df["naam"] == selected

    fig = px.scatter(
        plot_df,
        x=x,
        y=y,
        color="highlight",
        hover_name="naam",
        trendline="ols"
    )

    fig.update_layout(
        title=f"<b>{title}</b>",
        xaxis_title=xlabel,
        yaxis_title=ylabel
        showlegend=False
    )

    return fig
