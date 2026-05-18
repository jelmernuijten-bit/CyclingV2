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

            sprint = round(

                get_col([
                    "okj_10s",
                    "v5"
                ]),

                0
            )

            twintig = round(

                get_col([
                    "okj_20m",
                    "v2"
                ]),

                0
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
            # ANALYSE
            # =========================================

            if ftp_kg > 5.5:

                profiel = "Klimmer"

            elif sprint > 1400:

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

                    FTP/kg bedraagt {ftp_kg}.
                    Sprintvermogen bedraagt {sprint} watt.
                    20 minuten vermogen bedraagt {twintig} watt.
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
