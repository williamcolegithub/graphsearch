import numpy as np
import pandas as pd
import time
from typing import Dict, Optional
import matplotlib.pyplot as plt
import networkx as nx
import os

try:
    import graphblas as gb
    from graphblas import Vector, Matrix, semiring
    HAS_GRAPHBLAS = True
    print("GraphBLAS available")
    import graphblas
    print(f"GraphBLAS version: {graphblas.__version__}")
except ImportError:
    HAS_GRAPHBLAS = False
    print("GraphBLAS not available")

def generate_reaction_network(n_molecules: int = 10, n_reactions: int = 15, seed: int = 42) -> pd.DataFrame:
    """Generate a directed reaction network with ensured connectivity."""
    np.random.seed(seed)
    sources = np.random.randint(0, n_molecules, size=n_reactions)
    targets = np.random.randint(0, n_molecules, size=n_reactions)
    mask = sources != targets
    edges_df = pd.DataFrame({'source': sources[mask], 'target': targets[mask]})
    chain_sources = list(range(n_molecules - 1))
    chain_targets = list(range(1, n_molecules))
    chain_df = pd.DataFrame({'source': chain_sources, 'target': chain_targets})
    edges_df = pd.concat([edges_df, chain_df]).drop_duplicates(subset=['source', 'target'])
    print(f"GraphBLAS: Generated graph with {len(edges_df)} edges (including chain)")
    return edges_df

def bfs_shortest_path_graphblas(edges_df: pd.DataFrame, start_node: int, end_node: int, 
                              n_molecules: int, visualize: bool = False, save_path: str = None) -> Optional[Dict[str, any]]:
    """Perform BFS using GraphBLAS with optional visualization saved to PNG."""
    if not HAS_GRAPHBLAS:
        print("GraphBLAS is not installed.")
        return None
    
    start_time = time.time()
    
    A = Matrix.from_coo(edges_df['source'], edges_df['target'], [True] * len(edges_df),
                        nrows=n_molecules, ncols=n_molecules, dtype=bool)
    A_indices = Matrix.from_coo(edges_df['source'], edges_df['target'], edges_df['source'],
                                nrows=n_molecules, ncols=n_molecules, dtype=int)
    print(f"GraphBLAS: Matrix has {A.nvals} edges")
    
    frontier = Vector.from_coo([start_node], [True], size=n_molecules, dtype=bool)
    visited = Vector.from_coo([start_node], [True], size=n_molecules, dtype=bool)
    predecessors = Vector(int, n_molecules)
    predecessors[:] = -1
    all_nodes = Vector.from_coo(range(n_molecules), [True] * n_molecules, size=n_molecules, dtype=bool)
    print(f"GraphBLAS: Starting from {start_node}, targeting {end_node}")
    
    distance = 0
    found = False
    
    while frontier.nvals > 0 and not found:
        distance += 1
        temp = frontier.vxm(A, semiring.lor_land)
        next_frontier = Vector(bool, n_molecules)
        mask = Vector(bool, n_molecules)
        mask << all_nodes
        mask(visited) << False
        next_frontier(mask) << temp
        
        frontier_indices = Vector.from_coo(frontier.to_coo()[0], frontier.to_coo()[0], size=n_molecules, dtype=int)
        parents = Vector(int, n_molecules)
        parents(next_frontier) << frontier_indices.vxm(A_indices, semiring.min_first)
        predecessors(next_frontier & (predecessors == -1)) << parents
        
        if next_frontier[end_node].get(False):
            found = True
            print(f"GraphBLAS: Found {end_node} at distance {distance}")
        
        frontier.clear()
        frontier << next_frontier
        visited |= next_frontier
        
        if not frontier.nvals:
            print(f"GraphBLAS: Frontier empty, stopping")
            break
    
    reachable = Vector(bool, n_molecules)
    reachable << visited
    print(f"GraphBLAS: Reachable nodes from {start_node}: {reachable.nvals}")
    if not reachable[end_node].get(False):
        print(f"GraphBLAS: {end_node} not reachable from {start_node}")
    
    path = []
    if found:
        current = end_node
        path.append(current)
        seen = {current}
        while current != start_node and current != -1:
            next_current = predecessors[current].get(-1)
            if next_current in seen or next_current == -1:
                break
            current = next_current
            path.append(current)
            seen.add(current)
        path.reverse()
        print(f"GraphBLAS: Path: {path}")
    else:
        distance = float('inf')
        print("GraphBLAS: No path found")
    
    elapsed = time.time() - start_time
    print(f"GraphBLAS: Took {elapsed:.4f}s")
    
    # Visualization with saving to PNG
    if visualize and found:
        G = nx.DiGraph()
        edges = list(zip(edges_df['source'], edges_df['target']))
        G.add_edges_from(edges)
        
        pos = nx.spring_layout(G)
        plt.figure(figsize=(8, 6))
        
        nx.draw_networkx_nodes(G, pos, node_color='lightgray', node_size=50, alpha=0.7)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, alpha=0.5)
        
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_nodes(G, pos, nodelist=path, node_color='red', node_size=100)
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color='red', width=2, arrows=True)
        
        path_labels = {node: str(node) for node in path}
        nx.draw_networkx_labels(G, pos, labels=path_labels, font_size=10, font_color='black')
        
        plt.title(f"Shortest Path from {start_node} to {end_node} (Distance: {distance})")
        plt.axis('off')
        
        # Save to PNG
        if save_path is None:
            save_path = f"bfs_path_{start_node}_to_{end_node}_{n_molecules}_molecules.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to: {os.path.abspath(save_path)}")
        plt.close()  # Close the figure to free memory
    
    return {'platform': 'GraphBLAS', 'path': path, 'distance': distance, 'time': elapsed, 'edges': edges_df}

def main():
    """Test BFS with scaled graph sizes, visualizing the smallest case."""
    sizes = [
        {"molecules": 200, "reactions": 100},  # Smallest case
        {"molecules": 100, "reactions": 300},
        {"molecules": 500, "reactions": 1500},
        {"molecules": 1000, "reactions": 5000},
        {"molecules": 5000, "reactions": 20000}
    ]
    
    # Find the index of the smallest case
    min_molecules = min(size['molecules'] for size in sizes)
    smallest_idx = next(i for i, size in enumerate(sizes) if size['molecules'] == min_molecules)
    
    for i, size in enumerate(sizes):
        print(f"\nTesting {size['molecules']} molecules, {size['reactions']} reactions")
        edges_df = generate_reaction_network(size['molecules'], size['reactions'])
        if size['molecules'] <= 100:
            start_node = 2
            end_node = 8
        else:
            start_node = np.random.randint(0, size['molecules'] // 4)
            end_node = np.random.randint(3 * size['molecules'] // 4, size['molecules'])
        print(f"Path from {start_node} to {end_node}")
        
        visualize = (i == smallest_idx)
        result = bfs_shortest_path_graphblas(edges_df, start_node, end_node, size['molecules'], visualize=visualize)
        if result:
            print(f"Distance: {result['distance']} hops, Time: {result['time']:.4f}s")

if __name__ == "__main__":
    main()