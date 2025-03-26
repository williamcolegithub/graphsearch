import mgclient  # Updated import from pymgclient to mgclient
import networkx as nx
import pickle
import subprocess
import time

def parse_config(fname_cfg):
    with open(fname_cfg, 'r') as fp:
        credentials = {}
        for line in fp:
            if not line.startswith('#') and '=' in line:
                k, v = map(str.strip, line.split('=', 1))
                if k == 'INIT_MEMGRAPH_USERNAME':
                    credentials['user'] = v
                elif k == 'INIT_MEMGRAPH_PASSWORD':
                    credentials['pwd'] = v
                elif k == 'memgraph_host':
                    credentials['host'] = v
                elif k == 'MEMGRAPH_BOLT_PORT':
                    credentials['port'] = int(v)
        return credentials

def connect_to_memgraph(credentials):
    return mgclient.connect(
        host=credentials.get('host', 'localhost'),
        port=credentials.get('port', 7687),
        username=credentials.get('user', None),
        password=credentials.get('pwd', None),
        sslmode=False
    )

def create_networkx_graph(connection, batch_size=10000):
    G = nx.DiGraph()
    cursor = connection.cursor()

    # Validate data scope
    cursor.execute("MATCH ()-[r]->() RETURN count(r);")
    total_rels = cursor.fetchone()[0]
    cursor.execute("MATCH (m:Substance)-[r:REACTANT_OF|REAGENT_OF]->(n:Reaction) RETURN count(r);")
    reactant_rels = cursor.fetchone()[0]
    cursor.execute("MATCH (n:Reaction)-[r:PRODUCT_OF]->(m:Substance) RETURN count(r);")
    product_rels = cursor.fetchone()[0]
    print(f"Total relationships: {total_rels}")
    print(f"REACTANT_OF/REAGENT_OF relationships: {reactant_rels}")
    print(f"PRODUCT_OF relationships: {product_rels}")
    print(f"Captured relationships: {reactant_rels + product_rels} ({(reactant_rels + product_rels) / total_rels * 100:.2f}% of total)")

    cursor.execute("MATCH (n) RETURN count(n);")
    total_nodes = cursor.fetchone()[0]
    cursor.execute("MATCH (n:Substance) RETURN count(n);")
    substance_nodes = cursor.fetchone()[0]
    cursor.execute("MATCH (n:Reaction) RETURN count(n);")
    reaction_nodes = cursor.fetchone()[0]
    print(f"Total nodes: {total_nodes}")
    print(f"Substance nodes: {substance_nodes}")
    print(f"Reaction nodes: {reaction_nodes}")
    print(f"Captured nodes (before filtering): {substance_nodes + reaction_nodes} ({(substance_nodes + reaction_nodes) / total_nodes * 100:.2f}% of total)")

    # Process REACTANT_OF/REAGENT_OF edges
    print('Processing reactant_of/reagent_of edges...')
    offset = 0
    while True:
        cursor.execute(f"""
        MATCH (m:Substance)-[r:REACTANT_OF|REAGENT_OF]->(n:Reaction) 
        RETURN m, r, n 
        SKIP {offset} LIMIT {batch_size}
        """)
        records = cursor.fetchall()
        if not records:
            break
        for i, record in enumerate(records, offset + 1):
            if i % 100000 == 0:
                print(f'Nr. of reactant_of/reagent_of edges processed: {i}')
            m, r, n = record[0], record[1], record[2]
            substance_id = m.properties['inchikey']
            rxid = n.properties['rxid']
            G.add_node(substance_id, **m.properties)
            G.add_node(rxid, **n.properties)
            G.add_edge(substance_id, rxid, **r.properties)
        offset += batch_size
    print('... done')

    # Process PRODUCT_OF edges
    print('Processing product_of edges...')
    offset = 0
    while True:
        cursor.execute(f"""
        MATCH (n:Reaction)-[r:PRODUCT_OF]->(m:Substance) 
        RETURN n, r, m 
        SKIP {offset} LIMIT {batch_size}
        """)
        records = cursor.fetchall()
        if not records:
            break
        for i, record in enumerate(records, offset + 1):
            if i % 100000 == 0:
                print(f'Nr. of product_of edges processed: {i}')
            n, r, m = record[0], record[1], record[2]
            rxid = n.properties['rxid']
            substance_id = m.properties['inchikey']
            G.add_node(substance_id, **m.properties)
            G.add_node(rxid, **n.properties)
            G.add_edge(rxid, substance_id, **r.properties)
        offset += batch_size
    print('... done')
    return G

def stop_container():
    subprocess.run(["docker", "stop", "memgraph"], check=True)
    print("Memgraph container stopped to free up RAM.")

def create_nx_graph_save_to_disk(fname_graph, fname_cfg, batch_size=10000):
    credentials = parse_config(fname_cfg)
    connection = connect_to_memgraph(credentials)
    G = create_networkx_graph(connection, batch_size)
    time.sleep(2)
    stop_container()
    with open(fname_graph, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    fname_cfg = '../.env.memgraph'
    fname_graph = 'aicp.pkl'
    create_nx_graph_save_to_disk(fname_graph, fname_cfg)