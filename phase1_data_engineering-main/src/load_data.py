"""
load_data.py
Chargement des données brutes PaySim depuis data/raw/paysim.csv
"""

import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "paysim.csv")

EXPECTED_COLUMNS = [
    "step", "type", "amount", "nameOrig", "oldbalanceOrg",
    "newbalanceOrig", "nameDest", "oldbalanceDest", "newbalanceDest", "isFraud"
]


def load_paysim(path: str = RAW_PATH) -> pd.DataFrame:
    """
    Charge le fichier CSV PaySim et retourne un DataFrame brut.

    Args:
        path: chemin vers le fichier CSV

    Returns:
        DataFrame brut avec toutes les colonnes originales
    """
    logger.info(f"Chargement des données depuis : {path}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fichier introuvable : {path}\n"
            "Placez paysim.csv dans data/raw/"
        )

    df = pd.read_csv(path)

    # Vérification des colonnes attendues
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

    logger.info(f"Données chargées : {len(df):,} lignes, {len(df.columns)} colonnes")
    logger.info(f"Types de transactions : {df['type'].value_counts().to_dict()}")
    logger.info(f"Fraudes : {df['isFraud'].sum():,} ({df['isFraud'].mean()*100:.2f}%)")

    return df


def get_basic_stats(df: pd.DataFrame) -> dict:
    """Retourne un résumé statistique rapide du dataset."""
    return {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "transaction_types": df["type"].value_counts().to_dict(),
        "fraud_count": int(df["isFraud"].sum()),
        "fraud_rate": float(df["isFraud"].mean()),
        "amount_mean": float(df["amount"].mean()),
        "amount_max": float(df["amount"].max()),
        "n_steps": int(df["step"].nunique()),
        "unique_orig": int(df["nameOrig"].nunique()),
        "unique_dest": int(df["nameDest"].nunique()),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = load_paysim()
    stats = get_basic_stats(df)
    print("\n=== Statistiques de base ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
