from src.core.graph import Graph
from src.algorithms.bfs import bfs
from src.algorithms.dijkstra import shortest_path
from src.algorithms.prim import prim_mst
from src.algorithms.kruskal import kruskal_mst


def _triangle_graph() -> Graph:
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "C", 4)
    return g


def test_bfs_visits_all_nodes():
    g = _triangle_graph()
    order = bfs(g, "A")
    assert set(order) == {"A", "B", "C"}


def test_dijkstra_shortest_path():
    g = _triangle_graph()
    path, dist = shortest_path(g, "A", "C")
    assert path == ["A", "B", "C"]
    assert dist == 3


def test_prim_and_kruskal_same_total_on_connected_graph():
    g = _triangle_graph()
    _, prim_total = prim_mst(g, "A")
    _, kruskal_total = kruskal_mst(g)
    assert prim_total == kruskal_total == 3
