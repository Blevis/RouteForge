"""
src/core/graph.py
-----------------
RouteForge – Weighted undirected graph (adjacency-list representation).

Nodes are stored as strings.
Edges are stored as  node -> {neighbor: weight}  mappings.

Validation policy
-----------------
  • graph.py enforces *structural* invariants only:
      - nodes exist before edges reference them  (auto-created in add_edge)
      - edge weights are non-negative
  • *Domain* rules (name characters, weight range, NaN/Inf checks) live in
    src/core/validators.py and are called at the entry points add_node and
    add_edge so every code path — UI, tests, scripts — benefits automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from src.core.validators import validate_edge, validate_node_name


# ---------------------------------------------------------------------------
# Edge dataclass (immutable, hashable, canonical ordering)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Edge:
    u: str
    v: str
    weight: float


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class Graph:
    """
    Weighted undirected graph implemented with an adjacency list.

    Public surface
    --------------
    add_node(node)            – add a node (idempotent)
    add_edge(u, v, weight)    – add / update an undirected edge
    remove_node(node)         – remove node and all incident edges
    remove_edge(u, v)         – remove a single edge
    has_node(node)            – membership test
    has_edge(u, v)            – edge existence test
    nodes()                   – list of node names
    neighbors(node)           – list of (neighbor, weight) pairs
    edges()                   – list of Edge objects (each edge once)
    order()                   – number of nodes
    size()                    – number of undirected edges
    copy()                    – deep copy
    display()                 – pretty-print adjacency list
    """

    def __init__(self) -> None:
        self._adj: Dict[str, Dict[str, float]] = {}
        self.positions: Dict[str, Tuple[int, int]] = {}  # node -> (x, y)

    # ------------------------------------------------------------------
    # Position helpers  (used by the visualiser)
    # ------------------------------------------------------------------

    def set_position(self, node: str, x: int, y: int) -> None:
        self.positions[node] = (x, y)

    def get_position(self, node: str) -> Tuple[int, int] | None:
        return self.positions.get(node)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_node(self, node: str) -> None:
        """
        Add a node if it does not already exist.
        Raises ValueError (via validators) for invalid names.
        """
        validate_node_name(node)
        if node not in self._adj:
            self._adj[node] = {}

    def add_edge(self, u: str, v: str, weight: float) -> None:
        """
        Add or update an undirected weighted edge.

        If either endpoint does not exist it is created automatically.
        If the edge already exists its weight is updated silently.
        Raises ValueError for invalid node names, self-loops, or bad weights.
        """
        validate_edge(u, v, weight)  # name format, no self-loop, weight range/NaN

        # Auto-create endpoints without re-validating names (already done above)
        if u not in self._adj:
            self._adj[u] = {}
        if v not in self._adj:
            self._adj[v] = {}

        self._adj[u][v] = weight
        self._adj[v][u] = weight

    def remove_node(self, node: str) -> bool:
        """
        Remove a node and all incident edges.
        Returns True if the node existed and was removed, False otherwise.
        Also removes the stored position if present.
        """
        if node not in self._adj:
            return False

        for neighbor in list(self._adj[node]):
            del self._adj[neighbor][node]

        del self._adj[node]
        self.positions.pop(node, None)
        return True

    def remove_edge(self, u: str, v: str) -> bool:
        """
        Remove an undirected edge.
        Returns True if the edge existed and was removed, False otherwise.
        """
        # Original code had a logic bug:  `removed = True or removed`
        # always evaluates to True regardless of the second delete.
        # Fixed: track both directions independently.
        removed_uv = False
        removed_vu = False

        if u in self._adj and v in self._adj[u]:
            del self._adj[u][v]
            removed_uv = True

        if v in self._adj and u in self._adj[v]:
            del self._adj[v][u]
            removed_vu = True

        # For a well-formed graph both are True or both are False.
        # Return True only if at least one direction was actually removed.
        return removed_uv or removed_vu

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def has_node(self, node: str) -> bool:
        return node in self._adj

    def has_edge(self, u: str, v: str) -> bool:
        return u in self._adj and v in self._adj[u]

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        """
        Return (neighbor, weight) pairs for *node*.
        Raises KeyError if the node does not exist.
        """
        if node not in self._adj:
            raise KeyError(f"Node '{node}' does not exist.")
        return list(self._adj[node].items())

    def nodes(self) -> List[str]:
        return list(self._adj.keys())

    def edges(self) -> List[Edge]:
        """Return each undirected edge exactly once."""
        seen: Set[Tuple[str, str]] = set()
        result: List[Edge] = []

        for u, neighbors in self._adj.items():
            for v, w in neighbors.items():
                key = (min(u, v), max(u, v))   # canonical order, no string-sort ambiguity
                if key not in seen:
                    seen.add(key)
                    result.append(Edge(key[0], key[1], w))

        return result

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def order(self) -> int:
        """Number of nodes."""
        return len(self._adj)

    def size(self) -> int:
        """Number of undirected edges."""
        return len(self.edges())

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Print the adjacency list in a readable form."""
        if not self._adj:
            print("Graph is empty.")
            return

        for node in sorted(self._adj):
            neighbor_str = ", ".join(
                f"{nbr}({wt})" for nbr, wt in sorted(self._adj[node].items())
            )
            print(f"  {node}: {neighbor_str or '(isolated)'}")

    def copy(self) -> Graph:
        """Return a deep copy of this graph (structure and positions)."""
        g = Graph()
        for node in self._adj:
            g._adj[node] = {}              # bypass name validation for internal copy
        for edge in self.edges():
            g.add_edge(edge.u, edge.v, edge.weight)
        for node, pos in self.positions.items():
            g.positions[node] = pos
        return g