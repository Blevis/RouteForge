# RouteForge

**A Graph Algorithm Visualisation and Route Optimisation System**

RouteForge is a Python-based graph algorithms project built as part of a Year 2 Data Structures & Algorithms module. It provides an interactive environment for constructing weighted graphs, running classical graph algorithms, and visualising their execution step by step in real time.

---

## Team

| Name | |
|---|---|
| Blevis Allushi |
| Kristian Seraj |
| Renato Zotaj |
| Leandra Latifi |

---

## Features

### Graph Construction
- Add and remove nodes and edges interactively
- Assign and update edge weights
- Load built-in sample graphs or generate random connected graphs
- Full input validation (name format, weight range, self-loop prevention)

### Algorithms
| Algorithm | Purpose |
|---|---|
| Breadth-First Search (BFS) | Level-order graph traversal |
| Depth-First Search (DFS) | Depth-order graph traversal |
| Dijkstra's Algorithm | Single-source shortest path |
| Prim's Algorithm | Minimum spanning tree |
| Kruskal's Algorithm | Minimum spanning tree (edge-sorted) |

### Pygame Visualiser
- Interactive graph editor — click to place nodes, connect edges, set weights
- Step-by-step animation of all five algorithms with play/pause and variable speed
- Backward stepping through any algorithm execution
- Right-click to delete nodes or edges directly on the canvas
- Distance labels updated live during Dijkstra playback
- MST edges highlighted progressively for Prim and Kruskal

---

## Getting Started

**Requirements:** Python 3.12+

```bash
# Clone and enter the project
cd RouteForge

# Create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## CLI Menu

```
 1   Add node
 2   Add edge
 3   Display graph
 4   BFS traversal
 5   DFS traversal
 6   Shortest path (Dijkstra)
 7   Minimum spanning tree (Prim)
 8   Minimum spanning tree (Kruskal)
 9   Generate random graph
10   Open pygame visualiser
11   Remove node
12   Remove edge
13   Load sample graph
 0   Exit
```

---

## Visualiser Controls

### Edit Mode
| Input | Action |
|---|---|
| Left-click empty canvas | Add node |
| Left-click node | Select as edge start |
| Left-click second node | Open weight input |
| Left-click same node | Deselect |
| Right-click node | Delete node and all its edges |
| Right-click edge | Delete edge |
| Right-click (mid-selection) | Cancel selection |
| `Enter` | Confirm edge weight |
| `Esc` | Cancel current action |

### Algorithm Hotkeys
| Key | Algorithm |
|---|---|
| `B` | BFS |
| `D` | DFS |
| `K` | Dijkstra |
| `P` | Prim's MST |
| `U` | Kruskal's MST |

### Playback Controls
| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `→` / `←` | Step forward / backward |
| `+` / `-` | Speed up / slow down |
| `R` or `Esc` | Return to edit mode |

---

## Project Structure

```
RouteForge/
├── main.py
├── requirements.txt
├── README.md
├── docs/                        # LaTeX academic report
├── tests/                       # pytest unit tests
└── src/
    ├── core/
    │   ├── graph.py             # Graph, Edge dataclass
    │   └── validators.py        # Input validation
    ├── algorithms/
    │   ├── bfs.py
    │   ├── dfs.py
    │   ├── dijkstra.py
    │   ├── helpers.py           # Path reconstruction
    │   ├── prim.py
    │   └── kruskal.py
    ├── ui/
    │   └── menu.py              # CLI menu
    ├── utils/
    │   └── graph_generator.py   # Random graph generation
    ├── data/                    # Sample graph files
    └── visualization/
        └── pygame_view.py       # Interactive visualiser
```

---

## Running Tests

```bash
pytest
```

---

## Academic Report

A full technical report documenting the system architecture, data structures, algorithm pseudocode, complexity analysis, and design decisions is available in `docs/routeforge_report.pdf`.
