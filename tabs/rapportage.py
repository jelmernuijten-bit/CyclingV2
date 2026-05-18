from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from data_loader import load_data

# =========================================
# LAYOUT
# =========================================

def rapportage_layout():

    return html.Div([

        html.Div(
            id="rapport-kpis",

            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(4, 1fr)",
                "gap": "15px",
                "marginBottom": "20px"
            }
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
# CALLBACKS
# =========================================

def register_rapportage_callbacks(app):

    @app.callback(

        Output("rapport-kpis", "children"),
        Output("power-profile", "figure"),
        Output("analysis-text", "children"),

        Input("db", "value"),
        Input("name", "value")
    )

    def update_rapportage(db, name):

        if not db or not name:

            return [], go.Figure(), []

        try:

            df = load_data(db)

            if len(df) < 5:

                return (
                    [],
                    go.Figure(),
                    [html.H3("Dataset too small.")]
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

            rider_df = df[
                df[name_col] == name
            ]

            if rider_df.empty:

                return [], go.Figure(), []

            rider = rider_df.iloc[0]

            def get_col(options, default=0):

                for col in options:

                    if col in rider.index:

                        try:
                            return float(rider[col])

                        except:
                            return default

                return default

            ftp = get_col(["mftp", "ftp"])

            gewicht = get_col([
                "gewicht",
                "weight"
            ], 1)

            ftp_kg = round(
                ftp / gewicht,
                2
            ) if gewicht else 0

            sprint = get_col(["okj_10s"])
            vijf_min = get_col(["okj_5min"])
            twintig = get_col(["okj_20m"])

            def percentile_rank(series, value):

                series = series.replace(
                    [np.inf, -np.inf],
                    np.nan
                ).dropna()

                return round(
                    (
                        np.sum(series <= value)
                        / len(series)
                    ) * 100,
                    1
                )

            sprint_pct = percentile_rank(
                df["okj_10s"],
                sprint
            )

            ftpkg_pct = percentile_rank(
                df["mftp"] / df["gewicht"],
                ftp_kg
            )

            vijfmin_pct = percentile_rank(
                df["okj_5min"],
                vijf_min
            )

            twintig_pct = percentile_rank(
                df["okj_20m"],
                twintig
            )

            sprint_n = sprint_pct / 100
            ftpkg_n = ftpkg_pct / 100
            vijfmin_n = vijfmin_pct / 100
            twintig_n = twintig_pct / 100

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

            decay10 = round(
                max(0, 100 + (slope_10s * 4)),
                1
            )

            decay5 = round(
                max(0, 100 + (slope_5m * 5)),
                1
            )

            decay10_n = decay10 / 100
            decay5_n = decay5 / 100

            ftpkg_z = round(
                (
                    ftp_kg
                    - (
                        df["mftp"]
                        / df["gewicht"]
                    ).mean()
                )
                /
                (
                    df["mftp"]
                    / df["gewicht"]
                ).std(),
                2
            )

            sprint_z = round(
                (
                    sprint
                    - df["okj_10s"].mean()
                )
                /
                df["okj_10s"].std(),
                2
            )

            synergy_bonus = 0

            if (
                ftpkg_n >= 0.85
                and sprint_n >= 0.70
            ):
                synergy_bonus += 6

            if (
                vijfmin_n >= 0.85
                and decay5_n >= 0.85
            ):
                synergy_bonus += 5

            climber_score = round(
                (
                    (ftpkg_n ** 1.8) * 0.45 +
                    vijfmin_n * 0.30 +
                    decay5_n * 0.25
                ) * 100 + synergy_bonus,
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

            puncheur_score = round(
                (
                    vijfmin_n * 0.35 +
                    sprint_n * 0.25 +
                    decay5_n * 0.20 +
                    ftpkg_n * 0.20
                ) * 100,
                1
            )

            profiles = {

                "Climber": climber_score,
                "Sprinter": sprinter_score,
                "Puncheur": puncheur_score
            }

            hoofdprofiel = max(
                profiles,
                key=profiles.get
            )

            hoofdscore = profiles[
                hoofdprofiel
            ]

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
                rider_df.index[0]
            ]

            cluster_labels = {

                0: "Sprint Cluster",
                1: "Climber Cluster",
                2: "TT Cluster",
                3: "Puncher Cluster",
                4: "Allround Cluster"
            }

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

            def card(title, value):

                return html.Div([

                    html.Div(
                        title,

                        style={
                            "fontSize": "14px",
                            "color": "#666"
                        }
                    ),

                    html.H2(
                        str(value)
                    )

                ],

                style={

                    "backgroundColor": "white",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.1)"
                })

            kpis = [

                card("FTP", round(ftp)),
                card("FTP/kg", ftp_kg),
                card("Sprint", round(sprint)),
                card("5min", round(vijf_min))
            ]

            fig = go.Figure()

            fig.add_trace(

                go.Scatter(

                    x=["10s", "5m"],

                    y=[
                        sprint,
                        vijf_min
                    ],

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

                title="Advanced Durability Profile",

                height=500
            )

            analysis = [

                card(
                    "Primary Profile",
                    f"{hoofdprofiel} ({hoofdscore}%)"
                ),

                card(
                    "Cluster",
                    cluster_labels.get(
                        rider_cluster,
                        "Unknown"
                    )
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
                    "Puncheur Score",
                    puncheur_score
                ),

                card(
                    "Sprint Durability",
                    decay10
                ),

                card(
                    "VO2 Durability",
                    decay5
                ),

                card(
                    "FTP/kg Z-Score",
                    ftpkg_z
                ),

                card(
                    "Sprint Z-Score",
                    sprint_z
                ),

                card(
                    "PCA Explosiveness",
                    f"{round(explained[0] * 100,1)}%"
                ),

                card(
                    "PCA Aerobic",
                    f"{round(explained[1] * 100,1)}%"
                ),

                card(
                    "PCA Durability",
                    f"{round(explained[2] * 100,1)}%"
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
