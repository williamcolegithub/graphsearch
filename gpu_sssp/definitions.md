# Definitions

## Key Terms
- **Adjacency Matrix (\( A \))**: A boolean matrix where \( A[i,j] = 1 \) indicates a directed edge from node \( i \) to node \( j \), and \( A[i,j] = 0 \) otherwise. Represents the graph's connectivity structure.
- **Index Adjacency Matrix (\( A_{\text{indices}} \))**: An integer matrix where \( A_{\text{indices}}[i,j] = i \) if there is an edge from \( i \) to \( j \), and 0 otherwise. Used to track parent nodes during BFS.
- **Frontier Vector (\( F_k \))**: A boolean vector at level \( k \) where \( F_k[i] = 1 \) if node \( i \) is part of the current frontier set to be explored, and 0 otherwise.
- **Visited Vector (\( V \))**: A boolean vector where \( V[i] = 1 \) if node \( i \) has been explored, and 0 otherwise. Tracks processed nodes.
- **Predecessors Vector (\( P \))**: An integer vector where \( P[i] \) stores the parent node of \( i \) in the shortest path tree, initialized as -1 for unvisited nodes.
- **Semiring (\( \text{min_first} \))**: A mathematical structure combining a binary operation (minimum) and a semigroup operation (first), used to select the minimum index of the parent node from the frontier.
- **Semiring (\( \text{lor_land} \))**: A semiring with logical OR for addition and logical AND for multiplication, applied in matrix-vector multiplication to propagate frontier nodes.
- **Source Node (\( s \))**: The starting node from which the shortest path search begins.
- **Target Node (\( t \))**: The destination node for which the shortest path is sought.
- **Distance**: The number of edges (hops) in the shortest path from \( s \) to \( t \), computed as the level at which \( t \) is first reached.
- **Path**: A sequence of nodes \([s, \ldots, t]\) representing the shortest route, reconstructed using the predecessors vector.
- **GraphBLAS**: A library providing linear algebra operations for graph computations, enabling efficient matrix-based BFS implementations.

## Mathematical Context
- **Matrix-Vector Multiplication (\( \times \))**: Operation \( F_{k} = F_{k-1} \times A \) uses a semiring to update the frontier based on adjacency.
- **Masking (\( \land, \lor, \neg \))**: Logical operations to filter unvisited nodes and update visited sets.
- **Assignment (\( \leftarrow \))**: Updates vectors or matrices with computed results, ensuring state progression in BFS.