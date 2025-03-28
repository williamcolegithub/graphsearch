import numpy as np
import pandas as pd
import time
from typing import Dict, Optional
import pickle
import networkx as nx
import os
import psutil

try:
    import graphsearch.graphblas_straight as gb
    from graphsearch.graphblas_straight import Vector, Matrix
    HAS_GRAPHBLAS = True
    print("GraphBLAS available")
    import graphsearch.graphblas_straight as graphblas_straight
    print(f"GraphBLAS version: {graphblas_straight.__version__}")
except ImportError:
    HAS_GRAPHBLAS = False
    print("GraphBLAS not available")

def load_graph(file_path: str, source: str, target: str, cutoff: int = 5) -> tuple[nx.DiGraph, Dict, pd.DataFrame]:
    """Load the graph and extract a subgraph around source and target."""
    print(f"Memory available: {psutil.virtual_memory().available / (1024**3):.2f} GB")
    try:
        with open(file_path, 'rb') as f:
            G_full = pickle.load(f)
        print(f"Full graph loaded. Nodes: {G_full.number_of_nodes()}, Edges: {G_full.number_of_edges()}")

        # Extract subgraph around source and target with cutoff distance
        source_nodes = set(nx.single_source_shortest_path(G_full, source, cutoff=cutoff).keys())
        target_nodes = set(nx.single_source_shortest_path(G_full.reverse(), target, cutoff=cutoff).keys())
        subgraph_nodes = source_nodes.union(target_nodes)
        G = G_full.subgraph(subgraph_nodes).copy()
        print(f"Subgraph created. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        print(f"Memory after subgraph: {psutil.virtual_memory().available / (1024**3):.2f} GB")

        node_list = list(G.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(node_list)}
        edges = [(node_to_idx[u], node_to_idx[v]) for u, v in G.edges()]
        edges_df = pd.DataFrame(edges, columns=['source', 'target'])
        print(f"Edges DataFrame created. Memory: {psutil.virtual_memory().available / (1024**3):.2f} GB")

        return G, node_to_idx, edges_df
    except Exception as e:
        raise Exception(f"Error loading graph: {str(e)}")

def bfs_shortest_path_graphblas(
    edges_df: pd.DataFrame, 
    G: nx.DiGraph, 
    node_to_idx: Dict, 
    source: str, 
    target: str, 
    n_nodes: int
) -> Optional[Dict]:
    """Perform BFS using GraphBLAS on the subgraph."""
    if not HAS_GRAPHBLAS:
        print("GraphBLAS is not installed.")
        return None

    if source not in node_to_idx or target not in node_to_idx:
        print(f"Source {source} or target {target} not in subgraph")
        return None

    start_time = time.time()
    source_idx = node_to_idx[source]
    target_idx = node_to_idx[target]
    print(f"Starting BFS. Source idx: {source_idx}, Target idx: {target_idx}")

    A = Matrix.from_coo(edges_df['source'], edges_df['target'], [True] * len(edges_df),
                        nrows=n_nodes, ncols=n_nodes, dtype=bool)
    print(f"GraphBLAS: Matrix has {A.nvals} edges, size: {A.nrows}x{A.ncols}")
    print(f"Memory after matrix: {psutil.virtual_memory().available / (1024**3):.2f} GB")

    frontier = Vector.from_coo([source_idx], [True], size=n_nodes, dtype=bool)
    visited = Vector.from_coo([source_idx], [True], size=n_nodes, dtype=bool)
    predecessors = Vector(int, n_nodes)
    predecessors[:] = -1
    all_nodes = Vector.from_coo(list(range(n_nodes)), [True] * n_nodes, size=n_nodes, dtype=bool)
    print(f"GraphBLAS: Vectors initialized")

    distance = 0
    found = False

    while frontier.nvals > 0 and not found:
        distance += 1
        result = frontier.vxm(A, gb.semiring.ss.min_secondi)
        next_frontier = Vector(bool, n_nodes)
        next_frontier << result
        mask = Vector(bool, n_nodes)
        mask << all_nodes
        mask(visited, gb.binary.second[bool]) << False
        next_frontier(mask) << next_frontier

        predecessors(next_frontier & (predecessors == -1)) << result

        if next_frontier[target_idx].get(False):
            found = True
            print(f"GraphBLAS: Found {target} at distance {distance}")

        frontier.clear()
        frontier << next_frontier
        visited |= next_frontier
        if not frontier.nvals:
            print(f"GraphBLAS: Frontier empty, stopping")
            break

    if not found:
        print(f"GraphBLAS: {target} not reachable from {source} within subgraph")
        return None

    idx_to_node = {idx: node for node, idx in node_to_idx.items()}
    path = []
    current_idx = target_idx
    path.append(idx_to_node[current_idx])
    seen = {current_idx}
    while current_idx != source_idx and current_idx != -1:
        next_current = predecessors[current_idx].get(-1)
        if next_current in seen or next_current == -1:
            break
        current_idx = next_current
        path.append(idx_to_node[current_idx])
        seen.add(current_idx)
    path.reverse()
    print(f"GraphBLAS: Path: {path}")

    elapsed = time.time() - start_time
    print(f"GraphBLAS: Took {elapsed:.4f}s")

    path_details = []
    for node in path:
        props = G.nodes[node]
        node_type = 'Substance' if 'inchikey' in props else 'Reaction'
        path_details.append({'id': node, 'type': node_type, 'properties': props})

    edge_details = []
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        edge_details.append({'from': path[i], 'to': path[i + 1], 'relationship': edge_data})

    return {
        'platform': 'GraphBLAS',
        'path': path,
        'length': distance,
        'nodes': path_details,
        'edges': edge_details,
        'time': elapsed
    }

def print_path_details(path_info: Dict):
    """Pretty print the path information."""
    if not path_info:
        return
    print(f"\nShortest path found (length: {path_info['length']}):")
    print("Path:", " -> ".join(path_info['path']))
    print("\nDetailed path:")
    for i, node in enumerate(path_info['nodes']):
        print(f"Step {i}:")
        print(f"  Type: {node['type']}")
        print(f"  ID: {node['id']}")
        print(f"  Properties: {node['properties']}")
        if i < len(path_info['edges']):
            edge = path_info['edges'][i]
            print(f"  Relationship to next: {edge['relationship']}")
        print()

if __name__ == "__main__":
    graph_path = "/home/colewt/graphsearch/gpu_sssp/aicp.pkl"
    source_node = "QTBSBXVTEAMEQO-UHFFFAOYSA-N"
    target_node = "ASPIRE-9176362867855768187"

    G, node_to_idx, edges_df = load_graph(graph_path, source_node, target_node, cutoff=5)
    print(f"\nFinding shortest path from {source_node} to {target_node}...")
    path_info = bfs_shortest_path_graphblas(edges_df, G, node_to_idx, source_node, target_node, G.number_of_nodes())
    print_path_details(path_info)