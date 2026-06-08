from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State

import sqlite3
import pandas as pd

from data_loader import (
    DB_FILE,
    ensure_database
)


def sql_editor_layout():

    return html.Div([

        html.H3("SQL Editor"),

        dcc.Textarea(
            id="sql-query",
            value="""
SELECT name
FROM sqlite_master
WHERE type='table';
""",
            style={
                "width": "100%",
                "height": "250px",
                "fontFamily": "monospace"
            }
        ),

        html.Br(),

        html.Button(
            "Uitvoeren",
            id="run-query-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(
            id="sql-message",
            style={
                "marginBottom": "10px"
            }
        ),

        html.Div(id="sql-result")
    ])


def register_sql_callbacks(app):

    @app.callback(
        [
            Output("sql-result", "children"),
            Output("sql-message", "children")
        ],
        Input("run-query-btn", "n_clicks"),
        State("sql-query", "value"),
        prevent_initial_call=True
    )
    def run_query(n_clicks, query):

        if not query:
            return (
                None,
                "Geen query ingevoerd."
            )

        q = query.strip().lower()

        # Alleen veilige read-only queries
        if not (
            q.startswith("select")
            or q.startswith("with")
            or q.startswith("pragma")
        ):
            return (
                None,
                "Alleen SELECT, WITH en PRAGMA queries zijn toegestaan."
            )

        try:

            ensure_database()

            conn = sqlite3.connect(DB_FILE)

            df = pd.read_sql_query(
                query,
                conn
            )

            conn.close()

            table = dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[
                    {
                        "name": col,
                        "id": col
                    }
                    for col in df.columns
                ],
                page_size=25,
                sort_action="native",
                filter_action="native",
                style_table={
                    "overflowX": "auto"
                }
            )

            return (
                table,
                f"{len(df)} rijen gevonden."
            )

        except Exception as e:

            return (
                None,
                str(e)
            )
