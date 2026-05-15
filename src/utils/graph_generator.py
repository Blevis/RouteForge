import random
from src.core.graph import Graph


def generate_random_graph(n_nodes=6, edge_probability=0.4, max_weight=10):
    """
    Generates a connected-ish random weighted graph.
    """
    g = Graph()

    nodes = [f"N{i}" for i in range(n_nodes)]

    for n in nodes:
        g.add_node(n)

    # ensure connectivity (chain)
    for i in range(n_nodes - 1):
        weight = random.randint(1, max_weight)
        g.add_edge(nodes[i], nodes[i + 1], weight)

    # add random edges
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if random.random() < edge_probability:
                weight = random.randint(1, max_weight)
                g.add_edge(nodes[i], nodes[j], weight)

    return g