from dash import html, dcc, Input, Output
import plotly.express as px

from data_loader import (
    DatabaseService,
    get_database_options
)

from utils import (
    scatter,
    get_current_user,
    load_seg_riders
)

# =========================================
# LAYOUT
# =========================================

def vergelijking_layout():

    return html.Div([

        html.Div(

            [

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
            }
        )

    ])


# =========================================
# CALLBACKS
# =========================================

def register_callbacks(app):

    # -----------------------------------------
    # DATABASES
    # -----------------------------------------

    @app.callback(
        Output("db", "options"),
        Input("db", "id")
    )
    def load_databases(_):

        return get_database_options()

    # -----------------------------------------
    # RIDERS
    # -----------------------------------------

    @app.callback(
        Output("name", "options"),
        Input("db", "value")
    )
    def update_names(db):

        if not db:
            return []

        service = DatabaseService(db)

        df = service.get_comparison_dataframe()

        if df.empty:
            return []

        names = sorted(
            df["naam"]
            .dropna()
            .unique()
        )

        username = get_current_user()

        # =====================================
        # SEG FILTER
        # =====================================

        if username == "SEG":

            allowed_riders = load_seg_riders()

            allowed_clean = [

                r.strip().lower()

                for r in allowed_riders
            ]

            names = [

                n

                for n in names

                if n.strip().lower()
                in allowed_clean

            ]

        return [

            {
                "label": n,
                "value": n
            }

            for n in names

        ]

    # -----------------------------------------
    # GRAPHS
    # -----------------------------------------

    @app.callback(

        Output("p1", "figure"),
        Output("p2", "figure"),
        Output("p3", "figure"),
        Output("p4", "figure"),
        Output("p5", "figure"),
        Output("p6", "figure"),

        Input("db", "value"),
        Input("name", "value")
    )
    def update(db, name):

        if not db:

            empty = px.scatter()

            return (
                empty,
                empty,
                empty,
                empty,
                empty,
                empty
            )

        service = DatabaseService(db)

        df = service.get_comparison_dataframe()

        if df.empty:

            empty = px.scatter()

            return (
                empty,
                empty,
                empty,
                empty,
                empty,
                empty
            )

        return (

            # ---------------------------------
            # 10s vs 20m
            # ---------------------------------

            scatter(
                df,
                "power_10s",
                "power_20m",
                name,
                "10s vs 20min",
                "20min Power",
                "10s Power",
                db_name=db
            ),

            # ---------------------------------
            # 10s vs 20m W/kg
            # ---------------------------------

            scatter(
                df,
                "power_10s_kg",
                "power_20m_kg",
                name,
                "10s vs 20min (W/kg)",
                "20min Power (W/kg)",
                "10s Power (W/kg)",
                db_name=db
            ),

            # ---------------------------------
            # 1m vs Fatigue 21kJ
            # ---------------------------------

            scatter(
                df,
                "power_1m",
                "fatigue21_1m",
                name,
                "1min vs 1min @ 21kJ",
                "1min Power",
                "1min @ 21kJ",
                db_name=db
            ),

            # ---------------------------------
            # 1m vs Fatigue 21kJ W/kg
            # ---------------------------------

            scatter(
                df,
                "power_1m_kg",
                "fatigue21_1m_kg",
                name,
                "1min vs 1min @ 21kJ (W/kg)",
                "1min Power (W/kg)",
                "1min @ 21kJ (W/kg)",
                db_name=db
            ),

            # ---------------------------------
            # FTP vs Training Hours
            # ---------------------------------

            scatter(
                df,
                "duur",
                "ftp_adj",
                name,
                "Adjusted FTP vs Training Hours",
                "Training Hours",
                "Adjusted FTP",
                db_name=db
            ),

            # ---------------------------------
            # VO2 vs Weight
            # ---------------------------------

            scatter(
                df,
                "gewicht",
                "vo2_adj",
                name,
                "Adjusted VO2 vs Weight",
                "Weight",
                "Adjusted VO2",
                db_name=db
            )

        )
