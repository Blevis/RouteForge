from __future__ import annotations

from typing import Dict, List, Tuple

from src.core.graph import Graph, Edge


class DisjointSet:
    def __init__(self, items: List[str]) -> None:
        self.parent: Dict[str, str] = {item: item for item in items}
        self.rank: Dict[str, int] = {item: 0 for item in items}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> bool:
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
        else:
            self.parent[root_b] = root_a
            self.rank[root_a] += 1

        return True


def kruskal_mst(graph: Graph) -> Tuple[List[Edge], float]:
    """
    Kruskal's algorithm for Minimum Spanning Tree.
    Returns:
        mst_edges: list of edges in the MST
        total_weight: sum of MST edge weights
    """
    nodes = graph.nodes()
    if not nodes:
        return [], 0.0

    ds = DisjointSet(nodes)
    edges = sorted(graph.edges(), key=lambda e: e.weight)

    mst_edges: List[Edge] = []
    total_weight = 0.0

    for edge in edges:
        if ds.union(edge.u, edge.v):
            mst_edges.append(edge)
            total_weight += edge.weight

            if len(mst_edges) == len(nodes) - 1:
                break

    return mst_edges, total_weight