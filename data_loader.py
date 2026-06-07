# data_loader.py

import sqlite3
from pathlib import Path

import pandas as pd


class DatabaseService:

    def __init__(self, db_path):
        self.db_path = Path(db_path)

    def connect(self):
        return sqlite3.connect(self.db_path)

    # --------------------------------------------------
    # Renners
    # --------------------------------------------------

    def get_renners(self):

        query = """
        SELECT
            id,
            naam,
            geboortejaar,
            geslacht
        FROM renners
        ORDER BY naam
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn)

    def get_renner_id(self, naam):

        query = """
        SELECT id
        FROM renners
        WHERE naam = ?
        """

        with self.connect() as conn:

            row = conn.execute(
                query,
                (naam,)
            ).fetchone()

        return row[0] if row else None

    # --------------------------------------------------
    # Jaren
    # --------------------------------------------------

    def get_jaren(self, renner_id):

        query = """
        SELECT DISTINCT jaar
        FROM metingen
        WHERE renner_id = ?
        ORDER BY jaar
        """

        with self.connect() as conn:

            rows = conn.execute(
                query,
                (renner_id,)
            ).fetchall()

        return [r[0] for r in rows]

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------

    def get_metrics(self, renner_id, jaar):

        query = """
        SELECT
            mt.naam,
            me.waarde
        FROM metingen me
        JOIN metrics mt
            ON mt.id = me.metric_id
        WHERE me.renner_id = ?
        AND me.jaar = ?
        """

        with self.connect() as conn:

            rows = conn.execute(
                query,
                (renner_id, jaar)
            ).fetchall()

        return {
            naam: waarde
            for naam, waarde in rows
        }

    def get_metric(self,
                   renner_id,
                   jaar,
                   metric_name):

        metrics = self.get_metrics(
            renner_id,
            jaar
        )

        return metrics.get(metric_name)

    # --------------------------------------------------
    # Historie
    # --------------------------------------------------

    def get_metric_history(
        self,
        renner_id,
        metric_name
    ):

        query = """
        SELECT
            me.jaar,
            me.waarde
        FROM metingen me
        JOIN metrics mt
            ON mt.id = me.metric_id
        WHERE me.renner_id = ?
        AND mt.naam = ?
        ORDER BY me.jaar
        """

        with self.connect() as conn:

            return pd.read_sql_query(
                query,
                conn,
                params=(
                    renner_id,
                    metric_name
                )
            )

    # --------------------------------------------------
    # Powercurve
    # --------------------------------------------------

    def get_powercurve(
        self,
        renner_id,
        jaar
    ):

        query = """
        SELECT
            fatigue_kj,
            duration_s,
            power
        FROM powercurve
        WHERE renner_id = ?
        AND jaar = ?
        """

        with self.connect() as conn:

            return pd.read_sql_query(
                query,
                conn,
                params=(
                    renner_id,
                    jaar
                )
            )

    def get_power(
        self,
        renner_id,
        jaar,
        fatigue_kj,
        duration_s
    ):

        query = """
        SELECT power
        FROM powercurve
        WHERE renner_id = ?
        AND jaar = ?
        AND fatigue_kj = ?
        AND duration_s = ?
        """

        with self.connect() as conn:

            row = conn.execute(
                query,
                (
                    renner_id,
                    jaar,
                    fatigue_kj,
                    duration_s
                )
            ).fetchone()

        return row[0] if row else None

    # --------------------------------------------------
    # Dashboard dataframe
    # --------------------------------------------------

    def get_metrics_dataframe(self):

        query = """
        SELECT
            r.naam,
            me.jaar,
            mt.naam AS metric,
            me.waarde
        FROM metingen me
        JOIN renners r
            ON r.id = me.renner_id
        JOIN metrics mt
            ON mt.id = me.metric_id
        """

        with self.connect() as conn:

            df = pd.read_sql_query(
                query,
                conn
            )

        if df.empty:
            return pd.DataFrame()

        df = df.pivot_table(
            index=[
                "naam",
                "jaar"
            ],
            columns="metric",
            values="waarde",
            aggfunc="first"
        ).reset_index()

        return df


# ------------------------------------------------------
# Backwards compatible helper
# ------------------------------------------------------

def load_database(db_path):

    return DatabaseService(db_path)
