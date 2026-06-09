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

            metrics_df = pd.read_sql_query(
                """
                SELECT
                    id AS metric_id,
                    naam AS metric
                FROM metrics
                ORDER BY naam
                """,
                conn
            )

            jaren_df = pd.read_sql_query(
                """
                SELECT DISTINCT jaar
                FROM metingen
                WHERE renner_id = ?
                ORDER BY jaar
                """,
                conn,
                params=(renner_id,)
            )

            metingen_df = pd.read_sql_query(
                """
                SELECT
                    metric_id,
                    jaar,
                    waarde
                FROM metingen
                WHERE renner_id = ?
                """,
                conn,
                params=(renner_id,)
            )

        if metrics_df.empty:
            return html.Div(
                "Geen metrics gevonden."
            )

        jaren = jaren_df["jaar"].tolist()

        rows = []

        for _, metric in metrics_df.iterrows():

            row = {
                "metric": metric["metric"],
                "metric_id": metric["metric_id"]
            }

            for jaar in jaren:

                match = metingen_df[
                    (metingen_df["metric_id"] == metric["metric_id"])
                    &
                    (metingen_df["jaar"] == jaar)
                ]

                if not match.empty:
                    row[str(jaar)] = match.iloc[0]["waarde"]
                else:
                    row[str(jaar)] = None

            rows.append(row)

        pivot_df = pd.DataFrame(rows)

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

            metrics_df = pd.read_sql_query(
                """
                SELECT
                    id AS metric_id,
                    naam AS metric
                FROM metrics
                ORDER BY naam
                """,
                conn
            )

            jaren_df = pd.read_sql_query(
                """
                SELECT DISTINCT jaar
                FROM metingen
                WHERE renner_id = ?
                ORDER BY jaar
                """,
                conn,
                params=(renner_id,)
            )

            metingen_df = pd.read_sql_query(
                """
                SELECT
                    metric_id,
                    jaar,
                    waarde
                FROM metingen
                WHERE renner_id = ?
                """,
                conn,
                params=(renner_id,)
            )

        if metrics_df.empty:
            return html.Div(
                "Geen metrics gevonden."
            )

        jaren = jaren_df["jaar"].tolist()

        rows = []

        for _, metric in metrics_df.iterrows():

            row = {
                "metric": metric["metric"],
                "metric_id": metric["metric_id"]
            }

            for jaar in jaren:

                match = metingen_df[
                    (metingen_df["metric_id"] == metric["metric_id"])
                    &
                    (metingen_df["jaar"] == jaar)
                ]

                if not match.empty:
                    row[str(jaar)] = match.iloc[0]["waarde"]
                else:
                    row[str(jaar)] = None

            rows.append(row)

        pivot_df = pd.DataFrame(rows)

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

                if oud:

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

                else:

                    cursor.execute(
                        """
                        INSERT INTO metingen
                        (
                            renner_id,
                            jaar,
                            metric_id,
                            waarde
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            renner_id,
                            jaar,
                            metric_id,
                            value
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


