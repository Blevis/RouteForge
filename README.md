# RouteForge
### A Graph-Based Delivery Route Optimization System

**RouteForge** is a university-level graph algorithms project that models and analyzes a delivery network using fundamental data structures and algorithms. It demonstrates core concepts in graph theory including traversal, shortest path computation, and minimum spanning tree optimization.

Developed as part of a Data Structures & Algorithms final project.

---

## Team
- Blevis Allushi  
- Kristian Seraj  
- Renato Zotaj  
- Leandra Latifi  

---

## Project Overview

RouteForge simulates a delivery network where:
- **Nodes** represent locations (warehouses, depots, delivery points)
- **Edges** represent roads or routes between locations
- **Weights** represent distance, cost, or travel time

The system allows users to:
- Build and modify a graph
- Explore connectivity
- Compute optimal delivery routes
- Analyze and optimize the network structure

---

## How to Run

**Requirements:** Python 3.12+ (see `.python-version` if using pyenv).

```bash
cd RouteForge

# Create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

python main.py
```

Use menu option **10** for the pygame graph visualizer (requires `pygame`). Options **11–12** remove nodes/edges; option **13** loads a sample graph from `src/data/`.

Run tests:

```bash
pytest
```

---

## Core Features

### Graph Operations
- Add / remove nodes
- Add / remove edges
- Display adjacency structure
- Load sample datasets
- Handle disconnected graphs

### Traversal Algorithms
- Breadth-First Search (BFS)
- Depth-First Search (DFS)

### Optimization Algorithms
- Dijkstra's Algorithm (Shortest Path)
- Prim's Algorithm (Minimum Spanning Tree)
- Kruskal's Algorithm (Minimum Spanning Tree alternative)

---

## Key Concepts Demonstrated
- Graph representation (adjacency list)
- Greedy algorithms
- Traversal techniques
- Pathfinding optimization
- Complexity analysis
- Edge-case handling

---

## Project Structure

```text
RouteForge/
├── src/
│   ├── core/              # Graph, Edge, validators
│   ├── algorithms/        # BFS, DFS, Dijkstra, MST
│   ├── ui/                # Console menu
│   ├── utils/             # graph_generator, graph_io
│   ├── data/              # Sample JSON graphs
│   └── visualization/     # pygame visualizer
├── tests/                 # pytest unit tests
├── docs/                  # Academic report (LaTeX)
├── main.py
├── requirements.txt
└── README.md
```
