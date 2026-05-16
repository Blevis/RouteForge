from src.core.graph import Graph
from src.algorithms.bfs import bfs
from src.algorithms.dfs import dfs
from src.algorithms.dijkstra import shortest_path
from src.algorithms.prim import prim_mst
from src.algorithms.kruskal import kruskal_mst


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
        print("0. Exit")

    # -------------------------
    # BASIC GRAPH OPS
    # -------------------------

    def add_node(self):
        node = input("Enter node name: ").strip()
        self.graph.add_node(node)
        print(f"Node '{node}' added.")

    def add_edge(self):
        u = input("From node: ").strip()
        v = input("To node: ").strip()

        try:
            w = float(input("Weight: ").strip())
            self.graph.add_edge(u, v, w)
            print(f"Edge {u} -- {v} ({w}) added.")
        except ValueError:
            print("Invalid weight.")

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
    
    def load_random_graph(self):
        from src.utils.graph_generator import generate_random_graph

        self.graph = generate_random_graph()
        print("Random graph generated.")

    def open_visualizer(self):
        from src.visualization.pygame_view import GraphVisualizer

        viz = GraphVisualizer(self.graph)
        viz.run()