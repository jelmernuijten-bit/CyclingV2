from dash import html, dcc, Input, Output
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data, prepare_df

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
# REGISTER CALLBACKS
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

            empty_fig = go.Figure()

            return [], empty_fig, "", ""

        # =========================================
        # LOAD DATA
        # =========================================

        df, best_exp = prepare_df(
            load_data(db)
        )

        rider = df[
            df.iloc[:, -1] == name
        ]

        if rider.empty:

            empty_fig = go.Figure()

            return [], empty_fig, "", ""

        rider = rider.iloc[0]

        # =========================================
        # KPI VALUES
        # =========================================

        ftp = round(rider.get("mftp", 0), 1)

        gewicht = round(
            rider.get("gewicht", 0),
            1
        )

        ftp_kg = round(
            ftp / gewicht,
            2
        ) if gewicht else 0

        vo2 = round(
            rider.get("vo2_adj", 0),
            1
        )

        duur = round(
            rider.get("duur", 0),
            1
        )

        # =========================================
        # KPI CARDS
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
                        value,

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

            rider.get("v5", 0),
            rider.get("v3", 0),
            rider.get("v1", 0),
            rider.get("v2", 0)
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
        # LOAD STATUS
        # =========================================

        kj7 = rider.get("kj7_20m", 0)

        kj28 = rider.get("kj28_20m", 1)

        fatigue = round(
            kj7 / kj28,
            2
        )

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
        # AUTOMATIC ANALYSIS
        # =========================================

        if ftp_kg > 5.5:

            profiel = "Klimmer"

        elif rider.get("v5_kg", 0) > 18:

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
