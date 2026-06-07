import sqlite3
import pandas as pd
import os
import gdown

from utils import safe_float

base_dir = os.path.dirname(os.path.abspath(__file__))

GOOGLE_DRIVE_FILE = (
    "https://drive.google.com/uc?export=download&id="
    "1o79swSIJGhCHR-QRueKfcu7cA5pDKjKA"
)
DB_FILE = os.path.join(base_dir, "cycling.db")


def ensure_database():

    if not os.path.exists(DB_FILE):

        print("Download database...")

        gdown.download(
            GOOGLE_DRIVE_FILE,
            DB_FILE,
            quiet=False
        )


def load_data():

    ensure_database()

    conn = sqlite3.connect(DB_FILE)

    #
    # Renners
    #
    renners = pd.read_sql_query("""
        SELECT
            id,
            naam,
            geboortejaar,
            geslacht
        FROM renners
    """, conn)

    #
    # Metingen
    #
    metingen = pd.read_sql_query("""
        SELECT
            m.renner_id,
            m.jaar,
            mt.naam AS metric,
            m.waarde
        FROM metingen m
        JOIN metrics mt
            ON mt.id = m.metric_id
    """, conn)

    #
    # Powercurve
    #
    powercurve = pd.read_sql_query("""
        SELECT
            renner_id,
            jaar,
            duration_s,
            power
        FROM powercurve
        WHERE fatigue_kj = 0
    """, conn)

    conn.close()

    #
    # Metrics pivot
    #
    metrics_df = (
        metingen
        .pivot_table(
            index=["renner_id", "jaar"],
            columns="metric",
            values="waarde",
            aggfunc="first"
        )
        .reset_index()
    )

    #
    # Powercurve pivot
    #
    power_df = (
        powercurve
        .pivot_table(
            index=["renner_id", "jaar"],
            columns="duration_s",
            values="power",
            aggfunc="max"
        )
        .reset_index()
    )

    #
    # Mooie kolomnamen
    #
    power_df = power_df.rename(
        columns={
            2: "v2",
            3: "v3",
            5: "v5",
            10: "v10",
            11: "v11",
            30: "v30",
            60: "v60",
            300: "v300",
            1200: "v1200"
        }
    )

    #
    # Alles samenvoegen
    #
    df = (
        metrics_df
        .merge(
            power_df,
            on=["renner_id", "jaar"],
            how="left"
        )
        .merge(
            renners,
            left_on="renner_id",
            right_on="id",
            how="left"
        )
    )

    return df


def prepare_df(df):

    #
    # Leeftijd tijdens meetjaar
    #
    df["leeftijd"] = (
        df["jaar"] - df["geboortejaar"]
    )

    #
    # Gewicht
    #
    if "Gewicht" in df.columns:
        df["gewicht"] = pd.to_numeric(
            df["Gewicht"],
            errors="coerce"
        )

    #
    # FTP
    #
    if "mFTP" in df.columns:
        df["ftp"] = pd.to_numeric(
            df["mFTP"],
            errors="coerce"
        )

    #
    # VO2
    #
    if "mVO2" in df.columns:
        df["vo2"] = pd.to_numeric(
            df["mVO2"],
            errors="coerce"
        )

    #
    # W/kg
    #
    if {"ftp", "gewicht"}.issubset(df.columns):
        df["ftp_kg"] = (
            df["ftp"] / df["gewicht"]
        ).round(2)

    if {"vo2", "gewicht"}.issubset(df.columns):
        df["vo2_kg"] = (
            df["vo2"] / df["gewicht"]
        ).round(2)

    #
    # Powercurve per kg
    #
    for col in [
        "v2",
        "v3",
        "v5",
        "v10",
        "v11",
        "v30",
        "v60",
        "v300",
        "v1200"
    ]:

        if col in df.columns and "gewicht" in df.columns:

            df[f"{col}_kg"] = (
                df[col] / df["gewicht"]
            ).round(2)

    return df
