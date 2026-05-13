"""
load_data.py — Phase 2
Chargement depuis la racine du projet ou Phase 1 (auto-détection).
"""

import pandas as pd
import os, logging

logger   = logging.getLogger(__name__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")

PHASE1_DIRS = [
    os.path.join(PROJECT_ROOT, "phase1_data_engineering-main", "data", "processed"),
    os.path.join(PROJECT_ROOT, "phase1_data_engineering", "data", "processed"),
]


def _resolve(filename, label):
    candidates = [
        os.path.join(PROJECT_ROOT, filename),
        os.path.join(INPUT_DIR, filename),
        *[os.path.join(phase1_dir, filename) for phase1_dir in PHASE1_DIRS],
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"[{label}] source : {candidate}")
            return candidate

    raise FileNotFoundError(
        f"[{label}] introuvable.\n"
        + "\n".join(f"  → {candidate}" for candidate in candidates)
        + "\nPlacez le fichier à la racine du projet ou lancez d'abord la Phase 1."
    )


def load_features(path=None):
    if path is None:
        path = _resolve("nodes_features.parquet", "nodes_features")
    df = pd.read_parquet(path)
    logger.info(f"Features : {df.shape[0]:,} nœuds × {df.shape[1]} colonnes")
    return df


def load_edges(path=None):
    if path is None:
        path = _resolve("edges.csv", "edges")
    df = pd.read_csv(path)
    logger.info(f"Arêtes : {len(df):,}")
    return df


def get_feature_columns(df):
    exclude = {
        "node_id", "account_type",
        "is_fraud_sender", "is_fraud_receiver", "is_fraud_node"
    }
    return [c for c in df.select_dtypes(include=["number"]).columns
            if c not in exclude]
