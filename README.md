# RouteForge
### A Graph-Based Delivery Route Optimization System

**RouteForge** is a university-level graph algorithms project that models and analyzes a delivery network using fundamental data structures and algorithms. It demonstrates core concepts in graph theory including traversal, shortest path computation, and minimum spanning tree optimization.

Developed as part of a Data Structures & Algorithms final project.

---

## 👥 Team
- Blevis Allushi  
- Kristian Seraj  
- Renato Zotaj  
- Leandra Latifi  

---

## 📌 Project Overview

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

## ⚙️ Core Features

### Graph Operations
- Add / remove nodes
- Add / remove edges
- Display adjacency structure
- Handle disconnected graphs

### Traversal Algorithms
- Breadth-First Search (BFS)
- Depth-First Search (DFS)

### Optimization Algorithms
- Dijkstra’s Algorithm (Shortest Path)
- Prim’s Algorithm (Minimum Spanning Tree)
- Kruskal’s Algorithm (Minimum Spanning Tree alternative)

---

## 🧠 Key Concepts Demonstrated
- Graph representation (adjacency list)
- Greedy algorithms
- Traversal techniques
- Pathfinding optimization
- Complexity analysis
- Edge-case handling

---

## 🏗️ Project Structure

```text
routeforge/
│
├── src/
│   ├── core/              # Graph, Node, Edge implementations
│   ├── algorithms/       # BFS, DFS, Dijkstra, MST algorithms
│   ├── ui/               # Console-based menu system
│   ├── utils/           # Helper functions
│   └── data/            # Sample datasets
│
├── tests/               # Unit tests
├── docs/                # Report, diagrams, documentation
├── assets/              # Images, visuals
├── main.py              # Entry point
├── requirements.txt
└── README.md
