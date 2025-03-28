import networkx as nx
import pickle
import sys
import os
from collections import deque
import pandas as pd
from typing import Set, Dict

GRAPH_PATH = "/home/colewt/graphsearch/gpu_sssp/aicp.pkl"
SOURCE_NODE = "RZAFRZXBKIOOTF-UHFFFAOYSA-M"  # Example source node
NEIGHBORHOOD_DEPTH = 2  # Depth of neighborhood to extract (adjust as needed)

def get_memory_size(obj, name: str) -> float:
    """Estimate memory size of an object in megabytes."""
    size_bytes = sys.getsizeof(obj)
    if isinstance(obj, (list, dict, set)):
        size_bytes += sum(sys.getsizeof(item) for item in obj)
    elif isinstance(obj, nx.DiGraph):
        size_bytes += sum(sys.getsizeof(n) + sys.getsizeof(d) for n, d in obj.nodes(data=True))
        size_bytes += sum(sys.getsizeof(u) + sys.getsizeof(v) + sys.getsizeof(d) 
                         for u, v, d in obj.edges(data=True))
    elif isinstance(obj, pd.DataFrame):
        size_bytes += obj.memory_usage(deep=True).sum()
    size_mb = size_bytes / (1024 ** 2)
    print(f"Memory usage of {name}: {size_mb:.2f} MB (type: {type(obj).__name__})")
    return size_mb

def load_graph(path: str) -> nx.DiGraph:
    print(f"Loading graph from {path}")
    file_size = os.path.getsize(path) / (1024 ** 3)
    print(f"Pickle file size: {file_size:.2f} GB")
    
    with open(path, "rb") as f:
        G = pickle.load(f)
    
    print(f"✅ Graph loaded. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    get_memory_size(G, "full graph (G)")
    return G

def extract_subgraph_neighborhood(G: nx.DiGraph, source: str, depth: int) -> nx.DiGraph:
    """Extract a subgraph within 'depth' steps from the source node."""
    if source not in G:
        raise ValueError(f"Source node {source} not in graph")
    
    print(f"Extracting subgraph neighborhood around {source} with depth {depth}")
    # BFS to collect nodes within depth
    visited = set([source])
    queue = deque([(source, 0)])
    while queue:
        node, dist = queue.popleft()
        if dist < depth:
            for neighbor in G.neighbors(node):  # Outgoing edges
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
    
    # Create subgraph
    subgraph = G.subgraph(visited).copy()
    print(f"Subgraph extracted. Nodes: {subgraph.number_of_nodes()}, Edges: {subgraph.number_of_edges()}")
    get_memory_size(visited, "visited set")
    get_memory_size(subgraph, "subgraph")
    return subgraph

def bfs_traversal(subgraph: nx.DiGraph, source: str) -> Dict:
    """Perform BFS traversal on the subgraph starting from source."""
    if source not in subgraph:
        raise ValueError(f"Source node {source} not in subgraph")
    
    print(f"Starting BFS traversal from {source} in subgraph")
    visited: Set[str] = set()
    queue = deque([source])
    visited.add(source)
    levels = {source: 0}  # Track level (distance from source)
    
    while queue:
        current = queue.popleft()
        level = levels[current]
        print(f"Visiting node: {current} at level {level}")
        
        # Get neighbors in subgraph
        neighbors = list(subgraph.neighbors(current))
        get_memory_size(neighbors, f"neighbors of {current}")
        
        for neighbor in neighbors:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                levels[neighbor] = level + 1
    
    print(f"BFS completed. Visited {len(visited)} nodes")
    get_memory_size(visited, "visited set")
    get_memory_size(queue, "queue (final)")
    get_memory_size(levels, "levels dict")
    
    return {
        "visited": list(visited),
        "levels": levels,
        "source": source,
        "node_count": len(visited)
    }

def main():
    # Load full graph
    G = load_graph(GRAPH_PATH)
    
    print("\n=== Full Graph Overview ===")
    print(f"Total nodes: {G.number_of_nodes()}")
    print(f"Total edges: {G.number_of_edges()}")
    print(f"Source in graph: {SOURCE_NODE in G}")
    print(f"Out-degree of source: {G.out_degree(SOURCE_NODE)}")
    
    # Extract subgraph
    subgraph = extract_subgraph_neighborhood(G, SOURCE_NODE, NEIGHBORHOOD_DEPTH)
    
    # Perform BFS on subgraph
    bfs_result = bfs_traversal(subgraph, SOURCE_NODE)
    
    print("\n=== BFS Results ===")
    print(f"Source: {bfs_result['source']}")
    print(f"Nodes visited: {bfs_result['node_count']}")
    print("First 10 visited nodes and levels:")
    for node in bfs_result['visited'][:10]:
        print(f"  {node}: Level {bfs_result['levels'][node]}")

if __name__ == "__main__":
    main()