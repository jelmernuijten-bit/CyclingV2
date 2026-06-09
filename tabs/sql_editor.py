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

    with sqlite3.connect(DB_FILE) as conn:

        renners = pd.read_sql_query(
            """
            SELECT
                id,
                naam
            FROM renners
            ORDER BY naam
            """,
            conn
        )

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

        html.Button(
            "Laden",
            id="load-metrics-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(
            id="edit-table-container"
        ),

        html.Br(),

        html.Button(
            "Opslaan",
            id="save-metrics-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(
            id="edit-message"
        )
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
        prevent_initial_call=True
    )
    def load_metrics(
        n_clicks,
        renner_id
    ):

        if not renner_id:
            return html.Div(
                "Selecteer een renner."
            )

        with sqlite3.connect(DB_FILE) as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    metrics.id AS metric_id,
                    metrics.naam AS metric,
                    metingen.jaar,
                    metingen.waarde
                FROM metingen

                JOIN metrics
                    ON metrics.id = metingen.metric_id

                WHERE metingen.renner_id = ?

                ORDER BY
                    metrics.naam,
                    metingen.jaar
                """,
                conn,
                params=(renner_id,)
            )

        if df.empty:
            return html.Div(
                "Geen gegevens gevonden."
            )

        metric_lookup = (
            df[
                ["metric_id", "metric"]
            ]
            .drop_duplicates()
        )

        pivot_df = (
            df.pivot(
                index="metric",
                columns="jaar",
                values="waarde"
            )
            .reset_index()
        )

        pivot_df = pivot_df.merge(
            metric_lookup,
            on="metric",
            how="left"
        )

        kolommen = []

        for col in pivot_df.columns:

            kolommen.append({
                "name": str(col),
                "id": str(col),
                "editable": (
                    col not in [
                        "metric",
                        "metric_id"
                    ]
                )
            })

        return dash_table.DataTable(
            id="edit-table",

            data=pivot_df.to_dict(
                "records"
            ),

            columns=kolommen,

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
            "edit-table",
            "data"
        ),
        prevent_initial_call=True
    )
    def save_metrics(
        n_clicks,
        renner_id,
        rows
    ):

        if not rows:
            return (
                "Geen gegevens geladen."
            )

        conn = sqlite3.connect(DB_FILE)

        cursor = conn.cursor()

        wijzigingen = 0

        for row in rows:

            metric_id = row[
                "metric_id"
            ]

            metric_naam = row[
                "metric"
            ]

            for key, value in row.items():

                if key in [
                    "metric",
                    "metric_id"
                ]:
                    continue

                try:
                    jaar = int(key)
                except:
                    continue

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

                if oude_waarde == value:
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
                        value,
                        renner_id,
                        jaar,
                        metric_id
                    )
                )

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
                        str(value)
                    )
                )

                wijzigingen += 1

        conn.commit()
        conn.close()

        return (
            f"{wijzigingen} wijziging(en) opgeslagen."
        )
