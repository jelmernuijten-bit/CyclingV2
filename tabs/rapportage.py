# Updated Advanced U19 Dashboard
# Includes:
# - Secret key support
# - Safe clustering
# - Safe PCA
# - NaN cleaning
# - Stable indexing

from dash import Dash, html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from data_loader import load_data

app = Dash(__name__)
server = app.server

# =========================================
# SECRET KEY
# =========================================

server.secret_key = "cyclinglab_secret_2026"

# =========================================
# LAYOUT
# =========================================

app.layout = html.Div([

    dcc.Dropdown(
        id="db"
    ),

    dcc.Dropdown(
        id="name"
    ),

    html.Div(
        id="rapport-kpis"
    ),

    dcc.Graph(
        id="power-profile"
    ),

    html.Div(
        id="analysis-text",

        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(2, 1fr)",
            "gap": "20px"
        }
    )
])

# =========================================
# CALLBACK
# =========================================

@app.callback(

    Output("rapport-kpis", "children"),
    Output("power-profile", "figure"),
    Output("analysis-text", "children"),

    Input("db", "value"),
    Input("name", "value")
)

def update_dashboard(db, name):

    if not db or not name:

        return [], go.Figure(), []

    try:

        df = load_data(db)

        if len(df) < 10:

            return (
                [],
                go.Figure(),
                [html.H3("Dataset too small for advanced analytics.")]
            )

        possible_name_cols = [
            "naam",
            "name",
            "renner",
            "rider"
        ]

        name_col = None

        for col in possible_name_cols:

            if col in df.columns:
                name_col = col
                break

        if name_col is None:
            name_col = df.columns[-1]

        rider = df[
            df[name_col] == name
        ]

        if rider.empty:

            return [], go.Figure(), []

        rider = rider.iloc[0]

        # =========================================
        # SAFE VALUE HELPER
        # =========================================

        def get_col(options, default=0):

            for col in options:

                if col in rider.index:

                    try:
                        return float(rider[col])

                    except:
                        return default

            return default

        ftp = get_col(["mftp"])
        gewicht = get_col(["gewicht"], 1)

        ftp_kg = ftp / gewicht if gewicht else 0

        sprint = get_col(["okj_10s"])
        een_min = get_col(["okj_1min"])
        vijf_min = get_col(["okj_5min"])
        twintig = get_col(["okj_20m"])

        # =========================================
        # PERCENTILE HELPERS
        # =========================================

        def percentile_rank(series, value):

            series = series.dropna()

            return round(

                (
                    np.sum(series <= value)
                    / len(series)
                ) * 100,

                1
            )

        def normalize(x):
            return x / 100

        ftpkg_pct = percentile_rank(
            df["mftp"] / df["gewicht"],
            ftp_kg
        )

        sprint_pct = percentile_rank(
            df["okj_10s"],
            sprint
        )

        vijfmin_pct = percentile_rank(
            df["okj_5min"],
            vijf_min
        )

        twintig_pct = percentile_rank(
            df["okj_20m"],
            twintig
        )

        ftpkg_n = normalize(ftpkg_pct)
        sprint_n = normalize(sprint_pct)
        vijfmin_n = normalize(vijfmin_pct)
        twintig_n = normalize(twintig_pct)

        # =========================================
        # DECAY CURVES
        # =========================================

        fatigue_levels = [0, 7, 14, 21, 28]

        sprint_curve = [
            get_col(["okj_10s"]),
            get_col(["kj7_10s"]),
            get_col(["kj14_10s"]),
            get_col(["kj21_10s"]),
            get_col(["kj28_10s"])
        ]

        vijfmin_curve = [
            get_col(["okj_5min"]),
            get_col(["kj7_5m"]),
            get_col(["kj14_5m"]),
            get_col(["kj21_5m"]),
            get_col(["kj28_5m"])
        ]

        slope_10s = np.polyfit(
            fatigue_levels,
            sprint_curve,
            1
        )[0]

        slope_5m = np.polyfit(
            fatigue_levels,
            vijfmin_curve,
            1
        )[0]

        decay10_n = max(0, 100 + (slope_10s * 4)) / 100
        decay5_n = max(0, 100 + (slope_5m * 5)) / 100

        # =========================================
        # PROFILE SCORES
        # =========================================

        climber_score = round(

            (
                (ftpkg_n ** 1.8) * 0.45 +
                vijfmin_n * 0.30 +
                decay5_n * 0.25
            ) * 100,

            1
        )

        sprinter_score = round(

            (
                (sprint_n ** 1.8) * 0.50 +
                decay10_n * 0.30 +
                twintig_n * 0.20
            ) * 100,

            1
        )

        # =========================================
        # PROFILE SELECTION
        # =========================================

        profiles = {

            "Climber": climber_score,
            "Sprinter": sprinter_score
        }

        hoofdprofiel = max(
            profiles,
            key=profiles.get
        )

        # =========================================
        # CLUSTERING
        # =========================================

        cluster_data = df[[

            "okj_10s",
            "okj_1min",
            "okj_5min",
            "okj_20m",
            "mftp"

        ]]

        cluster_data = cluster_data.replace(
            [np.inf, -np.inf],
            np.nan
        ).fillna(0)

        kmeans = KMeans(
            n_clusters=5,
            random_state=42,
            n_init=10
        )

        clusters = kmeans.fit_predict(
            cluster_data
        )

        rider_cluster = clusters[
            rider.name
        ]

        # =========================================
        # PCA
        # =========================================

        pca_data = df[[

            "okj_10s",
            "okj_1min",
            "okj_5min",
            "okj_20m",
            "mftp"

        ]]

        pca_data = pca_data.replace(
            [np.inf, -np.inf],
            np.nan
        ).fillna(0)

        pca = PCA(
            n_components=3
        )

        pca.fit(
            pca_data
        )

        explained = pca.explained_variance_ratio_

        # =========================================
        # KPI CARDS
        # =========================================

        def card(title, value):

            return html.Div([

                html.Div(
                    title
                ),

                html.H2(
                    str(value)
                )

            ],

            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px"
            })

        kpis = [

            card("FTP", round(ftp)),
            card("FTP/kg", round(ftp_kg, 2)),
            card("Sprint", round(sprint)),
            card("5min", round(vijf_min))
        ]

        # =========================================
        # GRAPH
        # =========================================

        fig = go.Figure()

        fig.add_trace(

            go.Scatter(

                x=["10s", "5m"],

                y=[sprint, vijf_min],

                mode="lines+markers",

                name="Fresh"
            )
        )

        fig.add_trace(

            go.Scatter(

                x=["10s", "5m"],

                y=[
                    get_col(["kj28_10s"]),
                    get_col(["kj28_5m"])
                ],

                mode="lines+markers",

                name="28kJ"
            )
        )

        fig.update_layout(

            template="plotly_white",

            title="Advanced Durability Profile"
        )

        # =========================================
        # ANALYSIS CARDS
        # =========================================

        analysis = [

            card(
                "Primary Profile",
                hoofdprofiel
            ),

            card(
                "Climber Score",
                climber_score
            ),

            card(
                "Sprinter Score",
                sprinter_score
            ),

            card(
                "Cluster",
                rider_cluster
            ),

            card(
                "PCA Explosiveness",
                round(explained[0] * 100, 1)
            ),

            card(
                "PCA Aerobic",
                round(explained[1] * 100, 1)
            ),

            card(
                "PCA Durability",
                round(explained[2] * 100, 1)
            )
        ]

        return (
            kpis,
            fig,
            analysis
        )

    except Exception as e:

        return (
            [],
            go.Figure(),
            [html.H3(str(e))]
        )

if __name__ == "__main__":

    app.run_server(
        debug=True
    )
