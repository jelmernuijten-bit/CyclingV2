# data_loader.py

import sqlite3
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from utils import find_best_exponent


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

    # --------------------------------------------------
    # Connection
    # --------------------------------------------------

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
    # Metrics
    # --------------------------------------------------

    def get_metrics_dataframe(self):

        query = """

        SELECT
            r.id AS renner_id,
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
                "renner_id",
                "naam",
                "jaar"
            ],

            columns="metric",

            values="waarde",

            aggfunc="first"

        ).reset_index()

        return df

    # --------------------------------------------------
    # Powercurve
    # --------------------------------------------------

    def get_powercurve_dataframe(self):

        query = """

        SELECT
            r.id AS renner_id,
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
    # Comparison dataframe
    # --------------------------------------------------

    def get_comparison_dataframe(self):

        metrics_df = (
            self.get_metrics_dataframe()
        )

        power_df = (
            self.get_powercurve_dataframe()
        )

        if metrics_df.empty:
            return pd.DataFrame()

        rows = []

        for _, rider in metrics_df.iterrows():

            renner_id = rider["renner_id"]
            naam = rider["naam"]
            jaar = rider["jaar"]

            power = power_df[

                (power_df["renner_id"] == renner_id)
                &
                (power_df["jaar"] == jaar)

            ]

            def get_power(
                fatigue,
                duration
            ):

                hit = power[

                    (power["fatigue_kj"] == fatigue)
                    &
                    (power["duration_s"] == duration)

                ]

                if hit.empty:
                    return np.nan

                return float(
                    hit.iloc[0]["power"]
                )

            gewicht = rider.get(
                "Gewicht",
                np.nan
            )

            ftp = rider.get(
                "mFTP",
                np.nan
            )

            vo2 = rider.get(
                "mVO2",
                np.nan
            )

            afstand = rider.get(
                "Afstand",
                np.nan
            )

            duur = rider.get(
                "Duur",
                np.nan
            )

            row = {

                "renner_id":
                    renner_id,

                "naam":
                    naam,

                "jaar":
                    jaar,

                "ftp":
                    ftp,

                "vo2":
                    vo2,

                "gewicht":
                    gewicht,

                "afstand":
                    afstand,

                "duur":
                    duur,

                "power_10s":
                    get_power(0, 10),

                "power_1m":
                    get_power(0, 60),

                "power_5m":
                    get_power(0, 300),

                "power_20m":
                    get_power(0, 1200),

                "fatigue7_10s":
                    get_power(7, 10),

                "fatigue14_10s":
                    get_power(14, 10),

                "fatigue21_10s":
                    get_power(21, 10),

                "fatigue28_10s":
                    get_power(28, 10),

                "fatigue21_1m":
                    get_power(21, 60),

                "fatigue21_5m":
                    get_power(21, 300),

                "fatigue21_20m":
                    get_power(21, 1200)

            }

            rows.append(row)

        df = pd.DataFrame(
            rows
        )

        if df.empty:
            return df

        gewicht = df["gewicht"].replace(
            0,
            np.nan
        )

        df["power_10s_kg"] = (
            df["power_10s"] / gewicht
        )

        df["power_1m_kg"] = (
            df["power_1m"] / gewicht
        )

        df["power_5m_kg"] = (
            df["power_5m"] / gewicht
        )

        df["power_20m_kg"] = (
            df["power_20m"] / gewicht
        )

        df["fatigue21_1m_kg"] = (
            df["fatigue21_1m"] / gewicht
        )

        best_exp = find_best_exponent(
            pd.DataFrame({

                "mVO2":
                    df["vo2"],

                "Gewicht":
                    df["gewicht"]

            })
        )

        df["ftp_adj"] = (
            df["ftp"]
            /
            (
                gewicht ** best_exp
            )
        )

        df["vo2_adj"] = (
            df["vo2"]
            /
            (
                gewicht ** best_exp
            )
        )

        return df

    # --------------------------------------------------
    # Single rider metrics
    # --------------------------------------------------

    def get_metrics(
        self,
        renner_id,
        jaar
    ):

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
                (
                    renner_id,
                    jaar
                )
            ).fetchall()

        return {

            naam: waarde

            for naam, waarde in rows
        }
