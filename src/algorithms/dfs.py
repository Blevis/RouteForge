from __future__ import annotations

from typing import List

from src.core.graph import Graph


def dfs(graph: Graph, start: str) -> List[str]:
    """
    Depth-first search traversal order.
    Iterative version to avoid recursion depth issues.
    """
    if not graph.has_node(start):
        raise KeyError(f"Start node '{start}' does not exist.")

    visited = set()
    stack = [start]
    order: List[str] = []

    while stack:
        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)
        order.append(node)

        neighbors = sorted(graph.neighbors(node), key=lambda x: x[0], reverse=True)
        for neighbor, _ in neighbors:
            if neighbor not in visited:
                stack.append(neighbor)

    return order