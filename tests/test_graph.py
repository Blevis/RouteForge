from src.core.graph import Graph


def test_add_node_and_edge():
    g = Graph()
    g.add_node("A")
    g.add_node("B")
    g.add_edge("A", "B", 3.0)
    assert g.has_node("A")
    assert g.has_edge("A", "B")
    assert g.size() == 1


def test_remove_node_removes_incident_edges():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    assert g.remove_node("B")
    assert not g.has_node("B")
    assert g.size() == 0


def test_remove_edge():
    g = Graph()
    g.add_edge("A", "B", 5)
    assert g.remove_edge("A", "B")
    assert not g.has_edge("A", "B")


def test_update_edge_weight():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("A", "B", 9)
    neighbors = dict(g.neighbors("A"))
    assert neighbors["B"] == 9
