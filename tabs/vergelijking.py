from dash import html, dcc, Input, Output
import plotly.express as px

from data_loader import (
    load_data,
    prepare_df,
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

    @app.callback(
        Output("db", "options"),
        Input("db", "id")
    )
    def load_databases(_):

        return get_database_options()

    @app.callback(
        Output("name", "options"),
        Input("db", "value")
    )
    def update_names(db):

        if not db:
            return []

        df = load_data(db)

        names = df.iloc[:, -1].unique()

        username = get_current_user()

        # =========================================
        # SEG FILTER
        # =========================================

        if username == "SEG":

            allowed_riders = load_seg_riders(db)

            allowed_clean = [

                r.strip().lower()

                for r in allowed_riders
            ]

            names = [

                n for n in names

                if n.strip().lower()
                in allowed_clean
            ]

        return [
            {"label": n, "value": n}
            for n in names
        ]

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
            return [px.scatter()] * 6

        df, best_exp = prepare_df(
            load_data(db)
        )

        return (

            scatter(
                df,
                "v5",
                "v2",
                name,
                "10s * 20min",
                "20min",
                "10s",
                db_name=db
            ),

            scatter(
                df,
                "v5_kg",
                "v2_kg",
                name,
                "10s * 20min (w/kg)",
                "20min (w/kg)",
                "10s (w/kg)",
                db_name=db
            ),

            scatter(
                df,
                "v3",
                "v11",
                name,
                "1min * 1min na 21kJ",
                "1min",
                "1min na 21kJ",
                db_name=db
            ),

            scatter(
                df,
                "v3_kg",
                "v11_kg",
                name,
                "1min * 1min na 21kJ (w/kg)",
                "1min (w/kg)",
                "1min na 21kJ (w/kg)",
                db_name=db
            ),

            scatter(
                df,
                "duur",
                "ftp_adj",
                name,
                f"Adjusted FTP * trainingsuren (exp={best_exp})",
                "Trainingsuren",
                "Adjusted FTP",
                db_name=db
            ),

            scatter(
                df,
                "gewicht",
                "vo2_adj",
                name,
                f"Adjusted VO2 * gewicht (exp={best_exp})",
                "Gewicht",
                "Adjusted VO2",
                db_name=db
            )

        )
