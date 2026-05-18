from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import plotly.express as px

from data_loader import (
    load_data,
    prepare_df
)

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
        # LOAD STATUS
        # =========================================

        html.Div(
            id="load-status",

            style={
                "marginTop": "20px",
                "marginBottom": "20px"
            }
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
        Output("load-status", "children"),
        Output("analysis-text", "children"),

        Input("db", "value"),
        Input("name", "value")
    )
    def update_rapportage(db, name):

        # =========================================
        # EMPTY STATE
        # =========================================

        if not db or not name:

            return (
                [],
                go.Figure(),
                "",
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

            # fallback = laatste kolom
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
                    "",
                    ""
                )

            rider = rider.iloc[0]

            # =========================================
            # SAFE COLUMN HELPER
            # =========================================

            def get_col(options, default=0):

                for col in options:

                    if col in rider.index:

                        value = rider[col]

                        if value is None:
                            return default

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

                1
            )

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

            vo2 = round(

                get_col([
                    "vo2_adj",
                    "vo2"
                ]),

                1
            )

            duur = round(

                get_col([
                    "duur",
                    "hours"
                ]),

                1
            )

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

                card("FTP/kg", ftp_kg),

                card("VO2", vo2),

                card("Trainingsuren", duur)
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

            values = [

                get_col([
                    "okj_10s",
                    "v5"
                ]),

                get_col([
                    "okj_1m",
                    "v3"
                ]),

                get_col([
                    "okj_5m",
                    "v1"
                ]),

                get_col([
                    "okj_20m",
                    "v2"
                ])
            ]

            fig = go.Figure()

            fig.add_trace(

                go.Scatter(

                    x=labels,
                    y=values,

                    mode="lines+markers",

                    line={
                        "width": 4
                    },

                    marker={
                        "size": 10
                    },

                    name=name
                )
            )

            fig.update_layout(

                title="Power Profile",

                template="plotly_white",

                height=500,

                paper_bgcolor="#f4f6f8",

                plot_bgcolor="white"
            )

            # =========================================
            # TRAININGSSTATUS
            # =========================================

            kj7 = get_col([
                "kj7_20m",
                "kj7"
            ], 0)

            kj28 = get_col([
                "kj28_20m",
                "kj28"
            ], 1)

            fatigue = round(
                kj7 / kj28,
                2
            ) if kj28 else 0

            if fatigue < 0.8:

                status = "Fris"
                color = "green"

            elif fatigue < 1.1:

                status = "Normaal"
                color = "orange"

            else:

                status = "Vermoeid"
                color = "red"

            load_div = html.Div(

                [

                    html.H3(
                        "Trainingsstatus"
                    ),

                    html.Div(

                        f"{status} (ratio: {fatigue})",

                        style={
                            "fontSize": "24px",
                            "fontWeight": "bold",
                            "color": color
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
            # AUTOMATISCHE ANALYSE
            # =========================================

            sprint = get_col([
                "v5_kg",
                "okj_10s_kg"
            ], 0)

            if ftp_kg > 5.5:

                profiel = "Klimmer"

            elif sprint > 18:

                profiel = "Sprinter"

            elif ftp_kg > 4.8:

                profiel = "Allrounder"

            else:

                profiel = "Ontwikkelende renner"

            analysis = html.Div([

                html.H3(
                    "Automatische analyse"
                ),

                html.P(

                    f"""
                    Deze renner heeft een
                    {profiel.lower()} profiel.

                    FTP/kg bedraagt {ftp_kg},
                    met een VO2 score van {vo2}.

                    De huidige trainingsstatus
                    wordt beoordeeld als:
                    {status.lower()}.
                    """
                )
            ])

            return (
                kpis,
                fig,
                load_div,
                analysis
            )

        except Exception as e:

            print("RAPPORTAGE ERROR:")
            print(e)

            return (
                [],
                px.scatter(),
                "",
                str(e)
            )
