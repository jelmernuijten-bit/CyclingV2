from dash import html, dcc, Input, Output
import plotly.express as px

from data_loader import (
    load_data,
    prepare_df
)

from utils import scatter


# =========================================
# LAYOUT
# =========================================

def vergelijking_layout():

    return html.Div([

        html.Div([

            dcc.Graph(id="p1"),
            dcc.Graph(id="p2"),
            dcc.Graph(id="p3"),
            dcc.Graph(id="p4"),
            dcc.Graph(id="p5"),
            dcc.Graph(id="p6"),

        ],

        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "10px"
        })

    ])


# =========================================
# CALLBACKS
# =========================================

def register_callbacks(app):

    # =========================================
    # INITIALISE FILTERS
    # =========================================

    @app.callback(
        Output("name", "options"),
        Output("geslacht", "options"),
        Output("leeftijd", "min"),
        Output("leeftijd", "max"),
        Output("leeftijd", "value"),
        Input("name", "id")
    )
    def initialize(_):

        result = prepare_df(load_data())

        if isinstance(result, tuple):
            df, _ = result
        else:
            df = result

        names = sorted(
            df["naam"]
            .dropna()
            .unique()
        )

        genders = sorted(
            df["geslacht"]
            .dropna()
            .unique()
        )

        min_age = int(df["leeftijd"].min())
        max_age = int(df["leeftijd"].max())

        return (

            [
                {
                    "label": n,
                    "value": n
                }
                for n in names
            ],

            [
                {
                    "label": g,
                    "value": g
                }
                for g in genders
            ],

            min_age,
            max_age,
            [min_age, max_age]
        )

    # =========================================
    # UPDATE FIGURES
    # =========================================

    @app.callback(
        Output("p1", "figure"),
        Output("p2", "figure"),
        Output("p3", "figure"),
        Output("p4", "figure"),
        Output("p5", "figure"),
        Output("p6", "figure"),

        Input("name", "value"),
        Input("geslacht", "value"),
        Input("leeftijd", "value")
    )
    def update(name, geslacht, leeftijd):

        result = prepare_df(load_data())

        if isinstance(result, tuple):
            df, best_exp = result
        else:
            df = result
            best_exp = 0.67

        # =========================================
        # FILTER GESLACHT
        # =========================================

        if geslacht:

            df = df[
                df["geslacht"].isin(geslacht)
            ]

        # =========================================
        # FILTER LEEFTIJD
        # =========================================

        if leeftijd:

            df = df[
                (df["leeftijd"] >= leeftijd[0])
                &
                (df["leeftijd"] <= leeftijd[1])
            ]

        # =========================================
        # FIGURES
        # =========================================

        try:

            fig1 = scatter(
                df,
                "v300",
                "v10",
                name,
                "10s * 20min",
                "20min",
                "10s"
            )

        except:

            fig1 = px.scatter()

        try:

            fig2 = scatter(
                df,
                "v300_kg",
                "v10_kg",
                name,
                "10s * 20min (w/kg)",
                "20min (w/kg)",
                "10s (w/kg)"
            )

        except:

            fig2 = px.scatter()

        try:

            fig3 = scatter(
                df,
                "v1200",
                "v60",
                name,
                "1min * 1min na 21kJ",
                "1min",
                "1min na 21kJ"
            )

        except:

            fig3 = px.scatter()

        try:

            fig4 = scatter(
                df,
                "v1200_kg",
                "v60_kg",
                name,
                "1min * 1min na 21kJ (w/kg)",
                "1min (w/kg)",
                "1min na 21kJ (w/kg)"
            )

        except:

            fig4 = px.scatter()

        try:

            fig5 = scatter(
                df,
                "duur",
                "ftp_kg",
                name,
                "FTP/kg vs trainingsuren",
                "Trainingsuren",
                "FTP/kg"
            )

        except:

            fig5 = px.scatter()

        try:

            fig6 = scatter(
                df,
                "gewicht",
                "vo2_kg",
                name,
                "VO2/kg vs gewicht",
                "Gewicht",
                "VO2/kg"
            )

        except:

            fig6 = px.scatter()

        return (
            fig1,
            fig2,
            fig3,
            fig4,
            fig5,
            fig6
        )
