from __future__ import annotations

from collections import deque
from typing import List

from src.core.graph import Graph


def bfs(graph: Graph, start: str) -> List[str]:
    """
    Breadth-first search traversal order.
    """
    if not graph.has_node(start):
        raise KeyError(f"Start node '{start}' does not exist.")

    visited = set([start])
    queue = deque([start])
    order: List[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor, _ in sorted(graph.neighbors(node), key=lambda x: x[0]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return order