import time
import networkx as nx
import pickle
from typing import Optional, Dict

def load_graph(file_path: str) -> nx.DiGraph:
    with open(file_path, 'rb') as f:
        G = pickle.load(f)
    print(f"Graph loaded successfully. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    return G

def find_shortest_path(G: nx.DiGraph, source: str, target: str) -> Optional[Dict]:
    try:
        if source not in G or target not in G:
            raise ValueError("Source or target node not in graph")

        start_time = time.time()
        path = nx.shortest_path(G, source=source, target=target)
        elapsed = time.time() - start_time
        print(f"✅ Shortest path found in {elapsed:.4f}s")

        path_length = len(path) - 1
        path_details = []
        for node in path:
            props = G.nodes[node]
            node_type = 'Substance' if 'inchikey' in props else 'Reaction'
            path_details.append({
                'id': node,
                'type': node_type,
                'properties': props
            })

        edge_details = []
        for i in range(len(path) - 1):
            edge_data = G.get_edge_data(path[i], path[i + 1])
            edge_details.append({
                'from': path[i],
                'to': path[i + 1],
                'relationship': edge_data
            })

        return {
            'path': path,
            'length': path_length,
            'nodes': path_details,
            'edges': edge_details,
            'time': elapsed
        }

    except nx.NetworkXNoPath:
        print(f"No path exists between {source} and {target}")
        return None
    except Exception as e:
        print(f"Error finding shortest path: {str(e)}")
        return None

def print_path_details(path_info: Dict):
    if not path_info:
        print("No path info.")
        return

    print(f"\nShortest path found (length: {path_info['length']})")
    print("Path:", " -> ".join(path_info['path']))
    print(f"Time taken: {path_info['time']:.4f}s\n")
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
    source_node = "RZAFRZXBKIOOTF-UHFFFAOYSA-M"
    target_node = "MGEPMOSEZPNDPD-UHFFFAOYSA-N"

    G = load_graph(graph_path)
    print(f"\nFinding shortest path from {source_node} to {target_node}...")
    path_info = find_shortest_path(G, source_node, target_node)
    print_path_details(path_info)
