from src.core.graph import Graph
from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from src.algorithms.dijkstra import shortest_path
from src.algorithms.prim import prim_mst
from src.algorithms.kruskal import kruskal_mst


def build_sample_graph() -> Graph:
    g = Graph()
    g.add_edge("Warehouse", "A", 4)
    g.add_edge("Warehouse", "B", 2)
    g.add_edge("A", "C", 3)
    g.add_edge("B", "C", 1)
    g.add_edge("B", "D", 7)
    g.add_edge("C", "D", 2)
    g.add_edge("C", "E", 5)
    g.add_edge("D", "E", 1)
    return g


def main() -> None:
    g = build_sample_graph()

    print("=== GRAPH ===")
    g.display()

    print("\n=== BFS from Warehouse ===")
    print(bfs(g, "Warehouse"))

    print("\n=== DFS from Warehouse ===")
    print(dfs(g, "Warehouse"))

    print("\n=== Shortest path Warehouse -> E ===")
    path, dist = shortest_path(g, "Warehouse", "E")
    print("Path:", path)
    print("Distance:", dist)

    print("\n=== Prim MST ===")
    prim_edges, prim_total = prim_mst(g, "Warehouse")
    for e in prim_edges:
        print(f"{e.u} -- {e.v} ({e.weight})")
    print("Total:", prim_total)

    print("\n=== Kruskal MST ===")
    kruskal_edges, kruskal_total = kruskal_mst(g)
    for e in kruskal_edges:
        print(f"{e.u} -- {e.v} ({e.weight})")
    print("Total:", kruskal_total)


if __name__ == "__main__":
    main()