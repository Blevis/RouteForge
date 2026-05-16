"""
src/core/validators.py
----------------------
RouteForge – Input validation utilities for the core graph layer.

All functions raise ValueError with a descriptive message on failure,
or return silently on success. Callers (Graph methods, UI layer) should
catch ValueError and surface the message appropriately.

Keeping validation here (not in graph.py or pygame_view.py) means:
  • Graph stays a pure data structure with minimal policy.
  • The UI layer stays presentation-only.
  • These rules are testable in isolation and reusable across algorithms.
"""

from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# Constants – adjust once here, enforced everywhere
# ---------------------------------------------------------------------------

#: Maximum allowed edge weight.
MAX_WEIGHT: float = 1_000_000.0

#: Minimum allowed edge weight (Graph already enforces >= 0, but
#: algorithms may further restrict to > 0; set to 0.0 to allow zero-weight
#: edges, or to a small positive epsilon if your algorithms require it).
MIN_WEIGHT: float = 0.0

#: Maximum characters in a node name.
MAX_NODE_NAME_LEN: int = 16

#: Allowed characters in a node name (alphanumeric + underscore + hyphen).
_ALLOWED_NAME_CHARS: frozenset[str] = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789_-"
)


# ---------------------------------------------------------------------------
# Weight validation
# ---------------------------------------------------------------------------

def validate_weight(weight: float) -> None:
    """
    Raise ValueError if *weight* is not a valid edge weight.

    Rules
    -----
    - Must be a real finite number (no NaN, no ±Inf).
    - Must be within [MIN_WEIGHT, MAX_WEIGHT].
    """
    if not isinstance(weight, (int, float)):
        raise ValueError(
            f"Weight must be a number, got {type(weight).__name__!r}."
        )

    if math.isnan(weight):
        raise ValueError("Weight must not be NaN.")

    if math.isinf(weight):
        raise ValueError("Weight must be finite, not ±Infinity.")

    if weight < MIN_WEIGHT:
        raise ValueError(
            f"Weight {weight} is below the minimum allowed value ({MIN_WEIGHT})."
        )

    if weight > MAX_WEIGHT:
        raise ValueError(
            f"Weight {weight} exceeds the maximum allowed value ({MAX_WEIGHT})."
        )


# ---------------------------------------------------------------------------
# Node name validation
# ---------------------------------------------------------------------------

def validate_node_name(name: str) -> None:
    """
    Raise ValueError if *name* is not a valid node identifier.

    Rules
    -----
    - Must be a non-empty string.
    - Length must not exceed MAX_NODE_NAME_LEN.
    - Characters must all be in _ALLOWED_NAME_CHARS (a-z, A-Z, 0-9, _, -).
    """
    if not isinstance(name, str):
        raise ValueError(
            f"Node name must be a string, got {type(name).__name__!r}."
        )

    if not name:
        raise ValueError("Node name must not be empty.")

    if len(name) > MAX_NODE_NAME_LEN:
        raise ValueError(
            f"Node name {name!r} is too long "
            f"(max {MAX_NODE_NAME_LEN} characters, got {len(name)})."
        )

    invalid = [ch for ch in name if ch not in _ALLOWED_NAME_CHARS]
    if invalid:
        bad = ", ".join(repr(ch) for ch in sorted(set(invalid)))
        raise ValueError(
            f"Node name {name!r} contains invalid character(s): {bad}. "
            f"Only letters, digits, underscores, and hyphens are allowed."
        )


# ---------------------------------------------------------------------------
# Edge validation (relationship between two nodes)
# ---------------------------------------------------------------------------

def validate_edge_nodes(u: str, v: str) -> None:
    """
    Raise ValueError if the pair (u, v) cannot form a valid edge.

    Rules
    -----
    - Both node names must individually pass validate_node_name.
    - u and v must not be the same node (no self-loops).
    """
    validate_node_name(u)
    validate_node_name(v)

    if u == v:
        raise ValueError(
            f"Self-loops are not allowed: cannot add edge from {u!r} to itself."
        )


# ---------------------------------------------------------------------------
# Convenience: validate a complete edge in one call
# ---------------------------------------------------------------------------

def validate_edge(u: str, v: str, weight: float) -> None:
    """
    Validate both the node pair and the weight together.
    Raises ValueError with a specific message on the first failure found.

    Usage (in Graph.add_edge, or in the UI before calling it)::

        from src.core.validators import validate_edge
        validate_edge(u, v, weight)   # raises on bad input
        graph.add_edge(u, v, weight)  # safe to call
    """
    validate_edge_nodes(u, v)
    validate_weight(weight)