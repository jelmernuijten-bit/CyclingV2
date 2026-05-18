from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px

from data_loader import load_data

# =========================================
# LAYOUT
# =========================================

def rapportage_layout():

    return html.Div([

        # =========================================
        # KPI CARDS
        # =========================================

        html.Div(
            id="rapport-kpis",

            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(4, 1fr)",
                "gap": "15px",
                "marginBottom": "20px"
            }
        ),

        # =========================================
        # POWER PROFILE
        # =========================================

        dcc.Graph(
            id="power-profile"
        ),

        # =========================================
        # ANALYSIS
        # =========================================

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

            ftp = round(

                get_col([
                    "mftp",
                    "ftp",
                    "ftp_adj"
                ]),

                0
            )

            ftp = int(ftp)

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
            # FATIGUE DATA
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
            # HOOFDPROFIEL
            # =========================================

            if (

                ftp_kg >= 5.8
                and vijf_min >= 500
                and gewicht <= 70

            ):

                hoofdprofiel = "Climber"

            elif (

                sprint >= 1600
                and ftp_kg < 4.8

            ):

                hoofdprofiel = "Sprinter"

            elif (

                ftp >= 390
                and fatigue_5m <= 6

            ):

                hoofdprofiel = "Time Trialist"

            elif (

                sprint >= 1400
                and ftp_kg >= 4.8

            ):

                hoofdprofiel = "Classics Rider"

            elif (

                vijf_min >= 520
                and een_min >= 700

            ):

                hoofdprofiel = "Puncheur"

            elif (

                ftp >= 360
                and fatigue_5m <= 8

            ):

                hoofdprofiel = "Diesel"

            else:

                hoofdprofiel = "Developing Rider"

            # =========================================
            # SUBTYPES
            # =========================================

            subtypes = []

            # Fatigue Resistant

            if fatigue_5m <= 5:

                subtypes.append(
                    "Fatigue Resistant"
                )

            # Anaerobic

            if (

                sprint >= 1500
                and een_min >= 750

            ):

                subtypes.append(
                    "Anaerobic"
                )

            # Endurance

            if kj28_20m >= 360:

                subtypes.append(
                    "Endurance"
                )

            # Explosive

            if (

                sprint >= 1450
                and vijf_min >= 500

            ):

                subtypes.append(
                    "Explosive"
                )

            # Lightweight

            if gewicht <= 68:

                subtypes.append(
                    "Lightweight"
                )

            # Durable

            if sprint_decay <= 7:

                subtypes.append(
                    "Durable"
                )

            # =========================================
            # SUBTYPE STRING
            # =========================================

            if len(subtypes) > 0:

                subtype = " / ".join(subtypes)

            else:

                subtype = "Balanced"

            # =========================================
            # FINALE PROFIEL
            # =========================================

            profiel = f"{subtype} {hoofdprofiel}"

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
            # POWER PROFILE
            # =========================================

            labels = [
                "10s",
                "1m",
                "5m",
                "20m"
            ]

            fig = go.Figure()

            # =========================================
            # LIJNEN DEFINIEREN
            # =========================================

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

            # =========================================
            # LIJNEN TOEVOEGEN
            # =========================================

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
                            "width": 1.5,
                            "color": lijn["kleur"]
                        },

                        marker={
                            "size": 5
                        },

                        name=lijn["naam"]
                    )
                )

            fig.update_layout(

                title="Power Profile",

                template="plotly_white",

                height=500,

                paper_bgcolor="#f4f6f8",

                plot_bgcolor="white",

                hovermode="x unified",

                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1
                },

                margin={
                    "l": 40,
                    "r": 40,
                    "t": 80,
                    "b": 40
                }
            )

            # =========================================
            # ANALYSE
            # =========================================

            analysis = html.Div([

                html.H3(
                    "Automatische analyse"
                ),

                html.P(

                    f"""
                    Deze renner heeft een
                    {profiel} profiel.

                    FTP/kg bedraagt {ftp_kg:.2f}.
                    Sprintvermogen bedraagt {sprint} watt.
                    20 minuten vermogen bedraagt {twintig} watt.

                    Vermogensverlies op 5 minuten na 28kj bedraagt
                    {fatigue_5m}%.
                    """
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
