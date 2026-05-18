from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

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
                "padding": "20px",
                "backgroundColor": "white",
                "borderRadius": "10px",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.1)"
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

            # =========================================
            # LOAD DATA
            # =========================================

            df = load_data(db)

            # =========================================
            # FIND NAME COLUMN
            # =========================================

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

            # =========================================
            # SELECT RIDER
            # =========================================

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

            # =========================================
            # SAFE VALUE HELPER
            # =========================================

            def get_col(options, default=0):

                for col in options:

                    if col in rider.index:

                        value = rider[col]

                        try:
                            return float(value)

                        except:
                            return default

                return default

            # =========================================
            # KPI VALUES
            # =========================================

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

            # =========================================
            # FATIGUE VALUES
            # =========================================

            kj28_10s = get_col([
                "kj28_10s"
            ])

            kj28_5m = get_col([
                "kj28_5m"
            ])

            kj28_20m = get_col([
                "kj28_20m"
            ])

            # =========================================
            # FATIGUE METRICS
            # =========================================

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

            # =========================================
            # PERCENTILE FUNCTIONS
            # =========================================

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

            # =========================================
            # DATABASE PERCENTILES
            # =========================================

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

            # =========================================
            # FATIGUE SCORES
            # =========================================

            fatigue_score = max(
                0,
                100 - (fatigue_5m * 8)
            )

            durability_score = max(
                0,
                100 - (sprint_decay * 10)
            )

            # =========================================
            # NORMALIZED SCORES
            # =========================================

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

            fatigue_n = normalize(
                fatigue_score
            )

            durability_n = normalize(
                durability_score
            )

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

            # =========================================
            # DECAY SLOPES
            # =========================================

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

            # =========================================
            # DECAY SCORES
            # =========================================

            decay_10s_score = max(
                0,
                100 + (slope_10s * 4)
            )

            decay_1m_score = max(
                0,
                100 + (slope_1m * 4)
            )

            decay_5m_score = max(
                0,
                100 + (slope_5m * 5)
            )

            decay_20m_score = max(
                0,
                100 + (slope_20m * 6)
            )

            decay10_n = decay_10s_score / 100
            decay1_n = decay_1m_score / 100
            decay5_n = decay_5m_score / 100
            decay20_n = decay_20m_score / 100

            # =========================================
            # PROFILE SCORES
            # =========================================

            climber_score = round(

                (
                    ftpkg_n * 0.30 +
                    vijfmin_n * 0.25 +
                    decay5_n * 0.20 +
                    gewicht_light_n * 0.15 +
                    fatigue_n * 0.10
                ) * 100,

                1
            )

            sprinter_score = round(

                (
                    sprint_n * 0.35 +
                    eenmin_n * 0.20 +
                    decay10_n * 0.25 +
                    durability_n * 0.10 +
                    (1 - gewicht_light_n) * 0.10
                ) * 100,

                1
            )

            tt_score = round(

                (
                    ftp_n * 0.25 +
                    twintig_n * 0.25 +
                    endurance_n * 0.20 +
                    decay20_n * 0.20 +
                    fatigue_n * 0.10
                ) * 100,

                1
            )

            classics_score = round(

                (
                    sprint_n * 0.20 +
                    ftpkg_n * 0.20 +
                    twintig_n * 0.20 +
                    decay10_n * 0.15 +
                    decay5_n * 0.15 +
                    durability_n * 0.10
                ) * 100,

                1
            )

            puncheur_score = round(

                (
                    vijfmin_n * 0.30 +
                    eenmin_n * 0.25 +
                    sprint_n * 0.10 +
                    decay5_n * 0.20 +
                    ftpkg_n * 0.15
                ) * 100,

                1
            )

            diesel_score = round(

                (
                    ftp_n * 0.25 +
                    twintig_n * 0.25 +
                    endurance_n * 0.20 +
                    decay20_n * 0.20 +
                    fatigue_n * 0.10
                ) * 100,

                1
            )

            # =========================================
            # SCORE OVERVIEW
            # =========================================

            profile_scores = {

                "Climber": climber_score,
                "Sprinter": sprinter_score,
                "Time Trialist": tt_score,
                "Classics Rider": classics_score,
                "Puncheur": puncheur_score,
                "Diesel": diesel_score
            }

            # =========================================
            # BEST PROFILE
            # =========================================

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

            # =========================================
            # SUBTYPES
            # =========================================

            subtypes = []

            if fatigue_score >= 75:

                subtypes.append(
                    "Fatigue Resistant"
                )

            if (

                sprint_pct >= 85
                and eenmin_pct >= 85

            ):

                subtypes.append(
                    "Anaerobic"
                )

            if endurance_n >= 0.80:

                subtypes.append(
                    "Endurance"
                )

            if (

                sprint_pct >= 80
                and vijfmin_pct >= 75

            ):

                subtypes.append(
                    "Explosive"
                )

            if gewicht_light_n >= 0.80:

                subtypes.append(
                    "Lightweight"
                )

            if durability_score >= 80:

                subtypes.append(
                    "Durable"
                )

            score_spread = (

                max(profile_scores.values())
                - min(profile_scores.values())
            )

            if score_spread <= 15:

                subtypes.append(
                    "Allround"
                )

            # =========================================
            # DECAY ARCHETYPES
            # =========================================

            decay_tags = []

            if (

                sprint_pct >= 85
                and decay10_n >= 0.80

            ):

                decay_tags.append(
                    "Repeatable Sprinter"
                )

            if (

                sprint_pct >= 90
                and decay10_n <= 0.55

            ):

                decay_tags.append(
                    "One Shot Sprinter"
                )

            if (

                ftpkg_n >= 0.85
                and decay5_n >= 0.85

            ):

                decay_tags.append(
                    "Fatigue Climber"
                )

            if (

                decay20_n >= 0.90
                and endurance_n >= 0.85

            ):

                decay_tags.append(
                    "Durable Engine"
                )

            if (

                sprint_pct >= 80
                and decay1_n <= 0.50

            ):

                decay_tags.append(
                    "Anaerobic Fader"
                )

            if (

                decay20_n >= 0.85
                and ftp_n >= 0.80

            ):

                decay_tags.append(
                    "Diesel Durability"
                )

            if (

                decay5_n >= 0.90
                and fatigue_n >= 0.90

            ):

                decay_tags.append(
                    "Clutch Performer"
                )

            # =========================================
            # SUBTYPE STRING
            # =========================================

            if len(subtypes) > 0:

                subtype = " / ".join(subtypes)

            else:

                subtype = "Balanced"

            # =========================================
            # KPI CARD HELPER
            # =========================================

            def card(title, value):

                return html.Div(

                    [

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
                    }
                )

            # =========================================
            # KPI CARDS
            # =========================================

            kpis = [

                card("FTP", f"{ftp} W"),

                card("FTP/kg", f"{ftp_kg:.2f}"),

                card("10s", f"{sprint} W"),

                card("20m", f"{twintig} W")
            ]

            # =========================================
            # POWER PROFILE GRAPH
            # =========================================

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
                    "naam": "7kj",
                    "kleur": "#e63946",
                    "cols": [
                        "kj7_10s",
                        "kj7_1m",
                        "kj7_5m",
                        "kj7_20m"
                    ]
                },

                {
                    "naam": "14kj",
                    "kleur": "#457b9d",
                    "cols": [
                        "kj14_10s",
                        "kj14_1m",
                        "kj14_5m",
                        "kj14_20m"
                    ]
                },

                {
                    "naam": "21kj",
                    "kleur": "#2a9d8f",
                    "cols": [
                        "kj21_10s",
                        "kj21_1m",
                        "kj21_5m",
                        "kj21_20m"
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

                title="Power Profile & Durability",

                template="plotly_white",

                height=550,

                paper_bgcolor="#f4f6f8",

                plot_bgcolor="white",

                hovermode="x unified",

                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1
                }
            )

            # =========================================
            # ANALYSIS
            # =========================================

            analysis = html.Div([

                html.H2(
                    "Advanced Rider Analysis"
                ),

                html.Br(),

                html.P([

                    "Primair profiel: ",

                    html.Span(

                        hoofdprofiel,

                        style={
                            "color": "#dc2626",
                            "fontWeight": "bold",
                            "fontSize": "22px"
                        }
                    ),

                    f" ({hoofdscore}%)"
                ]),

                html.P([

                    "Secundair profiel: ",

                    html.Span(

                        second_profile,

                        style={
                            "color": "#2563eb",
                            "fontWeight": "bold",
                            "fontSize": "20px"
                        }
                    ),

                    f" ({second_score}%)"
                ]),

                html.Br(),

                html.H3(
                    "Subtypes"
                ),

                html.P(
                    subtype
                ),

                html.Br(),

                html.H3(
                    "Profile Scores"
                ),

                html.P(
                    f"Climber: {climber_score}%"
                ),

                html.P(
                    f"Sprinter: {sprinter_score}%"
                ),

                html.P(
                    f"Time Trialist: {tt_score}%"
                ),

                html.P(
                    f"Classics Rider: {classics_score}%"
                ),

                html.P(
                    f"Puncheur: {puncheur_score}%"
                ),

                html.P(
                    f"Diesel: {diesel_score}%"
                ),

                html.Br(),

                html.H3(
                    "Decay Archetypes"
                ),

                html.Ul([

                    html.Li(tag)
                    for tag in decay_tags

                ]),

                html.Br(),

                html.H3(
                    "Durability Scores"
                ),

                html.P(
                    f"10s Durability: {round(decay_10s_score,1)}"
                ),

                html.P(
                    f"1min Durability: {round(decay_1m_score,1)}"
                ),

                html.P(
                    f"5min Durability: {round(decay_5m_score,1)}"
                ),

                html.P(
                    f"20min Durability: {round(decay_20m_score,1)}"
                ),

                html.Br(),

                html.H3(
                    "Percentile Scores"
                ),

                html.P(
                    f"FTP/kg: {ftpkg_pct}e percentiel"
                ),

                html.P(
                    f"Sprint: {sprint_pct}e percentiel"
                ),

                html.P(
                    f"1 minuut: {eenmin_pct}e percentiel"
                ),

                html.P(
                    f"5 minuten: {vijfmin_pct}e percentiel"
                ),

                html.P(
                    f"20 minuten: {twintig_pct}e percentiel"
                )

            ])

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
