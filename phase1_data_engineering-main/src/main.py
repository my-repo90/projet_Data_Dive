"""
main.py
Point d'entrée principal de la Phase 1 — Data Engineering.

Lance le pipeline complet :
1. Chargement des données brutes
2. Nettoyage
3. Construction du graphe
4. Calcul des features
5. Export
"""

import os
import sys
import logging
import argparse
import time

# Ajout du dossier src au path
sys.path.insert(0, os.path.dirname(__file__))

from load_data import load_paysim, get_basic_stats
from clean_data import clean_data, save_cleaned
from build_graph import build_nodes, build_edges, build_networkx_graph, save_nodes_edges
from compute_features import compute_all_features, save_features
from export_data import export_all


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )


def run_pipeline(data_path: str = None, filter_types: bool = True, verbose: bool = False):
    """
    Pipeline complet de la Phase 1.

    Args:
        data_path: chemin vers paysim.csv (None = chemin par défaut)
        filter_types: filtrer sur TRANSFER et CASH_OUT uniquement
        verbose: logging détaillé
    """
    setup_logging(verbose)
    logger = logging.getLogger("main")

    start = time.time()
    logger.info("=" * 60)
    logger.info("  PHASE 1 — DATA ENGINEERING  ")
    logger.info("=" * 60)

    # ─── ÉTAPE 1 : Chargement ────────────────────────────────────
    logger.info("\n[1/5] Chargement des données brutes...")
    kwargs = {"path": data_path} if data_path else {}
    df_raw = load_paysim(**kwargs)
    stats = get_basic_stats(df_raw)
    logger.info(f"  {stats['n_rows']:,} transactions chargées")

    # ─── ÉTAPE 2 : Nettoyage ─────────────────────────────────────
    logger.info("\n[2/5] Nettoyage des données...")
    df_clean = clean_data(df_raw, filter_types=filter_types)
    save_cleaned(df_clean)
    logger.info(f"  {len(df_clean):,} transactions après nettoyage")

    # ─── ÉTAPE 3 : Construction du graphe ────────────────────────
    logger.info("\n[3/5] Construction du graphe...")
    edges = build_edges(df_clean)
    nodes = build_nodes(df_clean)
    G = build_networkx_graph(nodes, edges)
    save_nodes_edges(nodes, edges)
    logger.info(f"  Graphe : {G.number_of_nodes():,} nœuds, {G.number_of_edges():,} arêtes")

    # ─── ÉTAPE 4 : Calcul des features ───────────────────────────
    logger.info("\n[4/5] Calcul des features...")
    features = compute_all_features(df_clean, nodes)
    save_features(features)
    logger.info(f"  {features.shape[1]} features calculées pour {features.shape[0]:,} nœuds")

    # ─── ÉTAPE 5 : Export ────────────────────────────────────────
    logger.info("\n[5/5] Export des données...")
    paths = export_all(nodes, edges, features)

    # ─── Résumé final ────────────────────────────────────────────
    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info("  PIPELINE TERMINÉ")
    logger.info("=" * 60)
    logger.info(f"  Durée totale : {elapsed:.1f}s")
    logger.info(f"  Nœuds       : {G.number_of_nodes():,}")
    logger.info(f"  Arêtes      : {G.number_of_edges():,}")
    logger.info(f"  Features    : {features.shape[1]} colonnes")
    logger.info("\n  Fichiers générés :")
    for k, v in paths.items():
        logger.info(f"    {v}")

    return {
        "df_clean": df_clean,
        "nodes": nodes,
        "edges": edges,
        "graph": G,
        "features": features,
        "export_paths": paths,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Phase 1 — Data Engineering Pipeline"
    )
    parser.add_argument(
        "--data", type=str, default=None,
        help="Chemin vers paysim.csv (défaut : data/raw/paysim.csv)"
    )
    parser.add_argument(
        "--no-filter", action="store_true",
        help="Ne pas filtrer les types de transactions"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Logging détaillé"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_pipeline(
        data_path=args.data,
        filter_types=not args.no_filter,
        verbose=args.verbose,
    )
