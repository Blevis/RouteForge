import pygame
import math
from src.core.graph import Graph

class GraphVisualizer:
    def __init__(self, graph: Graph):
        self.graph = graph

        pygame.init()
        self.width, self.height = 900, 650
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RouteForge - Graph Visualizer")

        self.running = True
        self.font = pygame.font.SysFont("Arial", 14)

        self.node_radius = 18

        self.selected_node = None

    def compute_positions(self):
        nodes = self.graph.nodes()

        center_x, center_y = self.width // 2, self.height // 2
        radius = 220

        for i, node in enumerate(nodes):
            if node not in self.graph.positions:
                angle = (2 * math.pi * i) / max(len(nodes), 1)

                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))

                self.graph.set_position(node, x, y)

    def draw(self):
        self.screen.fill((25, 25, 25))

        self.compute_positions()

        # edges
        for u in self.graph.nodes():
            for v, w in self.graph.neighbors(u):

                if u < v:  # avoid double draw
                    x1, y1 = self.graph.get_position(u)
                    x2, y2 = self.graph.get_position(v)

                    pygame.draw.line(self.screen, (180, 180, 180), (x1, y1), (x2, y2), 2)

                    # EDGE WEIGHT LABEL (MIDPOINT)
                    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                    label = self.font.render(str(w), True, (255, 255, 0))
                    self.screen.blit(label, (mx, my))

        # nodes
        for node in self.graph.nodes():
            x, y = self.graph.get_position(node)

            pygame.draw.circle(self.screen, (0, 140, 255), (x, y), self.node_radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), self.node_radius, 2)

            # NODE LABEL
            text = self.font.render(node, True, (255, 255, 255))
            self.screen.blit(text, (x - 10, y - 10))

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                node_name = f"N{len(self.graph.nodes())}"
                self.graph.add_node(node_name)
                self.graph.set_position(node_name, x, y)

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()

        pygame.quit()