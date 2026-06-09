from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State
import sqlite3
import pandas as pd

from data_loader import (
    DB_FILE,
    ensure_database
)


def edit_data_layout():

    ensure_database()

    conn = sqlite3.connect(DB_FILE)

    renners = pd.read_sql_query(
        """
        SELECT id, naam
        FROM renners
        ORDER BY naam
        """,
        conn
    )

    jaren = pd.read_sql_query(
        """
        SELECT DISTINCT jaar
        FROM metingen
        ORDER BY jaar DESC
        """,
        conn
    )

    conn.close()

    return html.Div([

        html.H3("Gegevens bewerken"),

        html.Label("Renner"),

        dcc.Dropdown(
            id="edit-runner",
            options=[
                {
                    "label": row["naam"],
                    "value": row["id"]
                }
                for _, row in renners.iterrows()
            ]
        ),

        html.Br(),

        html.Label("Jaar"),

        dcc.Dropdown(
            id="edit-year",
            options=[
                {
                    "label": str(row["jaar"]),
                    "value": row["jaar"]
                }
                for _, row in jaren.iterrows()
            ]
        ),

        html.Br(),

        html.Button(
            "Laden",
            id="load-metrics-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(id="edit-table-container"),

        html.Br(),

        html.Button(
            "Opslaan",
            id="save-metrics-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(id="edit-message")
    ])


def register_edit_callbacks(app):

    @app.callback(
        Output(
            "edit-table-container",
            "children"
        ),
        Input(
            "load-metrics-btn",
            "n_clicks"
        ),
        State(
            "edit-runner",
            "value"
        ),
        State(
            "edit-year",
            "value"
        ),
        prevent_initial_call=True
    )
    def load_metrics(
        n_clicks,
        renner_id,
        jaar
    ):

        if not renner_id or not jaar:
            return html.Div(
                "Selecteer een renner en jaar."
            )

        conn = sqlite3.connect(DB_FILE)

        df = pd.read_sql_query(
            """
            SELECT
                metrics.id AS metric_id,
                metrics.naam AS metric,
                metingen.waarde
            FROM metingen

            JOIN metrics
                ON metrics.id = metingen.metric_id

            WHERE metingen.renner_id = ?
              AND metingen.jaar = ?

            ORDER BY metrics.naam
            """,
            conn,
            params=(
                renner_id,
                jaar
            )
        )

        conn.close()

        return dash_table.DataTable(
            id="edit-table",

            data=df.to_dict(
                "records"
            ),

            columns=[
                {
                    "name": "metric_id",
                    "id": "metric_id",
                    "editable": False
                },
                {
                    "name": "Metric",
                    "id": "metric",
                    "editable": False
                },
                {
                    "name": "Waarde",
                    "id": "waarde",
                    "editable": True,
                    "type": "numeric"
                }
            ],

            hidden_columns=[
                "metric_id"
            ],

            editable=True,

            page_size=50,

            style_table={
                "overflowX": "auto"
            }
        )

    @app.callback(
        Output(
            "edit-message",
            "children"
        ),
        Input(
            "save-metrics-btn",
            "n_clicks"
        ),
        State(
            "edit-runner",
            "value"
        ),
        State(
            "edit-year",
            "value"
        ),
        State(
            "edit-table",
            "data"
        ),
        prevent_initial_call=True
    )
    def save_metrics(
        n_clicks,
        renner_id,
        jaar,
        rows
    ):

        if not rows:
            return "Geen gegevens geladen."

        conn = sqlite3.connect(DB_FILE)

        cursor = conn.cursor()

        wijzigingen = 0

        for row in rows:

            metric_id = row["metric_id"]
            nieuwe_waarde = row["waarde"]

            oud = cursor.execute(
                """
                SELECT waarde
                FROM metingen
                WHERE renner_id = ?
                  AND jaar = ?
                  AND metric_id = ?
                """,
                (
                    renner_id,
                    jaar,
                    metric_id
                )
            ).fetchone()

            oude_waarde = (
                oud[0]
                if oud
                else None
            )

            if oude_waarde == nieuwe_waarde:
                continue

            cursor.execute(
                """
                UPDATE metingen
                SET waarde = ?
                WHERE renner_id = ?
                  AND jaar = ?
                  AND metric_id = ?
                """,
                (
                    nieuwe_waarde,
                    renner_id,
                    jaar,
                    metric_id
                )
            )

            metric_naam = row["metric"]

            cursor.execute(
                """
                INSERT INTO wijzigingslog
                (
                    renner_id,
                    jaar,
                    tabel,
                    sleutel,
                    oude_waarde,
                    nieuwe_waarde
                )
                VALUES
                (?, ?, ?, ?, ?, ?)
                """,
                (
                    renner_id,
                    jaar,
                    "metingen",
                    metric_naam,
                    str(oude_waarde),
                    str(nieuwe_waarde)
                )
            )

            wijzigingen += 1

        conn.commit()
        conn.close()

        return (
            f"{wijzigingen} wijziging(en) opgeslagen."
        )
