"""
src/visualization/pygame_view.py
---------------------------------
RouteForge - Interactive Graph Visualizer (pygame)

Two modes
---------
  EDIT mode   - build the graph interactively
  ALGO mode   - step through BFS / DFS / Dijkstra with playback controls

Edit controls
-------------
  Left-click   empty space     -> Add node
  Left-click   node            -> Select as edge start (highlighted green)
  Left-click   second node     -> Begin edge weight entry
  Right-click                  -> Cancel current selection
  Escape                       -> Cancel any in-progress action
  Backspace    (weight input)  -> Delete last character
  Enter        (weight input)  -> Confirm edge with typed weight
  Scroll wheel                 -> Ignored

Algorithm controls (shown in sidebar when active)
--------------------------------------------------
  B            -> Run BFS  (prompts for start node via sidebar click)
  D            -> Run DFS  (prompts for start node via sidebar click)
  K            -> Run Dijkstra (prompts start + end via sidebar clicks)
  Space        -> Play / Pause
  Right arrow  -> Step forward
  Left arrow   -> Step backward
  +  /  =      -> Speed up
  -            -> Slow down
  R            -> Reset - return to edit mode

Node picking for algorithms
---------------------------
  After pressing B / D / K the visualiser enters "pick" mode.
  Click any node on the canvas to select it as start (and for Dijkstra,
  then click a second node for the end).  The sidebar shows a prompt.
"""

from __future__ import annotations

import math
import heapq
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import pygame

from src.core.graph import Graph
from src.core.validators import validate_weight


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BG_COLOR          = (15,  17,  22)
GRID_COLOR        = (28,  32,  40)
NODE_DEFAULT      = (30, 120, 220)
NODE_SELECTED     = (30, 200, 110)
NODE_HOVER        = (60, 150, 240)
NODE_BORDER       = (200, 215, 235)
EDGE_COLOR        = (140, 155, 175)
EDGE_PENDING      = (255, 200,  50)
WEIGHT_LABEL      = (255, 220,  60)
NODE_TEXT         = (230, 240, 255)
UI_TEXT           = (180, 190, 205)
INPUT_BOX_BG      = ( 22,  26,  34)
INPUT_BOX_BORDER  = (255, 200,  50)
INPUT_BOX_TEXT    = (230, 240, 255)
STATUS_OK         = ( 80, 200, 120)
STATUS_ERR        = (220,  80,  80)
PANEL_BG          = (20,  23,  30, 200)

# Algorithm colours
ALGO_VISITED      = ( 20, 160, 140)   # fully processed - teal
ALGO_FRONTIER     = (220, 130,  30)   # in queue / stack / heap - orange
ALGO_ACTIVE       = (240, 240, 255)   # node being expanded this step - white
ALGO_EDGE_USED    = ( 20, 160, 140)   # traversed edge - teal
ALGO_PATH         = (255, 210,  50)   # Dijkstra final path - gold
ALGO_PATH_NODE    = (255, 180,  20)   # nodes on final path

# Pick-mode highlight
PICK_START_COLOR  = (30, 200, 110)
PICK_END_COLOR    = (220,  80,  80)


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
NODE_RADIUS   = 22
PANEL_WIDTH   = 240
LAYOUT_RADIUS = 240

# Playback
DEFAULT_FPS_ALGO  = 2      # steps per second at default speed
SPEED_LEVELS      = [0.5, 1, 2, 4, 8]   # steps/sec options


# ---------------------------------------------------------------------------
# Algorithm step dataclass
# ---------------------------------------------------------------------------

@dataclass
class AlgoStep:
    """
    A single animation frame of an algorithm.

    visited       - nodes fully processed so far
    frontier      - nodes currently in queue / stack / heap
    active_node   - the node being expanded this step (highlighted white)
    active_edges  - set of (u,v) pairs that have been traversed so far
    active_edge   - the single edge being relaxed / traversed this step
    dist_labels   - optional {node: distance_str} for Dijkstra
    path_nodes    - nodes on the final shortest path (Dijkstra last step)
    path_edges    - edges on the final shortest path
    description   - human-readable line shown in the sidebar
    """
    visited      : Set[str]                    = field(default_factory=set)
    frontier     : Set[str]                    = field(default_factory=set)
    active_node  : Optional[str]               = None
    active_edges : Set[Tuple[str,str]]         = field(default_factory=set)
    active_edge  : Optional[Tuple[str,str]]    = None
    dist_labels  : Dict[str, str]              = field(default_factory=dict)
    path_nodes   : Set[str]                    = field(default_factory=set)
    path_edges   : Set[Tuple[str,str]]         = field(default_factory=set)
    description  : str                         = ""


# ---------------------------------------------------------------------------
# Step generators  (mirror the real algorithms exactly, recording each step)
# ---------------------------------------------------------------------------

def _bfs_steps(graph: Graph, start: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    visited: Set[str] = {start}
    queue: deque = deque([start])
    active_edges: Set[Tuple[str,str]] = set()

    steps.append(AlgoStep(
        visited=set(), frontier={start},
        active_node=start,
        description=f"Start at '{start}' - add to queue"
    ))

    while queue:
        node = queue.popleft()
        current_visited = set(visited) - set(queue)

        for neighbor, _ in sorted(graph.neighbors(node), key=lambda x: x[0]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                edge = (min(node, neighbor), max(node, neighbor))
                active_edges.add(edge)

                steps.append(AlgoStep(
                    visited=set(current_visited),
                    frontier=set(queue),
                    active_node=node,
                    active_edges=set(active_edges),
                    active_edge=edge,
                    description=f"From '{node}': discover '{neighbor}'"
                ))

        steps.append(AlgoStep(
            visited=set(visited) - set(queue),
            frontier=set(queue),
            active_node=node,
            active_edges=set(active_edges),
            description=f"'{node}' fully processed"
        ))

    return steps


def _dfs_steps(graph: Graph, start: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    visited: Set[str] = set()
    stack: List[str] = [start]
    active_edges: Set[Tuple[str,str]] = set()

    steps.append(AlgoStep(
        visited=set(), frontier={start},
        active_node=start,
        description=f"Start at '{start}' - push to stack"
    ))

    while stack:
        node = stack.pop()
        if node in visited:
            continue

        visited.add(node)
        frontier = set(stack) - visited

        steps.append(AlgoStep(
            visited=set(visited),
            frontier=frontier,
            active_node=node,
            active_edges=set(active_edges),
            description=f"Visit '{node}'"
        ))

        neighbors = sorted(graph.neighbors(node), key=lambda x: x[0], reverse=True)
        for neighbor, _ in neighbors:
            if neighbor not in visited:
                stack.append(neighbor)
                edge = (min(node, neighbor), max(node, neighbor))
                active_edges.add(edge)

                steps.append(AlgoStep(
                    visited=set(visited),
                    frontier=set(stack) - visited,
                    active_node=node,
                    active_edges=set(active_edges),
                    active_edge=edge,
                    description=f"From '{node}': push '{neighbor}' to stack"
                ))

    return steps


def _dijkstra_steps(graph: Graph, start: str, end: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    distances: Dict[str, float] = {n: float("inf") for n in graph.nodes()}
    previous: Dict[str, Optional[str]] = {n: None for n in graph.nodes()}
    distances[start] = 0.0

    pq: List[Tuple[float, str]] = [(0.0, start)]
    visited: Set[str] = set()
    active_edges: Set[Tuple[str,str]] = set()

    def dist_label(n):
        d = distances[n]
        return "inf" if d == float("inf") else str(int(d) if d == int(d) else round(d, 1))

    steps.append(AlgoStep(
        visited=set(),
        frontier={start},
        active_node=start,
        dist_labels={n: dist_label(n) for n in graph.nodes()},
        description=f"Start at '{start}' - dist=0, all others=inf"
    ))

    while pq:
        current_dist, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)

        steps.append(AlgoStep(
            visited=set(visited),
            frontier={n for _, n in pq} - visited,
            active_node=node,
            active_edges=set(active_edges),
            dist_labels={n: dist_label(n) for n in graph.nodes()},
            description=f"Expand '{node}' (dist={dist_label(node)})"
        ))

        for neighbor, weight in graph.neighbors(node):
            new_dist = current_dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))
                edge = (min(node, neighbor), max(node, neighbor))
                active_edges.add(edge)

                steps.append(AlgoStep(
                    visited=set(visited),
                    frontier={n for _, n in pq} - visited,
                    active_node=node,
                    active_edges=set(active_edges),
                    active_edge=edge,
                    dist_labels={n: dist_label(n) for n in graph.nodes()},
                    description=(
                        f"Relax '{node}'->'{neighbor}': "
                        f"{dist_label(node)}+{weight}={dist_label(neighbor)}"
                    )
                ))

    # Reconstruct path for the final step
    path_nodes: Set[str] = set()
    path_edges: Set[Tuple[str,str]] = set()
    cur = end
    while cur is not None:
        path_nodes.add(cur)
        prev = previous.get(cur)
        if prev is not None:
            path_edges.add((min(prev, cur), max(prev, cur)))
        cur = prev

    total = distances.get(end, float("inf"))
    total_str = "unreachable" if total == float("inf") else str(round(total, 2))

    steps.append(AlgoStep(
        visited=set(visited),
        frontier=set(),
        active_node=end,
        active_edges=set(active_edges),
        dist_labels={n: dist_label(n) for n in graph.nodes()},
        path_nodes=path_nodes,
        path_edges=path_edges,
        description=f"Done. '{start}'->'{end}' = {total_str}"
    ))

    return steps


# ---------------------------------------------------------------------------
# AlgoPlayer - owns all playback state
# ---------------------------------------------------------------------------

@dataclass
class AlgoPlayer:
    algo_name  : str
    steps      : List[AlgoStep]
    index      : int   = 0
    playing    : bool  = False
    speed_idx  : int   = 1          # index into SPEED_LEVELS
    _tick      : float = 0.0        # accumulated time (seconds)

    @property
    def current_step(self) -> AlgoStep:
        return self.steps[self.index]

    @property
    def speed(self) -> float:
        return SPEED_LEVELS[self.speed_idx]

    def advance_time(self, dt: float) -> None:
        if not self.playing:
            return
        self._tick += dt
        interval = 1.0 / self.speed
        while self._tick >= interval and self.index < len(self.steps) - 1:
            self.index += 1
            self._tick -= interval
        if self.index >= len(self.steps) - 1:
            self.playing = False

    def step_forward(self) -> None:
        if self.index < len(self.steps) - 1:
            self.index += 1

    def step_back(self) -> None:
        if self.index > 0:
            self.index -= 1

    def speed_up(self) -> None:
        self.speed_idx = min(self.speed_idx + 1, len(SPEED_LEVELS) - 1)

    def slow_down(self) -> None:
        self.speed_idx = max(self.speed_idx - 1, 0)


# ---------------------------------------------------------------------------
# GraphVisualizer
# ---------------------------------------------------------------------------

class GraphVisualizer:

    # -----------------------------------------------------------------------
    # Init
    # -----------------------------------------------------------------------

    def __init__(self, graph: Graph):
        self.graph = graph

        pygame.init()

        self.width, self.height = 1100, 720
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("RouteForge  -  Graph Visualizer")

        self.clock   = pygame.time.Clock()
        self.running = True

        self.font_node   = pygame.font.SysFont("Consolas", 14, bold=True)
        self.font_ui     = pygame.font.SysFont("Segoe UI",  13)
        self.font_title  = pygame.font.SysFont("Consolas",  17, bold=True)
        self.font_input  = pygame.font.SysFont("Consolas",  16)
        self.font_status = pygame.font.SysFont("Segoe UI",  12, italic=True)
        self.font_dist   = pygame.font.SysFont("Consolas",  11, bold=True)

        # ---------- Edit state ----------
        self.edge_start   = None
        self.pending_edge = None
        self.hover_node   = None
        self.input_mode   = False
        self.weight_input = ""
        self._node_counter = 0

        # ---------- Status bar ----------
        self._status_msg   = ""
        self._status_color = STATUS_OK
        self._status_timer = 0

        # ---------- Algorithm state ----------
        # "edit"  -> normal edit mode
        # "pick_start" -> waiting for user to click a start node
        # "pick_end"   -> waiting for user to click an end node (Dijkstra)
        # "algo"  -> AlgoPlayer is active
        self._mode         : str            = "edit"
        self._algo_player  : Optional[AlgoPlayer] = None
        self._pending_algo : str            = ""    # "bfs" | "dfs" | "dijkstra"
        self._pick_start   : Optional[str]  = None  # chosen start node

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    def _set_status(self, msg, ok=True, duration=150):
        self._status_msg   = msg
        self._status_color = STATUS_OK if ok else STATUS_ERR
        self._status_timer = duration

    # -----------------------------------------------------------------------
    # Auto-layout
    # -----------------------------------------------------------------------

    def _ensure_positions(self):
        nodes = self.graph.nodes()
        if not nodes:
            return
        cx, cy = (self.width + PANEL_WIDTH) // 2, self.height // 2
        total  = len(nodes)
        for node in nodes:
            if node not in self.graph.positions:
                idx   = list(nodes).index(node)
                angle = (2 * math.pi * idx) / max(total, 1)
                x     = cx + int(LAYOUT_RADIUS * math.cos(angle))
                y     = cy + int(LAYOUT_RADIUS * math.sin(angle))
                self.graph.set_position(node, x, y)

    # -----------------------------------------------------------------------
    # Algorithm launchers
    # -----------------------------------------------------------------------

    def _start_pick(self, algo: str):
        """Enter node-picking mode for the given algorithm."""
        if not self.graph.nodes():
            self._set_status("Graph is empty.", ok=False)
            return
        self._cancel_action()
        self._pending_algo = algo
        self._pick_start   = None
        self._mode         = "pick_start"
        label = {"bfs": "BFS", "dfs": "DFS", "dijkstra": "Dijkstra"}[algo]
        self._set_status(f"{label}: click a START node on the canvas.", duration=999)

    def _launch_algo(self, start: str, end: Optional[str] = None):
        """Build the step list and enter algo mode."""
        algo = self._pending_algo
        try:
            if algo == "bfs":
                steps = _bfs_steps(self.graph, start)
                name  = f"BFS from '{start}'"
            elif algo == "dfs":
                steps = _dfs_steps(self.graph, start)
                name  = f"DFS from '{start}'"
            else:  # dijkstra
                steps = _dijkstra_steps(self.graph, start, end)
                name  = f"Dijkstra '{start}' -> '{end}'"
        except KeyError as exc:
            self._set_status(str(exc), ok=False)
            self._mode = "edit"
            return

        self._algo_player = AlgoPlayer(algo_name=name, steps=steps)
        self._mode        = "algo"
        self._set_status(f"{name} - Space to play, arrows to step, R to reset", duration=300)

    def _reset_to_edit(self):
        self._mode        = "edit"
        self._algo_player = None
        self._pending_algo = ""
        self._pick_start   = None
        self._cancel_action()
        self._set_status("Returned to edit mode.")

    # -----------------------------------------------------------------------
    # Draw helpers - grid & panel
    # -----------------------------------------------------------------------

    def _draw_grid(self):
        spacing = 40
        for gx in range(PANEL_WIDTH, self.width, spacing):
            for gy in range(0, self.height, spacing):
                pygame.draw.circle(self.screen, GRID_COLOR, (gx, gy), 1)

    def _draw_panel_edit(self):
        """Sidebar content when in edit mode."""
        instructions = [
            ("ADD NODE",       "Left-click empty space"),
            ("START EDGE",     "Left-click a node"),
            ("FINISH EDGE",    "Left-click second node"),
            ("CONFIRM WEIGHT", "Type weight + Enter"),
            ("CANCEL",         "Escape / Right-click"),
            ("",               ""),
            ("RUN BFS",        "Press  B"),
            ("RUN DFS",        "Press  D"),
            ("RUN DIJKSTRA",   "Press  K"),
        ]
        y = 72
        for label, desc in instructions:
            if not label:
                y += 6
                continue
            self.screen.blit(
                self.font_status.render(label, True, (100, 160, 220)), (15, y)
            )
            y += 14
            self.screen.blit(self.font_ui.render(desc, True, UI_TEXT), (18, y))
            y += 20

    def _draw_panel_pick(self):
        """Sidebar content when picking start/end nodes."""
        algo_label = {"bfs": "BFS", "dfs": "DFS", "dijkstra": "Dijkstra"}.get(
            self._pending_algo, ""
        )
        self.screen.blit(
            self.font_title.render(algo_label, True, ALGO_FRONTIER), (15, 72)
        )

        if self._mode == "pick_start":
            prompt = "Click START node"
            color  = PICK_START_COLOR
        else:
            prompt = "Click END node"
            color  = PICK_END_COLOR

        self.screen.blit(
            self.font_ui.render(prompt, True, color), (15, 96)
        )

        if self._pick_start:
            self.screen.blit(
                self.font_ui.render(f"Start: {self._pick_start}", True, PICK_START_COLOR),
                (15, 116)
            )

        self.screen.blit(
            self.font_status.render("Esc to cancel", True, (120, 130, 145)), (15, 140)
        )

    def _draw_panel_algo(self):
        """Sidebar content during algorithm playback."""
        p = self._algo_player
        if p is None:
            return

        # Title
        self.screen.blit(
            self.font_title.render(p.algo_name[:22], True, (255, 255, 255)), (15, 72)
        )

        # Step counter
        step_str = f"Step {p.index + 1} / {len(p.steps)}"
        self.screen.blit(self.font_ui.render(step_str, True, UI_TEXT), (15, 94))

        # Description (word-wrap at ~26 chars)
        desc  = p.current_step.description
        words = desc.split()
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + 1 > 26:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)

        y = 114
        for line in lines[:3]:
            self.screen.blit(self.font_ui.render(line, True, (200, 210, 220)), (15, y))
            y += 16

        y = max(y + 6, 168)
        pygame.draw.line(self.screen, (45, 52, 68), (12, y), (PANEL_WIDTH - 18, y), 1)
        y += 8

        # Legend
        legend = [
            (ALGO_ACTIVE,   "Active node"),
            (ALGO_FRONTIER, "Frontier"),
            (ALGO_VISITED,  "Visited"),
        ]
        if p.algo_name.startswith("Dijkstra"):
            legend.append((ALGO_PATH_NODE, "Shortest path"))

        for color, label in legend:
            pygame.draw.circle(self.screen, color, (22, y + 6), 6)
            self.screen.blit(self.font_ui.render(label, True, UI_TEXT), (34, y))
            y += 18

        y += 6
        pygame.draw.line(self.screen, (45, 52, 68), (12, y), (PANEL_WIDTH - 18, y), 1)
        y += 8

        # Controls
        controls = [
            ("Space",  "Play / Pause"),
            ("->  <-", "Step forward / back"),
            ("+  -",   "Speed up / slow down"),
            ("R",      "Reset to edit mode"),
        ]
        for key, action in controls:
            self.screen.blit(
                self.font_status.render(key, True, (100, 160, 220)), (15, y)
            )
            y += 13
            self.screen.blit(self.font_ui.render(action, True, UI_TEXT), (18, y))
            y += 17

        # Speed + play state
        y += 4
        state_str = "PLAYING" if p.playing else "PAUSED"
        state_col = STATUS_OK if p.playing else (180, 180, 80)
        self.screen.blit(self.font_status.render(state_str, True, state_col), (15, y))
        y += 16
        spd_str = f"Speed: {p.speed}x"
        self.screen.blit(self.font_ui.render(spd_str, True, UI_TEXT), (15, y))

    def _draw_panel(self):
        surf = pygame.Surface((PANEL_WIDTH - 10, self.height), pygame.SRCALPHA)
        surf.fill(PANEL_BG)
        self.screen.blit(surf, (0, 0))

        self.screen.blit(
            self.font_title.render("ROUTEFORGE", True, (255, 255, 255)), (15, 16)
        )
        self.screen.blit(
            self.font_ui.render("Graph Visualizer", True, (120, 135, 160)), (17, 38)
        )
        pygame.draw.line(self.screen, (45, 52, 68), (12, 58), (PANEL_WIDTH - 18, 58), 1)

        if self._mode == "edit":
            self._draw_panel_edit()
        elif self._mode in ("pick_start", "pick_end"):
            self._draw_panel_pick()
        else:
            self._draw_panel_algo()

        # Stats footer
        y = self.height - 46
        pygame.draw.line(self.screen, (45, 52, 68), (12, y - 6), (PANEL_WIDTH - 18, y - 6), 1)
        for stat in (f"Nodes : {self.graph.order()}", f"Edges : {self.graph.size()}"):
            self.screen.blit(self.font_ui.render(stat, True, (130, 145, 165)), (15, y))
            y += 18

    # -----------------------------------------------------------------------
    # Draw helpers - canvas
    # -----------------------------------------------------------------------

    def _draw_edges(self):
        step = self._algo_player.current_step if self._algo_player else None

        for u in self.graph.nodes():
            for v, w in self.graph.neighbors(u):
                if u >= v:
                    continue

                x1, y1 = self.graph.get_position(u)
                x2, y2 = self.graph.get_position(v)
                edge   = (min(u, v), max(u, v))

                # Choose edge colour
                if step is not None:
                    if edge in step.path_edges:
                        color     = ALGO_PATH
                        thickness = 4
                    elif edge == step.active_edge:
                        color     = (255, 255, 255)
                        thickness = 3
                    elif edge in step.active_edges:
                        color     = ALGO_EDGE_USED
                        thickness = 2
                    else:
                        color     = EDGE_COLOR
                        thickness = 1
                else:
                    color     = EDGE_COLOR
                    thickness = 2

                pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), thickness)

                # Weight badge
                mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                label  = self.font_node.render(str(w), True, WEIGHT_LABEL)
                rect   = label.get_rect(center=(mx, my))
                pygame.draw.rect(self.screen, (30, 34, 44), rect.inflate(6, 6), border_radius=4)
                self.screen.blit(label, rect)

    def _draw_pending_edge_line(self):
        if self._mode != "edit":
            return
        if self.edge_start is None or self.input_mode:
            return
        x1, y1 = self.graph.get_position(self.edge_start)
        mx, my  = pygame.mouse.get_pos()
        pygame.draw.line(self.screen, EDGE_PENDING, (x1, y1), (mx, my), 2)

    def _node_color(self, node: str) -> tuple:
        """Determine fill colour for a node given current mode & step."""
        step = self._algo_player.current_step if self._algo_player else None

        # Pick mode highlights
        if self._mode == "pick_start":
            if node == self._pick_start:
                return PICK_START_COLOR
        if self._mode == "pick_end":
            if node == self._pick_start:
                return PICK_START_COLOR

        if step is not None:
            if node in step.path_nodes:
                return ALGO_PATH_NODE
            if node == step.active_node:
                return ALGO_ACTIVE
            if node in step.visited:
                return ALGO_VISITED
            if node in step.frontier:
                return ALGO_FRONTIER
            return NODE_DEFAULT

        # Edit mode
        if node == self.edge_start:
            return NODE_SELECTED
        if node == self.hover_node:
            return NODE_HOVER
        return NODE_DEFAULT

    def _draw_nodes(self):
        step = self._algo_player.current_step if self._algo_player else None

        for node in self.graph.nodes():
            x, y  = self.graph.get_position(node)
            color = self._node_color(node)

            # Glow for selected / active
            if node == self.edge_start or (step and node == step.active_node):
                glow = pygame.Surface((NODE_RADIUS * 4, NODE_RADIUS * 4), pygame.SRCALPHA)
                gc   = (*color, 55)
                pygame.draw.circle(
                    glow, gc,
                    (NODE_RADIUS * 2, NODE_RADIUS * 2), NODE_RADIUS + 7
                )
                self.screen.blit(glow, (x - NODE_RADIUS * 2, y - NODE_RADIUS * 2))

            pygame.draw.circle(self.screen, color,       (x, y), NODE_RADIUS)
            pygame.draw.circle(self.screen, NODE_BORDER, (x, y), NODE_RADIUS, 2)

            label = self.font_node.render(node, True, NODE_TEXT)
            self.screen.blit(label, label.get_rect(center=(x, y)))

            # Dijkstra distance labels (drawn above the node)
            if step and step.dist_labels:
                dist_str = step.dist_labels.get(node, "")
                if dist_str:
                    dl = self.font_dist.render(dist_str, True, ALGO_PATH)
                    self.screen.blit(dl, dl.get_rect(center=(x, y - NODE_RADIUS - 10)))

    def _draw_weight_input(self):
        if not self.input_mode or self.pending_edge is None:
            return
        u, v   = self.pending_edge
        x1, y1 = self.graph.get_position(u)
        x2, y2 = self.graph.get_position(v)
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2

        box_w, box_h = 210, 46
        bx = min(max(mx - box_w // 2, PANEL_WIDTH + 8), self.width  - box_w - 8)
        by = min(max(my - box_h - 16, 8),               self.height - box_h - 32)

        box = pygame.Rect(bx, by, box_w, box_h)
        pygame.draw.rect(self.screen, INPUT_BOX_BG,     box, border_radius=6)
        pygame.draw.rect(self.screen, INPUT_BOX_BORDER, box, 2, border_radius=6)
        prompt = self.font_input.render("Weight: " + self.weight_input + "|", True, INPUT_BOX_TEXT)
        self.screen.blit(prompt, (bx + 10, by + 13))
        hint = self.font_status.render("Enter to confirm  -  Esc to cancel", True, (120, 130, 145))
        self.screen.blit(hint, (bx + 10, by + box_h + 4))

    def _draw_status(self):
        if self._status_timer <= 0 or not self._status_msg:
            return
        surf = self.font_status.render(self._status_msg, True, self._status_color)
        self.screen.blit(surf, surf.get_rect(bottomright=(self.width - 12, self.height - 10)))
        self._status_timer -= 1

    # -----------------------------------------------------------------------
    # Full draw pass
    # -----------------------------------------------------------------------

    def draw(self):
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        self._draw_panel()
        self._ensure_positions()
        self._draw_edges()
        self._draw_pending_edge_line()
        self._draw_nodes()
        self._draw_weight_input()
        self._draw_status()

    # -----------------------------------------------------------------------
    # Hit-testing
    # -----------------------------------------------------------------------

    def _node_at(self, x, y):
        for node in self.graph.nodes():
            pos = self.graph.get_position(node)
            if pos is None:
                continue
            nx, ny = pos
            if math.hypot(x - nx, y - ny) <= NODE_RADIUS:
                return node
        return None

    # -----------------------------------------------------------------------
    # Weight parsing
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_weight(text):
        text = text.strip()
        if not text or text.count(".") > 1:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    # -----------------------------------------------------------------------
    # Cancel / reset
    # -----------------------------------------------------------------------

    def _cancel_action(self):
        self.edge_start   = None
        self.pending_edge = None
        self.input_mode   = False
        self.weight_input = ""

    # -----------------------------------------------------------------------
    # Event dispatch
    # -----------------------------------------------------------------------

    def handle_events(self, dt: float):
        self._ensure_positions()
        mx, my = pygame.mouse.get_pos()

        # Update hover only in edit mode
        if self._mode == "edit" and not self.input_mode:
            self.hover_node = self._node_at(mx, my)
        else:
            self.hover_node = None

        # Advance playback timer
        if self._mode == "algo" and self._algo_player:
            self._algo_player.advance_time(dt)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):   # scroll wheel
                    continue
                if event.button == 2:         # middle click
                    continue
                if event.button == 3:         # right click
                    if self._mode == "algo":
                        pass   # right-click does nothing in algo mode
                    else:
                        self._cancel_action()
                        if self._mode in ("pick_start", "pick_end"):
                            self._reset_to_edit()
                        self._set_status("Selection cleared.")
                    continue
                if event.button != 1:
                    continue
                if mx < PANEL_WIDTH:
                    continue

                self._handle_left_click(mx, my)

    def _handle_keydown(self, event):
        key = event.key

        # --- Global ---
        if key == pygame.K_ESCAPE:
            if self._mode in ("algo", "pick_start", "pick_end"):
                self._reset_to_edit()
            else:
                self._cancel_action()
                self._set_status("Action cancelled.")
            return

        # --- Weight input (edit mode) ---
        if self._mode == "edit" and self.input_mode:
            self._handle_weight_keydown(event)
            return

        # --- Algo mode playback ---
        if self._mode == "algo" and self._algo_player:
            p = self._algo_player
            if key == pygame.K_SPACE:
                p.playing = not p.playing
            elif key == pygame.K_RIGHT:
                p.step_forward()
                p.playing = False
            elif key == pygame.K_LEFT:
                p.step_back()
                p.playing = False
            elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                p.speed_up()
                self._set_status(f"Speed: {p.speed}x")
            elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                p.slow_down()
                self._set_status(f"Speed: {p.speed}x")
            elif key == pygame.K_r:
                self._reset_to_edit()
            return

        # --- Edit mode hotkeys (only when not in weight input) ---
        if self._mode == "edit" and not self.input_mode:
            if key == pygame.K_b:
                self._start_pick("bfs")
            elif key == pygame.K_d:
                self._start_pick("dfs")
            elif key == pygame.K_k:
                self._start_pick("dijkstra")
            elif key == pygame.K_r:
                self._reset_to_edit()

        # Pick mode also accepts algo hotkeys to switch algo
        if self._mode in ("pick_start", "pick_end"):
            if key == pygame.K_b:
                self._start_pick("bfs")
            elif key == pygame.K_d:
                self._start_pick("dfs")
            elif key == pygame.K_k:
                self._start_pick("dijkstra")

    def _handle_left_click(self, x, y):
        clicked = self._node_at(x, y)

        # --- Pick mode ---
        if self._mode == "pick_start":
            if clicked is None:
                self._set_status("Click a node to select start.", duration=120)
                return
            self._pick_start = clicked
            if self._pending_algo == "dijkstra":
                self._mode = "pick_end"
                self._set_status(
                    f"Start='{clicked}'. Now click an END node.", duration=999
                )
            else:
                self._launch_algo(clicked)
            return

        if self._mode == "pick_end":
            if clicked is None:
                self._set_status("Click a node to select end.", duration=120)
                return
            if clicked == self._pick_start:
                self._set_status("End node must differ from start.", ok=False, duration=150)
                return
            self._launch_algo(self._pick_start, clicked)
            return

        # --- Algo mode: clicks do nothing on canvas ---
        if self._mode == "algo":
            return

        # --- Edit mode ---
        if self.input_mode:
            return

        if clicked:
            self._handle_node_click(clicked)
        else:
            self._handle_empty_click(x, y)

    # -----------------------------------------------------------------------
    # Edit mode helpers
    # -----------------------------------------------------------------------

    def _handle_weight_keydown(self, event):
        if event.key == pygame.K_RETURN:
            weight = self._parse_weight(self.weight_input)
            if weight is None:
                self._set_status("Invalid weight - enter a positive number.", ok=False, duration=180)
                return
            try:
                validate_weight(weight)
            except ValueError as exc:
                self._set_status(str(exc), ok=False, duration=200)
                return

            u, v = self.pending_edge
            if self.graph.has_edge(u, v):
                self._set_status("Edge " + u + " - " + v + " already exists.", ok=False)
                self._cancel_action()
                return
            try:
                self.graph.add_edge(u, v, weight)
            except ValueError as exc:
                self._set_status(str(exc), ok=False, duration=200)
                self._cancel_action()
                return
            self._set_status("Edge " + u + " - " + v + "  (weight " + str(weight) + ") added.")
            self._cancel_action()

        elif event.key == pygame.K_BACKSPACE:
            self.weight_input = self.weight_input[:-1]

        elif event.key == pygame.K_ESCAPE:
            self._cancel_action()
            self._set_status("Edge creation cancelled.")

        else:
            ch = event.unicode
            if ch.isdigit():
                self.weight_input += ch
            elif ch == "." and "." not in self.weight_input:
                self.weight_input += ch

    def _handle_node_click(self, node):
        if self.edge_start is None:
            self.edge_start = node
            self._set_status("Node '" + node + "' selected - click target node.")
        elif node == self.edge_start:
            self.edge_start = None
            self._set_status("Selection cleared.")
        else:
            self.pending_edge = (self.edge_start, node)
            self.input_mode   = True
            self.weight_input = ""
            self._set_status("Enter weight for " + self.edge_start + " - " + node)

    def _handle_empty_click(self, x, y):
        if self.edge_start is not None:
            self._cancel_action()
            self._set_status("Edge creation cancelled - click a node to start again.")
            return
        name = "N" + str(self._node_counter)
        self._node_counter += 1
        while self.graph.has_node(name):
            name = "N" + str(self._node_counter)
            self._node_counter += 1
        try:
            self.graph.add_node(name)
        except ValueError as exc:
            self._set_status(str(exc), ok=False)
            return
        self.graph.set_position(name, x, y)
        self._set_status("Node '" + name + "' added.")

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0   # seconds since last frame
            self.handle_events(dt)
            self.draw()
            pygame.display.flip()

        pygame.quit()