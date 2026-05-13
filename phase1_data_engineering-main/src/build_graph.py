"""
build_graph.py
Construction du graphe de transactions financières.
Nœuds = comptes (sender / receiver)
Arêtes = transactions
"""

import pandas as pd
import numpy as np
import networkx as nx
import os
import logging

logger = logging.getLogger(__name__)

NODES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "nodes.csv")
EDGES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "edges.csv")


def build_edges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit le DataFrame des arêtes depuis les transactions nettoyées.

    Chaque transaction = une arête orientée sender → receiver.
    """
    edges = df[[
        "sender", "receiver", "step", "type", "amount",
        "log_amount", "is_fraud", "balance_diff_orig",
        "balance_diff_dest", "orig_account_emptied"
    ]].copy()

    edges = edges.rename(columns={"sender": "source", "receiver": "target"})
    edges["edge_id"] = edges.index
    logger.info(f"Arêtes construites : {len(edges):,}")
    return edges


def build_nodes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit le DataFrame des nœuds.

    Un nœud = un compte unique (sender ou receiver).
    On identifie si un compte a déjà envoyé/reçu une transaction frauduleuse.
    """
    senders = df[["sender"]].rename(columns={"sender": "node_id"})
    receivers = df[["receiver"]].rename(columns={"receiver": "node_id"})
    all_nodes = pd.concat([senders, receivers]).drop_duplicates().reset_index(drop=True)

    # Comptes impliqués dans fraude (comme émetteur)
    fraud_senders = set(df[df["is_fraud"] == 1]["sender"].unique())
    # Comptes impliqués dans fraude (comme récepteur)
    fraud_receivers = set(df[df["is_fraud"] == 1]["receiver"].unique())

    all_nodes["is_fraud_sender"] = all_nodes["node_id"].isin(fraud_senders).astype(int)
    all_nodes["is_fraud_receiver"] = all_nodes["node_id"].isin(fraud_receivers).astype(int)
    all_nodes["is_fraud_node"] = (
        (all_nodes["is_fraud_sender"] == 1) | (all_nodes["is_fraud_receiver"] == 1)
    ).astype(int)

    # Type de compte (C = client, M = marchand)
    all_nodes["account_type"] = all_nodes["node_id"].apply(
        lambda x: "merchant" if str(x).startswith("M") else "client"
    )

    logger.info(f"Nœuds construits : {len(all_nodes):,}")
    logger.info(f"  → Nœuds frauduleux : {all_nodes['is_fraud_node'].sum():,}")
    return all_nodes


def build_networkx_graph(nodes: pd.DataFrame, edges: pd.DataFrame) -> nx.DiGraph:
    """
    Construit un graphe NetworkX orienté à partir des nœuds et arêtes.
    """
    G = nx.DiGraph()

    # Ajout des nœuds
    for _, row in nodes.iterrows():
        G.add_node(row["node_id"], **row.to_dict())

    # Ajout des arêtes
    for _, row in edges.iterrows():
        G.add_edge(
            row["source"],
            row["target"],
            **row.drop(["source", "target"]).to_dict()
        )

    logger.info(f"Graphe NetworkX : {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes")
    return G


def save_nodes_edges(nodes: pd.DataFrame, edges: pd.DataFrame,
                     nodes_path: str = NODES_PATH,
                     edges_path: str = EDGES_PATH) -> None:
    """Sauvegarde nœuds et arêtes en CSV."""
    os.makedirs(os.path.dirname(nodes_path), exist_ok=True)
    nodes.to_csv(nodes_path, index=False)
    edges.to_csv(edges_path, index=False)
    logger.info(f"Nœuds sauvegardés : {nodes_path}")
    logger.info(f"Arêtes sauvegardées : {edges_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from load_data import load_paysim
    from clean_data import clean_data

    df = clean_data(load_paysim())
    edges = build_edges(df)
    nodes = build_nodes(df)
    G = build_networkx_graph(nodes, edges)
    save_nodes_edges(nodes, edges)

    print(f"\nGraphe : {G.number_of_nodes()} nœuds, {G.number_of_edges()} arêtes")
