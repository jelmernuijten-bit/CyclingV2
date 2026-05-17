
from dash import html, dcc, Input, Output
import plotly.express as px

from data_loader import load_data, prepare_df
from utils import scatter


def vergelijking_layout():

    return html.Div([

        dcc.Dropdown(
            id="db",
            options=[],
            placeholder="Select database"
        ),

        dcc.Dropdown(
            id="name",
            placeholder="Select renner"
        ),

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


def register_callbacks(app):

    @app.callback(
        Output("db", "options"),
        Input("db", "id")
    )
    def load_databases(_):

        from data_loader import get_database_options

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

        df, best_exp = prepare_df(load_data(db))

        return (

            scatter(
                df,
                "v5",
                "v2",
                name,
                "10s * 20min",
                "20min",
                "10s"
            ),

            scatter(
                df,
                "v5_kg",
                "v2_kg",
                name,
                "10s * 20min (w/kg)",
                "20min (w/kg)",
                "10s (w/kg)"
            ),

            scatter(
                df,
                "v3",
                "v11",
                name,
                "1min * 1min na 21kJ",
                "1min",
                "1min na 21kJ"
            ),

            scatter(
                df,
                "v3_kg",
                "v11_kg",
                name,
                "1min * 1min na 21kJ (w/kg)",
                "1min (w/kg)",
                "1min na 21kJ (w/kg)"
            ),

            scatter(
                df,
                "duur",
                "ftp_adj",
                name,
                f"Adjusted FTP * trainingsuren (exp={best_exp})",
                "Trainingsuren",
                "Adjusted FTP",
                show_zscore=True
            ),

            scatter(
                df,
                "gewicht",
                "vo2_adj",
                name,
                f"Adjusted VO2 * gewicht (exp={best_exp})",
                "Gewicht",
                "Adjusted VO2",
                show_zscore=True
            ),
        )
