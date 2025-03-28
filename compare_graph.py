import numpy as np
import pandas as pd
import pickle
import networkx as nx
import os
import psutil
from typing import Dict, Optional

try:
    import graphsearch.graphblas_straight as gb
    from graphsearch.graphblas_straight import Vector, Matrix
    HAS_GRAPHBLAS = True
    print("GraphBLAS available")
except ImportError:
    HAS_GRAPHBLAS = False
    print("GraphBLAS not available")

def print_graph_statistics(G: nx.DiGraph, label: str = "Graph"):
    print(f"\n=== {label} Statistics ===")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Directed: {G.is_directed()}")
    print(f"Average degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    print(f"Density: {nx.density(G):.6f}")
    node_types = {}
    for node, data in G.nodes(data=True):
        node_type = 'Substance' if 'inchikey' in data else 'Reaction'
        node_types[node_type] = node_types.get(node_type, 0) + 1
    print("Node types:")
    for type_name, count in node_types.items():
        print(f"  {type_name}: {count}")
    print(f"Is strongly connected: {nx.is_strongly_connected(G)}")
    print(f"Number of strongly connected components: {len(list(nx.strongly_connected_components(G)))}")

def load_and_analyze_aicp(file_path: str) -> nx.DiGraph:
    print(f"Memory available: {psutil.virtual_memory().available / (1024**3):.2f} GB")
    try:
        with open(file_path, 'rb') as f:
            G = pickle.load(f)
        print(f"AICP graph loaded successfully")
        print_graph_statistics(G, "AICP Graph")
        print(f"Memory after loading: {psutil.virtual_memory().available / (1024**3):.2f} GB")
        return G
    except Exception as e:
        raise Exception(f"Error loading AICPs graph: {str(e)}")

def generate_synthetic_graph(n_molecules: int = 2528685, n_reactions: int = 5785149, seed: int = 42) -> nx.DiGraph:
    np.random.seed(seed)
    G = nx.DiGraph()
    molecules = [f"MOL_{i}" for i in range(n_molecules)]
    for mol in molecules:
        G.add_node(mol, inchikey=f"INCHI_{mol}", type="Substance")
    for i in range(n_reactions):
        reaction_id = f"RXN_{i}"
        n_reactants = np.random.randint(1, 4)
        n_products = np.random.randint(1, 4)
        reactants = np.random.choice(molecules, n_reactants, replace=False)
        products = np.random.choice(molecules, n_products, replace=False)
        G.add_node(reaction_id, type="Reaction")
        for reactant in reactants:
            G.add_edge(reactant, reaction_id, relationship="reactant")
        for product in products:
            G.add_edge(reaction_id, product, relationship="product")
    print_graph_statistics(G, "Synthetic Graph")
    return G

def main():
    aicp_path = "/home/colewt/graphsearch/gpu_sssp/aicp.pkl"
    print("\nAnalyzing AICPs graph...")
    aicp_graph = load_and_analyze_aicp(aicp_path)
    print("\nGenerating synthetic graph...")
    synthetic_graph = generate_synthetic_graph()
    print("\n=== Comparison Summary ===")
    print(f"AICP - Nodes: {aicp_graph.number_of_nodes()}, Edges: {aicp_graph.number_of_edges()}")
    print(f"Synthetic - Nodes: {synthetic_graph.number_of_nodes()}, Edges: {synthetic_graph.number_of_edges()}")

if __name__ == "__main__":
    main()