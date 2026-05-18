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

            return (
                [],
                go.Figure(),
                ""
            )

        try:

            df = load_data(db)

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

                return (
                    [],
                    go.Figure(),
                    ""
                )

            rider = rider.iloc[0]

            def get_col(options, default=0):

                for col in options:

                    if col in rider.index:

                        value = rider[col]

                        try:
                            return float(value)

                        except:
                            return default

                return default

            ftp = int(round(
                get_col([
                    "mftp",
                    "ftp",
                    "ftp_adj"
                ]),
                0
            ))

            gewicht = round(
                get_col([
                    "gewicht",
                    "weight"
                ]),
                1
            )

            ftp_kg = round(
                ftp / gewicht,
                2
            ) if gewicht else 0

            sprint = int(round(
                get_col([
                    "okj_10s",
                    "v5"
                ]),
                0
            ))

            een_min = int(round(
                get_col([
                    "okj_1min",
                    "v3"
                ]),
                0
            ))

            vijf_min = int(round(
                get_col([
                    "okj_5min",
                    "v1"
                ]),
                0
            ))

            twintig = int(round(
                get_col([
                    "okj_20m",
                    "v2"
                ]),
                0
            ))

            kj28_10s = get_col(["kj28_10s"])
            kj28_5m = get_col(["kj28_5m"])
            kj28_20m = get_col(["kj28_20m"])

            fatigue_5m = 0

            if vijf_min > 0:

                fatigue_5m = round(
                    (
                        (vijf_min - kj28_5m)
                        / vijf_min
                    ) * 100,
                    1
                )

            sprint_decay = 0

            if sprint > 0:

                sprint_decay = round(
                    (
                        (sprint - kj28_10s)
                        / sprint
                    ) * 100,
                    1
                )

            def percentile_rank(series, value):

                return round(
                    (
                        np.sum(series <= value)
                        / len(series)
                    ) * 100,
                    1
                )

            def normalize(value):
                return value / 100

            ftpkg_pct = percentile_rank(
                df["mftp"] / df["gewicht"],
                ftp_kg
            )

            ftp_pct = percentile_rank(
                df["mftp"],
                ftp
            )

            sprint_pct = percentile_rank(
                df["okj_10s"],
                sprint
            )

            eenmin_pct = percentile_rank(
                df["okj_1min"],
                een_min
            )

            vijfmin_pct = percentile_rank(
                df["okj_5min"],
                vijf_min
            )

            twintig_pct = percentile_rank(
                df["okj_20m"],
                twintig
            )

            gewicht_pct = percentile_rank(
                df["gewicht"],
                gewicht
            )

            kj28_20m_pct = percentile_rank(
                df["kj28_20m"],
                kj28_20m
            )

            ftpkg_n = normalize(ftpkg_pct)
            ftp_n = normalize(ftp_pct)
            sprint_n = normalize(sprint_pct)
            eenmin_n = normalize(eenmin_pct)
            vijfmin_n = normalize(vijfmin_pct)
            twintig_n = normalize(twintig_pct)

            gewicht_light_n = normalize(
                100 - gewicht_pct
            )

            endurance_n = normalize(
                kj28_20m_pct
            )

            fatigue_levels = [0, 7, 14, 21, 28]

            sprint_curve = [
                get_col(["okj_10s"]),
                get_col(["kj7_10s"]),
                get_col(["kj14_10s"]),
                get_col(["kj21_10s"]),
                get_col(["kj28_10s"])
            ]

            eenmin_curve = [
                get_col(["okj_1min"]),
                get_col(["kj7_1m"]),
                get_col(["kj14_1m"]),
                get_col(["kj21_1m"]),
                get_col(["kj28_1m"])
            ]

            vijfmin_curve = [
                get_col(["okj_5min"]),
                get_col(["kj7_5m"]),
                get_col(["kj14_5m"]),
                get_col(["kj21_5m"]),
                get_col(["kj28_5m"])
            ]

            twintig_curve = [
                get_col(["okj_20m"]),
                get_col(["kj7_20m"]),
                get_col(["kj14_20m"]),
                get_col(["kj21_20m"]),
                get_col(["kj28_20m"])
            ]

            slope_10s = np.polyfit(
                fatigue_levels,
                sprint_curve,
                1
            )[0]

            slope_1m = np.polyfit(
                fatigue_levels,
                eenmin_curve,
                1
            )[0]

            slope_5m = np.polyfit(
                fatigue_levels,
                vijfmin_curve,
                1
            )[0]

            slope_20m = np.polyfit(
                fatigue_levels,
                twintig_curve,
                1
            )[0]

            decay10_n = max(0, 100 + (slope_10s * 4)) / 100
            decay1_n = max(0, 100 + (slope_1m * 4)) / 100
            decay5_n = max(0, 100 + (slope_5m * 5)) / 100
            decay20_n = max(0, 100 + (slope_20m * 6)) / 100

            ftpkg_z = round(
                (
                    ftp_kg - (df["mftp"] / df["gewicht"]).mean()
                )
                /
                (df["mftp"] / df["gewicht"]).std(),
                2
            )

            sprint_z = round(
                (
                    sprint - df["okj_10s"].mean()
                )
                /
                df["okj_10s"].std(),
                2
            )

            vijfmin_z = round(
                (
                    vijf_min - df["okj_5min"].mean()
                )
                /
                df["okj_5min"].std(),
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

            if (
                sprint_n >= 0.80
                and decay10_n >= 0.80
            ):
                synergy_bonus += 5

            climber_score = round(
                (
                    (ftpkg_n ** 1.8) * 0.35 +
                    vijfmin_n * 0.25 +
                    decay5_n * 0.20 +
                    gewicht_light_n * 0.10 +
                    endurance_n * 0.10
                ) * 100 + synergy_bonus,
                1
            )

            sprinter_score = round(
                (
                    (sprint_n ** 1.8) * 0.40 +
                    eenmin_n * 0.20 +
                    decay10_n * 0.20 +
                    (1 - gewicht_light_n) * 0.10 +
                    decay1_n * 0.10
                ) * 100,
                1
            )

            tt_score = round(
                (
                    ftp_n * 0.30 +
                    twintig_n * 0.25 +
                    endurance_n * 0.20 +
                    decay20_n * 0.15 +
                    decay5_n * 0.10
                ) * 100,
                1
            )

            classics_score = round(
                (
                    sprint_n * 0.20 +
                    ftpkg_n * 0.20 +
                    decay10_n * 0.20 +
                    decay5_n * 0.20 +
                    endurance_n * 0.20
                ) * 100,
                1
            )

            puncheur_score = round(
                (
                    vijfmin_n * 0.30 +
                    eenmin_n * 0.25 +
                    sprint_n * 0.15 +
                    decay5_n * 0.20 +
                    ftpkg_n * 0.10
                ) * 100,
                1
            )

            diesel_score = round(
                (
                    ftp_n * 0.30 +
                    twintig_n * 0.30 +
                    endurance_n * 0.20 +
                    decay20_n * 0.20
                ) * 100,
                1
            )

            profile_scores = {
                "Climber": climber_score,
                "Sprinter": sprinter_score,
                "Time Trialist": tt_score,
                "Classics Rider": classics_score,
                "Puncheur": puncheur_score,
                "Diesel": diesel_score
            }

            hoofdprofiel = max(
                profile_scores,
                key=profile_scores.get
            )

            hoofdscore = profile_scores[
                hoofdprofiel
            ]

            sorted_profiles = sorted(
                profile_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )

            second_profile = sorted_profiles[1][0]
            second_score = sorted_profiles[1][1]

            rarity_score = round(
                abs(ftpkg_z) *
                abs(sprint_z) *
                abs(vijfmin_z),
                2
            )

            if rarity_score >= 12:
                rarity_label = "Extremely Rare Phenotype"

            elif rarity_score >= 7:
                rarity_label = "Rare Rider Type"

            elif rarity_score >= 4:
                rarity_label = "Above Average Profile"

            else:
                rarity_label = "Common Profile"

            cluster_data = df[[
                "okj_10s",
                "okj_1min",
                "okj_5min",
                "okj_20m",
                "mftp"
            ]].fillna(0)

            kmeans = KMeans(
                n_clusters=5,
                random_state=42,
                n_init=10
            )

            clusters = kmeans.fit_predict(cluster_data)

            rider_cluster = clusters[
                rider.name
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
                "mftp",
                "kj28_20m"
            ]].fillna(0)

            pca = PCA(n_components=3)

            pca.fit(pca_data)

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

                    html.Div(
                        str(value),
                        style={
                            "fontSize": "28px",
                            "fontWeight": "bold"
                        }
                    )

                ],

                style={
                    "backgroundColor": "white",
                    "padding": "20px",
                    "borderRadius": "10px",
                    "boxShadow": "0 1px 4px rgba(0,0,0,0.1)"
                })

            kpis = [
                card("FTP", f"{ftp} W"),
                card("FTP/kg", f"{ftp_kg:.2f}"),
                card("10s", f"{sprint} W"),
                card("20m", f"{twintig} W")
            ]

            labels = [
                "10s",
                "1m",
                "5m",
                "20m"
            ]

            fig = go.Figure()

            lijnen = [
                {
                    "naam": "0kj",
                    "kleur": "#000000",
                    "cols": [
                        "okj_10s",
                        "okj_1min",
                        "okj_5min",
                        "okj_20m"
                    ]
                },
                {
                    "naam": "28kj",
                    "kleur": "#f4a261",
                    "cols": [
                        "kj28_10s",
                        "kj28_1m",
                        "kj28_5m",
                        "kj28_20m"
                    ]
                }
            ]

            for lijn in lijnen:

                values = [
                    get_col([lijn["cols"][0]]),
                    get_col([lijn["cols"][1]]),
                    get_col([lijn["cols"][2]]),
                    get_col([lijn["cols"][3]])
                ]

                fig.add_trace(
                    go.Scatter(
                        x=labels,
                        y=values,
                        mode="lines+markers",
                        line={
                            "width": 2,
                            "color": lijn["kleur"]
                        },
                        marker={
                            "size": 6
                        },
                        name=lijn["naam"]
                    )
                )

            fig.update_layout(
                title="Advanced Power & Durability Profile",
                template="plotly_white",
                height=550,
                paper_bgcolor="#f4f6f8",
                plot_bgcolor="white",
                hovermode="x unified"
            )

            analysis = [

                card(
                    "Primary Profile",
                    f"{hoofdprofiel} ({hoofdscore}%)"
                ),

                card(
                    "Secondary Profile",
                    f"{second_profile} ({second_score}%)"
                ),

                card(
                    "Rarity",
                    rarity_label
                ),

                card(
                    "AI Cluster",
                    cluster_labels.get(
                        rider_cluster,
                        "Unknown"
                    )
                ),

                card(
                    "PCA Explosiveness",
                    f"{round(explained[0]*100,1)}%"
                ),

                card(
                    "PCA Aerobic",
                    f"{round(explained[1]*100,1)}%"
                ),

                card(
                    "PCA Durability",
                    f"{round(explained[2]*100,1)}%"
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
                )
            ]

            return (
                kpis,
                fig,
                analysis
            )

        except Exception as e:

            print(e)

            return (
                [],
                px.scatter(),
                str(e)
            )
