from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set


@dataclass(frozen=True)
class Edge:
    u: str
    v: str
    weight: float


class Graph:
    """
    Weighted undirected graph implemented with an adjacency list.

    Nodes are stored as strings.
    Edges are stored as neighbor -> weight pairs.
    """

    def __init__(self) -> None:
        self._adj: Dict[str, Dict[str, float]] = {}

    def add_node(self, node: str) -> None:
        """Add a node if it does not already exist."""
        if node not in self._adj:
            self._adj[node] = {}

    def add_edge(self, u: str, v: str, weight: float) -> None:
        """
        Add or update an undirected weighted edge.

        If either node does not exist, it is created automatically.
        If the edge already exists, its weight is updated.
        """
        if weight < 0:
            raise ValueError("Edge weight must be non-negative.")

        self.add_node(u)
        self.add_node(v)

        self._adj[u][v] = weight
        self._adj[v][u] = weight

    def remove_node(self, node: str) -> bool:
        """
        Remove a node and all incident edges.
        Returns True if removed, False if node did not exist.
        """
        if node not in self._adj:
            return False

        for neighbor in list(self._adj[node].keys()):
            del self._adj[neighbor][node]

        del self._adj[node]
        return True

    def remove_edge(self, u: str, v: str) -> bool:
        """
        Remove an undirected edge.
        Returns True if removed, False if edge did not exist.
        """
        removed = False
        if u in self._adj and v in self._adj[u]:
            del self._adj[u][v]
            removed = True
        if v in self._adj and u in self._adj[v]:
            del self._adj[v][u]
            removed = True or removed
        return removed

    def has_node(self, node: str) -> bool:
        return node in self._adj

    def has_edge(self, u: str, v: str) -> bool:
        return u in self._adj and v in self._adj[u]

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        """
        Return neighbors of a node as a list of (neighbor, weight).
        Raises KeyError if node does not exist.
        """
        if node not in self._adj:
            raise KeyError(f"Node '{node}' does not exist.")
        return list(self._adj[node].items())

    def nodes(self) -> List[str]:
        return list(self._adj.keys())

    def edges(self) -> List[Edge]:
        """
        Return each undirected edge only once.
        """
        seen: Set[Tuple[str, str]] = set()
        result: List[Edge] = []

        for u in self._adj:
            for v, w in self._adj[u].items():
                key = tuple(sorted((u, v)))
                if key not in seen:
                    seen.add(key)
                    result.append(Edge(key[0], key[1], w))

        return result

    def order(self) -> int:
        """Number of nodes."""
        return len(self._adj)

    def size(self) -> int:
        """Number of undirected edges."""
        return len(self.edges())

    def display(self) -> None:
        """Print the adjacency list in a readable form."""
        if not self._adj:
            print("Graph is empty.")
            return

        for node in sorted(self._adj.keys()):
            neighbors = ", ".join(
                f"{nbr}({wt})" for nbr, wt in sorted(self._adj[node].items())
            )
            print(f"{node}: {neighbors}")

    def copy(self) -> "Graph":
        """Deep copy of the graph structure."""
        g = Graph()
        for node in self._adj:
            g.add_node(node)
        for edge in self.edges():
            g.add_edge(edge.u, edge.v, edge.weight)
        return g