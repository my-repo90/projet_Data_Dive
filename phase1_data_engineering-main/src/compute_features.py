"""
compute_features.py
Calcul des features par nœud pour la phase 2 (IA / clustering / anomalies).

Features calculées :
- Features de volume : nombre de tx envoyées/reçues, montant total
- Features de réseau : degré entrant, degré sortant
- Features temporelles : step min/max/range
- Features de risque : taux de fraude des voisins
"""

import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

FEATURES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed", "nodes_features.parquet"
)


def compute_sender_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features pour chaque compte en tant qu'émetteur."""
    grp = df.groupby("sender")

    feats = pd.DataFrame({
        "tx_sent_count": grp["amount"].count(),
        "tx_sent_total_amount": grp["amount"].sum(),
        "tx_sent_mean_amount": grp["amount"].mean(),
        "tx_sent_max_amount": grp["amount"].max(),
        "tx_sent_std_amount": grp["amount"].std().fillna(0),
        "tx_sent_fraud_count": grp["is_fraud"].sum(),
        "tx_sent_fraud_rate": grp["is_fraud"].mean(),
        "tx_sent_step_min": grp["step"].min(),
        "tx_sent_step_max": grp["step"].max(),
        "tx_sent_step_range": grp["step"].max() - grp["step"].min(),
        "tx_sent_unique_receivers": grp["receiver"].nunique(),
        "orig_emptied_count": grp["orig_account_emptied"].sum(),
    }).reset_index().rename(columns={"sender": "node_id"})

    return feats


def compute_receiver_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features pour chaque compte en tant que récepteur."""
    grp = df.groupby("receiver")

    feats = pd.DataFrame({
        "tx_recv_count": grp["amount"].count(),
        "tx_recv_total_amount": grp["amount"].sum(),
        "tx_recv_mean_amount": grp["amount"].mean(),
        "tx_recv_max_amount": grp["amount"].max(),
        "tx_recv_std_amount": grp["amount"].std().fillna(0),
        "tx_recv_fraud_count": grp["is_fraud"].sum(),
        "tx_recv_fraud_rate": grp["is_fraud"].mean(),
        "tx_recv_unique_senders": grp["sender"].nunique(),
    }).reset_index().rename(columns={"receiver": "node_id"})

    return feats


def compute_balance_features(df: pd.DataFrame) -> pd.DataFrame:
    """Features de balance côté émetteur."""
    grp = df.groupby("sender")
    feats = pd.DataFrame({
        "balance_diff_mean": grp["balance_diff_orig"].mean(),
        "balance_diff_min": grp["balance_diff_orig"].min(),
        "old_balance_mean": grp["oldbalanceOrg"].mean(),
    }).reset_index().rename(columns={"sender": "node_id"})
    return feats


def merge_features(nodes: pd.DataFrame,
                   sender_feats: pd.DataFrame,
                   receiver_feats: pd.DataFrame,
                   balance_feats: pd.DataFrame) -> pd.DataFrame:
    """Fusionne toutes les features avec la table des nœuds."""
    df = nodes.copy()
    df = df.merge(sender_feats, on="node_id", how="left")
    df = df.merge(receiver_feats, on="node_id", how="left")
    df = df.merge(balance_feats, on="node_id", how="left")

    # Remplir les NaN (nœuds qui n'ont fait qu'envoyer ou que recevoir)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Feature composite : ratio envoi/réception
    df["tx_sent_recv_ratio"] = df["tx_sent_count"] / (df["tx_recv_count"] + 1)

    # Feature : total activité
    df["total_tx_count"] = df["tx_sent_count"] + df["tx_recv_count"]
    df["total_amount"] = df["tx_sent_total_amount"] + df["tx_recv_total_amount"]

    logger.info(f"Features finales : {df.shape[0]} nœuds, {df.shape[1]} colonnes")
    return df


def save_features(df: pd.DataFrame, path: str = FEATURES_PATH) -> None:
    """Sauvegarde les features en Parquet (format optimal pour la phase 2)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info(f"Features sauvegardées : {path}")


def compute_all_features(df_clean: pd.DataFrame, nodes: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline complet de calcul des features.

    Args:
        df_clean: DataFrame nettoyé (depuis clean_data)
        nodes: DataFrame des nœuds (depuis build_graph)

    Returns:
        DataFrame des features par nœud
    """
    logger.info("=== Calcul des features ===")
    sender_feats = compute_sender_features(df_clean)
    receiver_feats = compute_receiver_features(df_clean)
    balance_feats = compute_balance_features(df_clean)
    features = merge_features(nodes, sender_feats, receiver_feats, balance_feats)
    logger.info("=== Features calculées ===")
    return features


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from load_data import load_paysim
    from clean_data import clean_data
    from build_graph import build_nodes

    df = clean_data(load_paysim())
    nodes = build_nodes(df)
    features = compute_all_features(df, nodes)
    save_features(features)
    print(features.head())
    print(f"\nShape : {features.shape}")
    print(f"\nColonnes : {list(features.columns)}")
