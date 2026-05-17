from pathlib import Path

from src.core.graph import Graph
from src.utils.graph_io import DATA_DIR, load_graph, save_graph


def test_load_sample_delivery_small():
    path = DATA_DIR / "delivery_small.json"
    g = load_graph(path)
    assert g.order() == 5
    assert g.size() == 7


def test_save_and_load_round_trip(tmp_path: Path):
    g = Graph()
    g.add_edge("X", "Y", 2.5)
    out = tmp_path / "roundtrip.json"
    save_graph(g, out)
    loaded = load_graph(out)
    assert loaded.order() == 2
    assert loaded.has_edge("X", "Y")
    assert dict(loaded.neighbors("X"))["Y"] == 2.5
