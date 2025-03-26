import networkx as nx
import pickle
from typing import Dict

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

def explore_graph(G: nx.DiGraph, sample_size: int = 5):
    """
    Explore the graph and print sample nodes with their IDs and properties.
    
    Args:
        G: NetworkX directed graph
        sample_size: Number of nodes of each type to display
    """
    # Separate substances and reactions
    substance_nodes = []
    reaction_nodes = []
    
    # Iterate over all nodes
    for node, data in G.nodes(data=True):
        if 'inchikey' in data:
            substance_nodes.append((node, data))
        elif 'rxid' in data:
            reaction_nodes.append((node, data))
    
    print(f"\nTotal Substance nodes: {len(substance_nodes)}")
    print(f"Total Reaction nodes: {len(reaction_nodes)}")
    
    # Print sample Substance nodes
    print("\nSample Substance Nodes (identified by inchikey):")
    for i, (node, props) in enumerate(substance_nodes[:sample_size], 1):
        print(f"{i}. ID: {node}")
        print(f"   Properties: {props}")
        print()
    
    # Print sample Reaction nodes
    print("Sample Reaction Nodes (identified by rxid):")
    for i, (node, props) in enumerate(reaction_nodes[:sample_size], 1):
        print(f"{i}. ID: {node}")
        print(f"   Properties: {props}")
        print()
    
    # Suggest some example pairs
    if substance_nodes and reaction_nodes:
        print("Example source-target pairs to try:")
        print(f"1. Substance to Reaction: {substance_nodes[0][0]} -> {reaction_nodes[0][0]}")
        if len(substance_nodes) > 1:
            print(f"2. Substance to Substance: {substance_nodes[0][0]} -> {substance_nodes[1][0]}")
        if len(reaction_nodes) > 1:
            print(f"3. Reaction to Reaction: {reaction_nodes[0][0]} -> {reaction_nodes[1][0]}")

if __name__ == "__main__":
    # Path to your pickled graph
    graph_path = "/Users/colewt/Documents/aspire-aicp-services/scripts/aicp.pkl"
    
    # Load the graph
    G = load_graph(graph_path)
    
    # Explore the graph and print sample nodes
    explore_graph(G, sample_size=5)