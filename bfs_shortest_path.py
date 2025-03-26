import networkx as nx
import pickle
from typing import Optional, Dict

def load_graph(file_path: str) -> nx.DiGraph:
    """
    Load the pickled NetworkX directed graph from disk.
    """
    try:
        with open(file_path, 'rb') as f:
            G = pickle.load(f)
        print(f"Graph loaded successfully. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        return G
    except Exception as e:
        raise Exception(f"Error loading graph: {str(e)}")

def find_shortest_path(
    G: nx.DiGraph, 
    source: str, 
    target: str
) -> Optional[Dict]:
    """
    Find the shortest path between source and target nodes using BFS (default for unweighted graph).
    """
    try:
        if source not in G:
            raise ValueError(f"Source node {source} not found in graph")
        if target not in G:
            raise ValueError(f"Target node {target} not found in graph")

        # Use shortest_path without method parameter (defaults to BFS for unweighted DiGraph)
        path = nx.shortest_path(G, source=source, target=target)
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

        result = {
            'path': path,
            'length': path_length,
            'nodes': path_details,
            'edges': edge_details
        }
        return result
    
    except nx.NetworkXNoPath:
        print(f"No path exists between {source} and {target}")
        return None
    except Exception as e:
        print(f"Error finding shortest path: {str(e)}")
        return None

def print_path_details(path_info: Dict):
    """
    Pretty print the path information.
    """
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
    # Path to your pickled graph
    graph_path = "/Users/colewt/Documents/aspire-aicp-services/graphsearch/aicp.pkl"
    
    # Load the graph
    G = load_graph(graph_path)
    
    # Example source-target pairs
    # Option 1: Substance to Reaction
    source_node = "QTBSBXVTEAMEQO-UHFFFAOYSA-N"
    target_node = "ASPIRE-9176362867855768187"
    
    # Option 2: Substance to Substance (uncomment to use)
    # source_node = "QTBSBXVTEAMEQO-UHFFFAOYSA-N"
    # target_node = "XLYOFNOQVPJJNP-UHFFFAOYSA-N"
    
    # Option 3: Reaction to Reaction (uncomment to use)
    # source_node = "ASPIRE-9176362867855768187"
    # target_node = "ASPIRE-9178525407692597133"
    
    # Find shortest path
    print(f"\nFinding shortest path from {source_node} to {target_node}...")
    path_info = find_shortest_path(G, source_node, target_node)
    
    # Print results
    print_path_details(path_info)