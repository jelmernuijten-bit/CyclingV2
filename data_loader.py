
import sqlite3
import pandas as pd
import numpy as np
import os
import glob
import gdown
import json

from utils import (
    safe_float,
    parse_duur,
    find_best_exponent
)

base_dir = os.path.dirname(os.path.abspath(__file__))

GOOGLE_DRIVE_FOLDER = "https://drive.google.com/drive/folders/1nX5wfBjcekwJpZ_uB05t0TByLhbtb2Br"

local_db_folder = os.path.join(base_dir, "drive_databases")
cache_file = os.path.join(base_dir, "db_cache.json")

os.makedirs(local_db_folder, exist_ok=True)


def load_cache():

    if os.path.exists(cache_file):

        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except:
            return {}

    return {}


def save_cache(cache):

    with open(cache_file, "w") as f:
        json.dump(cache, f)


def sync_databases_if_needed():

    cache = load_cache()

    print("Controle Google Drive databases...")

    try:

        gdown.download_folder(
            GOOGLE_DRIVE_FOLDER,
            output=local_db_folder,
            quiet=True,
            use_cookies=False,
            remaining_ok=True
        )

        save_cache(cache)

    except Exception as e:

        print(f"Google Drive sync fout: {e}")


sync_databases_if_needed()


def get_database_options():

    return [
        {"label": f, "value": f}
        for root, dirs, files in os.walk(local_db_folder)
        for f in files
        if f.endswith(".db")
    ]


def load_data(db_name):

    db_path = None

    for root, dirs, files in os.walk(local_db_folder):

        if db_name in files:

            db_path = os.path.join(root, db_name)
            break

    if db_path is None:
        raise FileNotFoundError(f"Database niet gevonden: {db_name}")

    conn = sqlite3.connect(db_path)

    df = pd.read_sql_query("""
        SELECT m.*, r.naam
        FROM metingen m
        JOIN renners r ON m.renner_id = r.id
    """, conn)

    conn.close()

    return df


def prepare_df(df):

    df["naam"] = df.iloc[:, -1]
    df["gewicht"] = df.iloc[:, -2].apply(safe_float)

    df["v2"] = df.iloc[:, 2].apply(safe_float)
    df["v3"] = df.iloc[:, 3].apply(safe_float)
    df["v5"] = df.iloc[:, 5].apply(safe_float)
    df["v11"] = df.iloc[:, 11].apply(safe_float)
    df["ftp"] = df.iloc[:, 22].apply(safe_float)
    df["vo2"] = df.iloc[:, 23].apply(safe_float)

    df["duur"] = df.iloc[:, 25].apply(parse_duur)

    df = df.sort_values("duur")

    df["v2_kg"] = (df["v2"] / df["gewicht"]).round(1)
    df["v5_kg"] = (df["v5"] / df["gewicht"]).round(1)
    df["v3_kg"] = (df["v3"] / df["gewicht"]).round(1)
    df["v11_kg"] = (df["v11"] / df["gewicht"]).round(1)

    df["ftp_kg"] = (df["ftp"] / df["gewicht"]).round(2)

    best_exp = find_best_exponent(df)

    df["ftp_adj"] = (
        df["ftp"] / (df["gewicht"] ** best_exp)
    ).round(2)

    df["vo2_adj"] = (
        df["vo2"] / (df["gewicht"] ** best_exp)
    ).round(2)

    return df, best_exp
