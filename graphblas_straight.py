import networkx as nx
import pickle
import random
import time
import os
import sys
import pandas as pd
import graphblas as gb
from graphblas import Vector, Matrix
from typing import Optional, Dict
import psutil
from datetime import datetime

GRAPH_PATH = "/home/colewt/graphsearch/gpu_sssp/aicp.pkl"
SOURCE_NODE = "QTBSBXVTEAMEQO-UHFFFAOYSA-N"
TARGET_NODE = "ASPIRE-9176362867855768187"

memory_log = []

def log_memory(tag=""):
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    print(f"[MEMORY] {tag:<30} RSS: {mem_info.rss / (1024**2):.2f} MB, VMS: {mem_info.vms / (1024**2):.2f} MB")
    memory_log.append((datetime.now().isoformat(), tag, mem_info.rss, mem_info.vms))

def load_graph(path):
    try:
        print(f"Loading graph from {path}")
        file_size = os.path.getsize(path) / (1024 ** 3)
        print(f"Pickle file size: {file_size:.2f} GB")

        with open(path, "rb") as f:
            G = pickle.load(f)

        print(f"✅ Graph loaded. Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        log_memory("After loading graph")
        return G
    except Exception as e:
        print(f"❌ Failed to load graph: {e}")
        sys.exit(1)

def graph_to_dataframe(G: nx.DiGraph):
    try:
        nodes = list(G.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        idx_to_node = {idx: node for node, idx in node_to_idx.items()}
        edges = [(node_to_idx[u], node_to_idx[v]) for u, v in G.edges() if u in node_to_idx and v in node_to_idx]

        edges_df = pd.DataFrame(edges, columns=['source', 'target'])
        print(f"Edges DataFrame created: {edges_df.shape[0]} rows")
        print(edges_df.head())
        log_memory("After creating full edge DataFrame")
        return edges_df, node_to_idx, idx_to_node
    except Exception as e:
        print(f"❌ Failed during DataFrame creation: {e}")
        sys.exit(1)

def find_shortest_path_graphblas(G: nx.DiGraph, source: str, target: str) -> Optional[Dict]:
    try:
        edges_df, node_to_idx, idx_to_node = graph_to_dataframe(G)
        n_nodes = len(G.nodes())
        print(f"Graph has {n_nodes} nodes")

        if source not in node_to_idx or target not in node_to_idx:
            print(f"❌ Source {source} or target {target} not in node index mapping.")
            return None

        start_time = time.time()
        start_node = node_to_idx[source]
        end_node = node_to_idx[target]
        print(f"Start node index: {start_node}, Target node index: {end_node}")

        log_memory("Before matrix creation")
        A = Matrix.from_coo(edges_df['source'], edges_df['target'], [True] * len(edges_df),
                            nrows=n_nodes, ncols=n_nodes, dtype=bool)
        log_memory("After matrix creation")

        frontier = Vector.from_coo([start_node], [True], size=n_nodes, dtype=bool)
        visited = Vector.from_coo([start_node], [True], size=n_nodes, dtype=bool)
        predecessors = Vector(int, n_nodes)
        predecessors[:] = -1

        distance = 0
        found = False

        while frontier.nvals > 0 and not found:
            distance += 1
            try:
                print(f"\n--- Step {distance} ---")
                frontier_indices = list(frontier.to_coo()[0])
                print(f"Frontier size: {len(frontier_indices)} | Sample: {frontier_indices[:5]}")
                print(f"Visited so far: {visited.nvals} nodes")

                result = frontier.vxm(A, gb.semiring.ss.min_secondi)
                print(f"GraphBLAS: VXM result has {result.nvals} non-zero elements")

                next_frontier = Vector(bool, n_nodes)
                next_frontier << result
                mask = ~visited
                next_frontier(mask) << next_frontier

                next_frontier_indices = list(next_frontier.to_coo()[0])
                print(f"Next frontier size: {len(next_frontier_indices)} | Sample: {next_frontier_indices[:5]}")
                print(f"End node in next frontier: {next_frontier[end_node].get(False)}")

                if next_frontier[end_node].get(False):
                    found = True
                    print(f"🎯 Target node found at step {distance}")

                predecessors(next_frontier & (predecessors == -1)) << result
                frontier = next_frontier
                visited |= next_frontier

                log_memory(f"After step {distance}")
            except Exception as step_error:
                print(f"⚠️ Error in step {distance}: {step_error}")
                break

        if not found:
            print("❌ No path found with GraphBLAS")
            return None

        path = []
        current = end_node
        path.append(current)
        seen = {current}
        while current != start_node:
            next_current = predecessors[current].get(-1)
            if next_current == -1 or next_current in seen:
                print("❌ Loop or dead-end in path trace. Breaking.")
                return None
            current = next_current
            path.append(current)
            seen.add(current)

        path.reverse()
        path_str = [idx_to_node[idx] for idx in path]
        path_length = len(path_str) - 1
        elapsed = time.time() - start_time

        print(f"✅ Shortest path found in {elapsed:.4f}s")

        return {
            "path": path_str,
            "length": path_length,
            "nodes": path_str,
            "time": elapsed,
            "source": source,
            "target": target
        }
    except Exception as e:
        print(f"❌ Error during shortest path computation: {e}")
        return None

def export_memory_log(filename="memory_profile.csv"):
    import csv
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "tag", "rss", "vms"])
        writer.writerows(memory_log)

def main():
    G = load_graph(GRAPH_PATH)

    print("\n=== Graph Overview ===")
    print(f"Total nodes: {G.number_of_nodes()}")
    print(f"Total edges: {G.number_of_edges()}")
    print(f"Source in graph: {SOURCE_NODE in G}")
    print(f"Target in graph: {TARGET_NODE in G}")
    print(f"Out-degree of source: {G.out_degree(SOURCE_NODE)}")
    print(f"In-degree of target: {G.in_degree(TARGET_NODE)}")

    source_node = SOURCE_NODE
    print(f"🚀 Starting GraphBLAS shortest path from {source_node} to {TARGET_NODE} on full graph...")
    result = find_shortest_path_graphblas(G, source_node, TARGET_NODE)
    if result:
        print(f"\n✅ Path found (length {result['length']}):")
        print(" -> ".join(result['path']))
        print(f"🧪 Use this source/target for NetworkX comparison:")
        print(f"source_node = \"{result['source']}\"")
        print(f"target_node = \"{result['target']}\"")
    else:
        print("❌ No path found.")

    export_memory_log()

if __name__ == "__main__":
    main()
