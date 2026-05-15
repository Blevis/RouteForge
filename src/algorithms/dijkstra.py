from __future__ import annotations

import heapq
from typing import Dict, Optional, Tuple, List

from src.core.graph import Graph
from src.algorithms.helpers import reconstruct_path


def dijkstra(graph: Graph, start: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Compute shortest-path distances from start to every node.
    Returns:
        distances: node -> shortest distance
        previous: node -> previous node in shortest path
    """
    if not graph.has_node(start):
        raise KeyError(f"Start node '{start}' does not exist.")

    distances: Dict[str, float] = {node: float("inf") for node in graph.nodes()}
    previous: Dict[str, Optional[str]] = {node: None for node in graph.nodes()}
    distances[start] = 0.0

    pq: List[Tuple[float, str]] = [(0.0, start)]
    visited = set()

    while pq:
        current_dist, node = heapq.heappop(pq)

        if node in visited:
            continue
        visited.add(node)

        for neighbor, weight in graph.neighbors(node):
            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))

    return distances, previous


def shortest_path(graph: Graph, start: str, end: str) -> Tuple[Optional[List[str]], float]:
    """
    Return the shortest path from start to end and its total weight.
    If unreachable, returns (None, inf).
    """
    distances, previous = dijkstra(graph, start)
    path = reconstruct_path(previous, start, end)
    return path, distances.get(end, float("inf"))