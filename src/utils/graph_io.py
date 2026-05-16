"""
src/utils/graph_io.py
---------------------
Load and save RouteForge graphs as JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from src.core.graph import Graph

# Default directory for bundled sample graphs (relative to project root).
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_graph(path: Union[str, Path]) -> Graph:
    """
    Load a graph from a JSON file.

    Expected format::

        {
          "nodes": ["A", "B"],
          "edges": [{"u": "A", "v": "B", "weight": 1.0}]
        }
    """
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    g = Graph()
    for node in data.get("nodes", []):
        g.add_node(str(node))

    for edge in data.get("edges", []):
        u = str(edge["u"])
        v = str(edge["v"])
        weight = float(edge["weight"])
        g.add_edge(u, v, weight)

    return g


def save_graph(graph: Graph, path: Union[str, Path]) -> None:
    """Write a graph to JSON (nodes + edges; positions omitted)."""
    path = Path(path)
    payload = {
        "nodes": sorted(graph.nodes()),
        "edges": [
            {"u": e.u, "v": e.v, "weight": e.weight}
            for e in sorted(graph.edges(), key=lambda e: (e.u, e.v))
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def list_sample_graphs() -> List[Path]:
    """Return available sample JSON files in src/data/, sorted by name."""
    if not DATA_DIR.is_dir():
        return []
    return sorted(DATA_DIR.glob("*.json"))


def load_sample(name: str) -> Graph:
    """
    Load a sample by filename (e.g. ``delivery_small.json``) or stem
    (e.g. ``delivery_small``).
    """
    path = Path(name)
    if path.suffix != ".json":
        path = DATA_DIR / f"{name}.json"
    else:
        path = DATA_DIR / path.name
    if not path.is_file():
        raise FileNotFoundError(f"Sample graph not found: {path}")
    return load_graph(path)
