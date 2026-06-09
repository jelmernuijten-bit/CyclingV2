from dash import html, dcc, dash_table
from dash.dependencies import Input, Output, State
import sqlite3
import pandas as pd

from data_loader import (
    DB_FILE,
    ensure_database
)


# =====================================================
# HELPERS
# =====================================================

def format_duration(seconds):

    try:
        seconds = int(seconds)
    except:
        return str(seconds)

    if seconds < 60:
        return f"{seconds}s"

    if seconds % 60 == 0:
        return f"{seconds // 60}m"

    mins = seconds // 60
    secs = seconds % 60

    return f"{mins}m{secs}s"


# =====================================================
# LAYOUT
# =====================================================

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
            "Metrics laden",
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
            "Metrics opslaan",
            id="save-metrics-btn",
            n_clicks=0
        ),

        html.Div(
            id="edit-message"
        ),

        html.Hr(),

        # ======================================
        # POWERCURVE
        # ======================================

        html.H3("Powercurve"),

        html.Label("Jaar"),

        dcc.Dropdown(
            id="powercurve-year"
        ),

        html.Br(),

        html.Button(
            "Powercurve laden",
            id="load-powercurve-btn",
            n_clicks=0
        ),

        html.Br(),
        html.Br(),

        html.Div(
            id="powercurve-table-container"
        ),

        html.Br(),

        html.Button(
            "Powercurve opslaan",
            id="save-powercurve-btn",
            n_clicks=0
        ),

        html.Div(
            id="powercurve-message"
        )
    ])


# =====================================================
# CALLBACKS
# =====================================================

def register_edit_callbacks(app):

    # ======================================
    # POWERCURVE JAREN
    # ======================================

    @app.callback(
        Output(
            "powercurve-year",
            "options"
        ),
        Input(
            "edit-runner",
            "value"
        )
    )
    def load_powercurve_years(
        renner_id
    ):

        if not renner_id:
            return []

        with sqlite3.connect(DB_FILE) as conn:

            jaren = pd.read_sql_query(
                """
                SELECT DISTINCT jaar
                FROM powercurve
                WHERE renner_id = ?
                ORDER BY jaar DESC
                """,
                conn,
                params=(renner_id,)
            )

        return [
            {
                "label": str(row["jaar"]),
                "value": row["jaar"]
            }
            for _, row in jaren.iterrows()
        ]

    # ======================================
    # METRICS LADEN
    # ======================================

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
            # ======================================
    # METRICS OPSLAAN
    # ======================================

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

            metric_id = row["metric_id"]
            metric_naam = row["metric"]

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

    # ======================================
    # POWERCURVE LADEN
    # ======================================

    @app.callback(
        Output(
            "powercurve-table-container",
            "children"
        ),
        Input(
            "load-powercurve-btn",
            "n_clicks"
        ),
        State(
            "edit-runner",
            "value"
        ),
        State(
            "powercurve-year",
            "value"
        ),
        prevent_initial_call=True
    )
    def load_powercurve(
        n_clicks,
        renner_id,
        jaar
    ):

        if not renner_id:
            return html.Div(
                "Selecteer een renner."
            )

        if not jaar:
            return html.Div(
                "Selecteer een jaar."
            )

        with sqlite3.connect(DB_FILE) as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    fatigue_kj,
                    duration_s,
                    power
                FROM powercurve
                WHERE renner_id = ?
                  AND jaar = ?
                ORDER BY
                    fatigue_kj,
                    duration_s
                """,
                conn,
                params=(
                    renner_id,
                    jaar
                )
            )

        if df.empty:

            return html.Div(
                "Geen powercurve gevonden."
            )

        pivot_df = (
            df.pivot(
                index="fatigue_kj",
                columns="duration_s",
                values="power"
            )
            .reset_index()
        )

        originele_kolommen = list(
            pivot_df.columns
        )

        rename_map = {}

        for col in originele_kolommen:

            if col == "fatigue_kj":
                continue

            rename_map[col] = (
                format_duration(col)
            )

        pivot_df = pivot_df.rename(
            columns=rename_map
        )

        columns = []

        columns.append({
            "name": "Fatigue (kJ)",
            "id": "fatigue_kj",
            "editable": False
        })

        for originele in originele_kolommen:

            if originele == "fatigue_kj":
                continue

            columns.append({
                "name": format_duration(
                    originele
                ),
                "id": format_duration(
                    originele
                ),
                "editable": True
            })

        return dash_table.DataTable(
            id="powercurve-table",

            data=pivot_df.to_dict(
                "records"
            ),

            columns=columns,

            editable=True,

            page_size=100,

            style_table={
                "overflowX": "auto"
            }
        )

    # ======================================
    # POWERCURVE OPSLAAN
    # ======================================

    @app.callback(
        Output(
            "powercurve-message",
            "children"
        ),
        Input(
            "save-powercurve-btn",
            "n_clicks"
        ),
        State(
            "edit-runner",
            "value"
        ),
        State(
            "powercurve-year",
            "value"
        ),
        State(
            "powercurve-table",
            "data"
        ),
        prevent_initial_call=True
    )
    def save_powercurve(
        n_clicks,
        renner_id,
        jaar,
        rows
    ):

        if not rows:
            return (
                "Geen powercurve geladen."
            )

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        wijzigingen = 0

        duration_lookup = {}

        cursor.execute(
            """
            SELECT DISTINCT duration_s
            FROM powercurve
            WHERE renner_id = ?
              AND jaar = ?
            ORDER BY duration_s
            """,
            (
                renner_id,
                jaar
            )
        )

        for row in cursor.fetchall():

            duration = row[0]

            duration_lookup[
                format_duration(duration)
            ] = duration

        for row in rows:

            fatigue_kj = row[
                "fatigue_kj"
            ]

            for key, value in row.items():

                if key == "fatigue_kj":
                    continue

                if key not in duration_lookup:
                    continue

                duration_s = (
                    duration_lookup[key]
                )

                oud = cursor.execute(
                    """
                    SELECT power
                    FROM powercurve
                    WHERE renner_id = ?
                      AND jaar = ?
                      AND fatigue_kj = ?
                      AND duration_s = ?
                    """,
                    (
                        renner_id,
                        jaar,
                        fatigue_kj,
                        duration_s
                    )
                ).fetchone()

                oude_power = (
                    oud[0]
                    if oud
                    else None
                )

                if oude_power == value:
                    continue

                cursor.execute(
                    """
                    UPDATE powercurve
                    SET power = ?
                    WHERE renner_id = ?
                      AND jaar = ?
                      AND fatigue_kj = ?
                      AND duration_s = ?
                    """,
                    (
                        value,
                        renner_id,
                        jaar,
                        fatigue_kj,
                        duration_s
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
                        "powercurve",
                        f"{fatigue_kj}kj_{duration_s}s",
                        str(oude_power),
                        str(value)
                    )
                )

                wijzigingen += 1

        conn.commit()
        conn.close()

        return (
            f"{wijzigingen} powercurve wijziging(en) opgeslagen."
        )
