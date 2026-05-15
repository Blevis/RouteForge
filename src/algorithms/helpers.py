from __future__ import annotations
from typing import Dict, List, Optional


def reconstruct_path(
    previous: Dict[str, Optional[str]],
    start: str,
    end: str
) -> Optional[List[str]]:
    """
    Reconstruct shortest path from Dijkstra predecessor map.
    """
    path = []
    current = end

    while current is not None:
        path.append(current)
        if current == start:
            break
        current = previous.get(current)

    if not path or path[-1] != start:
        return None

    path.reverse()
    return path