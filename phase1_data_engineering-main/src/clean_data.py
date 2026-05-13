"""
clean_data.py
Nettoyage et filtrage des transactions PaySim.
"""

import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

PROCESSED_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "cleaned_transactions.csv"
)

# Types de transactions qui impliquent des transferts entre comptes
TRANSFER_TYPES = ["TRANSFER", "CASH_OUT"]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les lignes dupliquées."""
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    logger.info(f"Doublons supprimés : {before - after}")
    return df


def remove_negative_amounts(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les transactions avec montant négatif ou nul."""
    before = len(df)
    df = df[df["amount"] > 0]
    after = len(df)
    logger.info(f"Transactions montant <= 0 supprimées : {before - after}")
    return df


def filter_transfer_types(df: pd.DataFrame, types: list = None) -> pd.DataFrame:
    """
    Filtre pour ne garder que les types pertinents pour la détection de fraude.
    Par défaut : TRANSFER et CASH_OUT (seuls types avec fraudes dans PaySim).
    """
    if types is None:
        types = TRANSFER_TYPES
    before = len(df)
    df = df[df["type"].isin(types)].copy()
    after = len(df)
    logger.info(f"Filtrage types {types} : {before} → {after} lignes")
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Gère les valeurs manquantes."""
    missing = df.isnull().sum()
    if missing.any():
        logger.warning(f"Valeurs manquantes détectées :\n{missing[missing > 0]}")
        df = df.dropna()
        logger.info("Lignes avec NaN supprimées.")
    else:
        logger.info("Aucune valeur manquante.")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute des colonnes dérivées utiles pour la construction du graphe.
    """
    # Différence de balance côté émetteur
    df = df.copy()
    df["balance_diff_orig"] = df["newbalanceOrig"] - df["oldbalanceOrg"]
    df["balance_diff_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]

    # Flag : balance vidée côté émetteur (souvent associé à fraude)
    df["orig_account_emptied"] = (
        (df["oldbalanceOrg"] > 0) & (df["newbalanceOrig"] == 0)
    ).astype(int)

    # Normalisation du montant (log)
    df["log_amount"] = np.log1p(df["amount"])

    logger.info("Colonnes dérivées ajoutées : balance_diff_orig, balance_diff_dest, orig_account_emptied, log_amount")
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme pour cohérence interne du projet."""
    df = df.rename(columns={
        "nameOrig": "sender",
        "nameDest": "receiver",
        "isFraud": "is_fraud",
        "isFlaggedFraud": "is_flagged_fraud",
    })
    return df


def clean_data(df: pd.DataFrame, filter_types: bool = True) -> pd.DataFrame:
    """
    Pipeline complet de nettoyage.

    Args:
        df: DataFrame brut chargé depuis load_data
        filter_types: si True, filtre sur TRANSFER et CASH_OUT uniquement

    Returns:
        DataFrame nettoyé
    """
    logger.info("=== Début du nettoyage ===")
    df = remove_duplicates(df)
    df = remove_negative_amounts(df)
    df = handle_missing_values(df)
    if filter_types:
        df = filter_transfer_types(df)
    df = rename_columns(df)
    df = add_derived_columns(df)
    df = df.reset_index(drop=True)
    logger.info(f"=== Nettoyage terminé : {len(df):,} transactions ===")
    return df


def save_cleaned(df: pd.DataFrame, path: str = PROCESSED_PATH) -> None:
    """Sauvegarde le DataFrame nettoyé en CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Données nettoyées sauvegardées : {path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from load_data import load_paysim
    df_raw = load_paysim()
    df_clean = clean_data(df_raw)
    save_cleaned(df_clean)
    print(df_clean.head())
    print(df_clean.dtypes)
