# data_loader.py

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import requests


# ==================================================
# DATABASES
# ==================================================

DATABASES = {

    "Junioren":
    "https://drive.google.com/uc?export=download&id=1o79swSIJGhCHR-QRueKfcu7cA5pDKjKA"

}


# ==================================================
# DOWNLOAD DATABASE
# ==================================================

def download_database(db_name):

    if db_name not in DATABASES:

        raise ValueError(
            f"Onbekende database: {db_name}"
        )

    url = DATABASES[db_name]

    response = requests.get(url)

    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(
        suffix=".db",
        delete=False
    )

    tmp.write(response.content)
    tmp.close()

    return tmp.name


# ==================================================
# DATABASE OPTIONS
# ==================================================

def get_database_options():

    return [

        {
            "label": name,
            "value": name
        }

        for name in DATABASES.keys()
    ]


# ==================================================
# DATABASE SERVICE
# ==================================================

class DatabaseService:

    def __init__(self, db_name):

        self.db_name = db_name

        self.db_path = Path(
            download_database(db_name)
        )

    def connect(self):

        return sqlite3.connect(
            self.db_path
        )

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

            return pd.read_sql_query(
                query,
                conn
            )

    # --------------------------------------------------
    # Metrics dataframe
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

    # --------------------------------------------------
    # Powercurve dataframe
    # --------------------------------------------------

    def get_powercurve_dataframe(self):

        query = """

        SELECT
            r.naam,
            p.jaar,
            p.fatigue_kj,
            p.duration_s,
            p.power

        FROM powercurve p

        JOIN renners r
            ON r.id = p.renner_id

        """

        with self.connect() as conn:

            return pd.read_sql_query(
                query,
                conn
            )

    # --------------------------------------------------
    # Legacy dataframe
    # --------------------------------------------------

    def get_legacy_dataframe(self):

        metrics_df = (
            self.get_metrics_dataframe()
        )

        power_df = (
            self.get_powercurve_dataframe()
        )

        if metrics_df.empty:

            return pd.DataFrame()

        if power_df.empty:

            return metrics_df

        duration_map = {

            10: "10s",
            60: "1m",
            300: "5m",
            1200: "20m"
        }

        rows = []

        for (naam, jaar), grp in power_df.groupby(
            ["naam", "jaar"]
        ):

            row = {

                "naam": naam,
                "jaar": jaar

            }

            for _, r in grp.iterrows():

                fatigue = int(
                    r["fatigue_kj"]
                )

                duration = int(
                    r["duration_s"]
                )

                power = r["power"]

                if duration not in duration_map:
                    continue

                suffix = duration_map[
                    duration
                ]

                if fatigue == 0:

                    if suffix == "10s":
                        row["okj_10s"] = power

                    elif suffix == "1m":
                        row["okj_1min"] = power

                    elif suffix == "5m":
                        row["okj_5min"] = power

                    elif suffix == "20m":
                        row["okj_20m"] = power

                else:

                    row[
                        f"kj{fatigue}_{suffix}"
                    ] = power

            rows.append(row)

        power_wide = pd.DataFrame(rows)

        df = metrics_df.merge(

            power_wide,

            on=[
                "naam",
                "jaar"
            ],

            how="left"

        )

        rename_map = {

            "mFTP": "mftp",
            "mVO2": "vo2",
            "Gewicht": "gewicht",
            "Duur": "duur",
            "Afstand": "afstand"
        }

        df = df.rename(
            columns=rename_map
        )

        return df


# ==================================================
# OLD APP COMPATIBILITY
# ==================================================

def load_data(db_name):

    db = DatabaseService(
        db_name
    )

    return db.get_legacy_dataframe()
