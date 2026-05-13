"""
export_data.py
Export des données vers des formats compatibles avec la phase 2 (backend + Unity).
"""

import pandas as pd
import numpy as np
import json
import os
import logging

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "export")


def _convert_numpy(obj):
    """Convertit les types numpy en types Python natifs pour JSON."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    raise TypeError(f"Type non sérialisable : {type(obj)}")


def export_nodes_json(nodes: pd.DataFrame,
                      path: str = None) -> str:
    """
    Exporte les nœuds en JSON.
    Format : liste d'objets avec toutes les propriétés.
    """
    if path is None:
        path = os.path.join(EXPORT_DIR, "nodes.json")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    records = nodes.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_convert_numpy, indent=2, ensure_ascii=False)

    logger.info(f"Nœuds exportés en JSON : {path} ({len(records):,} nœuds)")
    return path


def export_edges_json(edges: pd.DataFrame,
                      path: str = None) -> str:
    """
    Exporte les arêtes en JSON.
    Format : liste d'objets {source, target, weight, ...}
    """
    if path is None:
        path = os.path.join(EXPORT_DIR, "edges.json")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Sélection des colonnes pertinentes pour l'export
    export_cols = ["source", "target", "amount", "log_amount",
                   "is_fraud", "step", "type", "edge_id"]
    cols_available = [c for c in export_cols if c in edges.columns]
    records = edges[cols_available].to_dict(orient="records")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, default=_convert_numpy, indent=2, ensure_ascii=False)

    logger.info(f"Arêtes exportées en JSON : {path} ({len(records):,} arêtes)")
    return path


def export_summary(nodes: pd.DataFrame,
                   edges: pd.DataFrame,
                   features: pd.DataFrame,
                   path: str = None) -> str:
    """Exporte un fichier de résumé du pipeline."""
    if path is None:
        path = os.path.join(EXPORT_DIR, "summary.json")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    summary = {
        "pipeline": "phase1_data_engineering",
        "n_nodes": int(len(nodes)),
        "n_edges": int(len(edges)),
        "n_features_per_node": int(len(features.columns)),
        "fraud_nodes": int(nodes["is_fraud_node"].sum()) if "is_fraud_node" in nodes.columns else None,
        "fraud_edges": int(edges["is_fraud"].sum()) if "is_fraud" in edges.columns else None,
        "account_types": nodes["account_type"].value_counts().to_dict() if "account_type" in nodes.columns else {},
        "feature_columns": list(features.columns),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, default=_convert_numpy, indent=2, ensure_ascii=False)

    logger.info(f"Résumé exporté : {path}")
    return path


def export_all(nodes: pd.DataFrame,
               edges: pd.DataFrame,
               features: pd.DataFrame) -> dict:
    """
    Lance tous les exports.

    Returns:
        dict avec les chemins de tous les fichiers exportés
    """
    logger.info("=== Export des données ===")
    paths = {
        "nodes_json": export_nodes_json(nodes),
        "edges_json": export_edges_json(edges),
        "summary_json": export_summary(nodes, edges, features),
    }
    logger.info("=== Export terminé ===")
    return paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from load_data import load_paysim
    from clean_data import clean_data, save_cleaned
    from build_graph import build_nodes, build_edges, save_nodes_edges
    from compute_features import compute_all_features, save_features

    df = clean_data(load_paysim())
    edges = build_edges(df)
    nodes = build_nodes(df)
    features = compute_all_features(df, nodes)

    paths = export_all(nodes, edges, features)
    print("\nFichiers exportés :")
    for k, v in paths.items():
        print(f"  {k}: {v}")
