import pygame


class GraphVisualizer:
    def __init__(self, graph):
        self.graph = graph
        self.width = 800
        self.height = 600
        self.radius = 20

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RouteForge Visualization")

        self.positions = self.compute_positions()

    def compute_positions(self):
        import math

        nodes = list(self.graph.nodes())
        pos = {}
        center_x, center_y = self.width // 2, self.height // 2
        r = 200

        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / len(nodes)
            x = center_x + int(r * math.cos(angle))
            y = center_y + int(r * math.sin(angle))
            pos[node] = (x, y)

        return pos

    def draw(self):
        running = True

        while running:
            self.screen.fill((30, 30, 30))

            # draw edges
            for u in self.graph.nodes():
                for v, w in self.graph.neighbors(u):
                    if u < v:
                        pygame.draw.line(
                            self.screen,
                            (200, 200, 200),
                            self.positions[u],
                            self.positions[v],
                            2
                        )

            # draw nodes
            for node, (x, y) in self.positions.items():
                pygame.draw.circle(self.screen, (0, 150, 255), (x, y), self.radius)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), self.radius, 2)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            pygame.display.flip()

        pygame.quit()