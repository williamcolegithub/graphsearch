# BFS with GraphBLAS - My Development Notes


## Implementation Details
- **Graph Generation**: Designed a function to construct directed graphs, utilizing a configurable number of molecules (nodes) and reactions (edges), with a chain ensured for connectivity. The approach leverages pandas for edge management and allows size adjustments.
- **BFS Algorithm**: Implemented using GraphBLAS for optimized sparse matrix operations, tracking predecessors to reconstruct paths and compute hop distances. The solution supports scalability testing.
- **Visualization**: Integrated a PNG export for the smallest test case using networkx and matplotlib, disabled for larger graphs to maintain performance.
- **Scalability**: Validated across sizes from 10 to 5000 molecules, demonstrating consistent performance.

## Design Considerations
- **GraphBLAS Selection**: Chosen for its efficient sparse matrix handling, suitable for large-scale graph computations.
- **Matrix Configuration**: Transitioned from a boolean adjacency matrix to an integer matrix (`A_indices`) storing source indices to enable accurate predecessor tracking.
- **Semiring Optimization**: Replaced `min_plus` with `min_first` to correctly select parent nodes based on frontier indices.
- **Visualization Strategy**: Limited plotting to the smallest case to avoid performance degradation in larger graphs.

## Technical Challenges and Resolutions
- **Incomplete Path Reconstruction**: Initially, the algorithm correctly computed distances (e.g., 3 hops from node 2 to 8), but reconstructed paths were limited to the target node (e.g., `[8]` instead of `[2, 3, 4, 8]`). Investigated by logging predecessor vectors, revealing that the boolean adjacency matrix lacked the ability to store source node indices, breaking the backtracking chain. Resolved by introducing an integer matrix (`A_indices`) where `A[i,j] = i`, allowing `semiring.min_first` to assign correct parent indices, successfully reconstructing the full path.
- **Incorrect Predecessor Assignment**: Parent nodes were assigned inconsistent values (e.g., `[4, 4, 4]` for nodes reachable from node 2 at level 1, instead of `[2, 2, 2]`). Analysis showed that `semiring.min_plus` was summing frontier indices with edge values, producing invalid results. Switched to `semiring.min_first` to select the minimum frontier index as the parent, aligning with the directed graph structure and ensuring accurate predecessor tracking for paths like `[2, 3, 4, 8]`.
- **TypeError in Vector.outer Operation**: Encountered a `TypeError` when attempting `frontier.outer(A, semiring.any_pair)`, as `outer` expected a vector argument but received the adjacency matrix `A`. This stemmed from an effort to mask `A_indices` using an outer product to limit frontier expansion. Corrected by abandoning the `outer` approach, opting instead for `frontier_indices.vxm(A_indices, semiring.min_first)` with proper matrix-vector multiplication, restoring correct traversal across edges.
- **Infinite Loop in Path Reconstruction**: During backtracking, the path reconstruction loop failed to terminate, hanging when encountering self-loops (e.g., `predecessors[8] = 8`) or broken chains (e.g., `predecessors[1] = 1`). Diagnosed through logging, which highlighted circular references in the predecessor array. Implemented a `seen` set to track visited nodes, breaking the loop if a node was revisited or invalid (-1), ensuring termination and accurate path output `[2, 3, 4, 8]`.
- **Performance Overhead from Debugging**: Extensive logging of predecessor and parent states at each level (e.g., printing full arrays) slowed execution, especially as graph size increased. Identified this as a bottleneck during scaling tests. Mitigated by selectively enabling debug prints and removing them for production runs, improving runtime efficiency while retaining diagnostic capability.
- **Memory Constraints on Large Graphs**: Scaling to 5000 molecules and 20000 reactions revealed potential memory issues, with sparse matrices consuming significant RAM. Monitored memory usage and ensured GraphBLAS’s sparsity optimization was effective. Adjusted visualization to exclude large graphs, reducing memory footprint and maintaining performance.
- **Graph Connectivity Assumptions**: Assumed graph connectivity due to the chain, but random edge generation occasionally led to unreachable nodes. Detected during reachability checks (e.g., `reachable.nvals` lower than expected). Strengthened the chain inclusion logic in `generate_reaction_network` to guarantee a fully connected graph, ensuring all target nodes are reachable.

## Lessons Learned
- **Semiring Precision**: The choice of `min_first` over `min_plus` was critical for index selection, directly impacting path accuracy.
- **Matrix Design Impact**: The content of the adjacency matrix (e.g., integer indices vs. boolean) significantly influenced algorithm output.
- **Debugging Efficiency**: Intermediate state logging proved essential for identifying and resolving discrepancies.
- **GraphBLAS Compliance**: Adhering to operation constraints (e.g., avoiding matrix in `outer`) required referencing documentation.
- **Visualization Value**: Graphical validation of paths (e.g., `[2, 3, 4, 8]`) confirmed correctness and enhanced understanding.
- **Incremental Testing**: Starting with a small graph (10 nodes) uncovered issues early, facilitating scalable development.
- **Performance Optimization**: Selective logging and visualization management improved runtime and memory efficiency.
- **Connectivity Assurance**: Explicit connectivity checks or robust generation logic are necessary to avoid unreachable nodes.

## Future Development Notes
- **Enhancements**: Consider integrating weighted edges for Dijkstra’s algorithm or exploring parallel processing for larger graphs. Unit tests for path validation are recommended.
- **Documentation**: Plan to include inline comments, a usage example (e.g., 10 nodes yielding `[2, 3, 4, 8]`), and a debugging guide.
- **References**: Will link to GraphBLAS documentation for detailed operation insights.
- **Version Control**: Intend to use commits like “Resolved loop issue with `seen` set” and tag a stable release.
