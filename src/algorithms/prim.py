from __future__ import annotations

import heapq
from typing import List, Tuple

from src.core.graph import Graph, Edge


def prim_mst(graph: Graph, start: str | None = None) -> Tuple[List[Edge], float]:
    """
    Prim's algorithm for Minimum Spanning Tree.
    Returns:
        mst_edges: list of edges in the MST
        total_weight: sum of MST edge weights
    """
    if graph.order() == 0:
        return [], 0.0

    if start is None:
        start = graph.nodes()[0]

    if not graph.has_node(start):
        raise KeyError(f"Start node '{start}' does not exist.")

    visited = set([start])
    mst_edges: List[Edge] = []
    total_weight = 0.0
    pq: List[Tuple[float, str, str]] = []

    for neighbor, weight in graph.neighbors(start):
        heapq.heappush(pq, (weight, start, neighbor))

    while pq and len(visited) < graph.order():
        weight, u, v = heapq.heappop(pq)

        if v in visited:
            continue

        visited.add(v)
        mst_edges.append(Edge(u, v, weight))
        total_weight += weight

        for neighbor, w in graph.neighbors(v):
            if neighbor not in visited:
                heapq.heappush(pq, (w, v, neighbor))

    return mst_edges, total_weight