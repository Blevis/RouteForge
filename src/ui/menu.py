from src.core.graph import Graph
from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from src.algorithms.dijkstra import shortest_path
from src.algorithms.prim import prim_mst
from src.algorithms.kruskal import kruskal_mst
from src.utils.graph_io import list_sample_graphs, load_graph


class Menu:
    def __init__(self):
        self.graph = Graph()

    def run(self):
        while True:
            self.print_menu()
            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self.add_node()
            elif choice == "2":
                self.add_edge()
            elif choice == "3":
                self.display_graph()
            elif choice == "4":
                self.run_bfs()
            elif choice == "5":
                self.run_dfs()
            elif choice == "6":
                self.run_dijkstra()
            elif choice == "7":
                self.run_prim()
            elif choice == "8":
                self.run_kruskal()
            elif choice == "9":
                self.load_random_graph()
            elif choice == "10":
                self.open_visualizer()
            elif choice == "11":
                self.remove_node()
            elif choice == "12":
                self.remove_edge()
            elif choice == "13":
                self.load_sample_graph()
            elif choice == "0":
                print("Exiting RouteForge...")
                break
            else:
                print("Invalid option.")

    def print_menu(self):
        print("\n" + "=" * 40)
        print(" ROUTEFORGE CLI ")
        print("=" * 40)
        print("1. Add Node")
        print("2. Add Edge")
        print("3. Display Graph")
        print("4. BFS Traversal")
        print("5. DFS Traversal")
        print("6. Shortest Path (Dijkstra)")
        print("7. Minimum Spanning Tree (Prim)")
        print("8. Minimum Spanning Tree (Kruskal)")
        print("9. Generate Random Graph")
        print("10. Open Graph Visualizer (pygame)")
        print("11. Remove Node")
        print("12. Remove Edge")
        print("13. Load Sample Graph")
        print("0. Exit")

    # -------------------------
    # BASIC GRAPH OPS
    # -------------------------

    def add_node(self):
        node = input("Enter node name: ").strip()
        try:
            self.graph.add_node(node)
            print(f"Node '{node}' added.")
        except ValueError as exc:
            print(exc)

    def add_edge(self):
        u = input("From node: ").strip()
        v = input("To node: ").strip()

        try:
            w = float(input("Weight: ").strip())
            self.graph.add_edge(u, v, w)
            print(f"Edge {u} -- {v} ({w}) added.")
        except ValueError as exc:
            print(exc)

    def remove_node(self):
        node = input("Node to remove: ").strip()
        if self.graph.remove_node(node):
            print(f"Node '{node}' removed.")
        else:
            print(f"Node '{node}' does not exist.")

    def remove_edge(self):
        u = input("From node: ").strip()
        v = input("To node: ").strip()
        if self.graph.remove_edge(u, v):
            print(f"Edge {u} -- {v} removed.")
        else:
            print(f"Edge {u} -- {v} does not exist.")

    def load_sample_graph(self):
        samples = list_sample_graphs()
        if not samples:
            print("No sample graphs found in src/data/.")
            return

        print("\nAvailable samples:")
        for i, path in enumerate(samples, start=1):
            print(f"  {i}. {path.stem}")

        choice = input("Select sample number: ").strip()
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(samples):
                raise ValueError
            self.graph = load_graph(samples[idx])
            print(f"Loaded '{samples[idx].stem}' ({self.graph.order()} nodes, "
                  f"{self.graph.size()} edges).")
        except ValueError:
            print("Invalid selection.")

    def display_graph(self):
        self.graph.display()

    # -------------------------
    # ALGORITHMS
    # -------------------------

    def run_bfs(self):
        start = input("Start node: ").strip()
        try:
            result = bfs(self.graph, start)
            print("BFS:", " → ".join(result))
        except KeyError as e:
            print(e)

    def run_dfs(self):
        start = input("Start node: ").strip()
        try:
            result = dfs(self.graph, start)
            print("DFS:", " → ".join(result))
        except KeyError as e:
            print(e)

    def run_dijkstra(self):
        start = input("Start node: ").strip()
        end = input("End node: ").strip()

        try:
            path, dist = shortest_path(self.graph, start, end)

            if path is None:
                print("No path found.")
            else:
                print("Shortest Path:", " → ".join(path))
                print("Total Cost:", dist)
        except KeyError as e:
            print(e)

    def run_prim(self):
        start = input("Start node (optional, press Enter to skip): ").strip()
        start = start if start else None

        mst, total = prim_mst(self.graph, start)
        self.print_mst(mst, total)

    def run_kruskal(self):
        mst, total = kruskal_mst(self.graph)
        self.print_mst(mst, total)

    def print_mst(self, mst, total):
        print("\nMST Edges:")
        for e in mst:
            print(f"{e.u} -- {e.v} ({e.weight})")
        print("Total Weight:", total)

        n = self.graph.order()
        if n > 1 and len(mst) < n - 1:
            print(
                "Warning: Graph may be disconnected; MST does not span all nodes."
            )

    def load_random_graph(self):
        from src.utils.graph_generator import generate_random_graph

        self.graph = generate_random_graph()
        print("Random graph generated.")

    def open_visualizer(self):
        from src.visualization.pygame_view import GraphVisualizer

        viz = GraphVisualizer(self.graph)
        viz.run()
