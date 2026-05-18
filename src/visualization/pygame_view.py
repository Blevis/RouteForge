"""
src/visualization/pygame_view.py
---------------------------------
RouteForge - Interactive Graph Visualizer (pygame)

Two modes
---------
  EDIT mode   - build the graph interactively
  ALGO mode   - step through BFS / DFS / Dijkstra / Prim / Kruskal

Edit controls
-------------
  Left-click   empty space     -> Add node
  Left-click   node            -> Select as edge start
  Left-click   second node     -> Begin edge weight entry
  Right-click  node            -> Remove node
  Right-click  edge            -> Remove edge
  Right-click  empty space     -> Cancel current selection
  Escape                       -> Cancel any in-progress action
  Backspace    (weight input)  -> Delete last character
  Enter        (weight input)  -> Confirm edge with typed weight
  Scroll wheel                 -> Ignored

Algorithm controls
------------------
  B  -> BFS      D  -> DFS      K  -> Dijkstra
  P  -> Prim     U  -> Kruskal
  Space -> Play/Pause   Arrows -> Step   +/- -> Speed   R -> Reset
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
from src.algorithms.kruskal import DisjointSet


# ---------------------------------------------------------------------------
# AMBER/EMBER TERMINAL PALETTE
# ---------------------------------------------------------------------------
# Background layers
BG_COLOR          = ( 11,  12,  14)   # near-black, warm tint
GRID_COLOR        = ( 24,  23,  18)   # very dark amber grid dots
PANEL_BG_COLOR    = ( 14,  13,  11)   # panel slightly warmer than canvas
PANEL_BORDER      = ( 60,  50,  25)   # amber panel edge

# Amber accents
AMBER             = (220, 160,  40)   # primary accent - warm amber
AMBER_DIM         = (120,  85,  18)   # dimmed amber for secondary text
AMBER_BRIGHT      = (255, 200,  70)   # highlight amber
COPPER            = (185, 110,  45)   # copper - structural elements

# Node states
NODE_DEFAULT_FILL = ( 22,  26,  32)   # very dark fill, almost black
NODE_DEFAULT_RING = ( 70,  90, 120)   # slate-blue ring - cool contrast to amber
NODE_SELECTED_FILL= ( 18,  36,  22)   # dark green tint
NODE_SELECTED_RING= ( 55, 180,  80)   # green ring
NODE_HOVER_RING   = (100, 140, 200)   # brighter blue ring
NODE_TEXT_COLOR   = (210, 210, 200)   # warm off-white label

# Edge colours
EDGE_DEFAULT      = ( 48,  52,  58)   # dark slate edge
EDGE_PENDING      = (220, 160,  40)   # amber preview line
WEIGHT_BG         = ( 18,  17,  14)   # weight badge background
WEIGHT_TEXT       = (180, 140,  35)   # dimmed amber weight

# Algorithm state colours
ALGO_VISITED_FILL = ( 12,  35,  30)   # dark teal fill
ALGO_VISITED_RING = ( 30, 140, 110)   # teal ring
ALGO_FRONTIER_FILL= ( 38,  28,   8)   # dark amber fill
ALGO_FRONTIER_RING= (200, 130,  25)   # amber ring
ALGO_ACTIVE_FILL  = ( 42,  42,  38)   # near-white fill tint
ALGO_ACTIVE_RING  = (240, 235, 200)   # bright warm white ring
ALGO_EDGE_USED    = ( 30, 140, 110)   # teal traversed edge
ALGO_EDGE_ACTIVE  = (240, 235, 200)   # bright white active edge
ALGO_PATH_FILL    = ( 40,  32,   8)   # gold tint fill
ALGO_PATH_RING    = (230, 190,  50)   # gold ring
ALGO_PATH_EDGE    = (220, 175,  40)   # gold path edge
ALGO_MST_EDGE     = ( 55, 180, 100)   # green MST edge
ALGO_REJECT_EDGE  = (160,  35,  35)   # red rejected edge
DIST_LABEL_COLOR  = (200, 165,  40)   # amber distance labels

# Pick highlights
PICK_START_RING   = ( 55, 200,  90)
PICK_END_RING     = (200,  60,  60)

# Status
STATUS_OK         = ( 60, 200, 100)
STATUS_ERR        = (210,  60,  60)

# UI text
UI_LABEL          = (130, 105,  45)   # amber-dim section labels
UI_VALUE          = (175, 160, 130)   # warm grey values
UI_DIM            = ( 70,  65,  50)   # very dim dividers/hints


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
NODE_RADIUS        = 20
PANEL_WIDTH        = 250
LAYOUT_RADIUS      = 235
EDGE_HIT_THRESHOLD = 10
SPEED_LEVELS       = [0.5, 1, 2, 4, 8]

# Corner cut size for hexagonal node feel (drawn as polygon)
HEX_CUT = 6


# ---------------------------------------------------------------------------
# AlgoStep
# ---------------------------------------------------------------------------

@dataclass
class AlgoStep:
    visited      : Set[str]                 = field(default_factory=set)
    frontier     : Set[str]                 = field(default_factory=set)
    active_node  : Optional[str]            = None
    active_edges : Set[Tuple[str,str]]      = field(default_factory=set)
    active_edge  : Optional[Tuple[str,str]] = None
    dist_labels  : Dict[str, str]           = field(default_factory=dict)
    path_nodes   : Set[str]                 = field(default_factory=set)
    path_edges   : Set[Tuple[str,str]]      = field(default_factory=set)
    mst_edges    : Set[Tuple[str,str]]      = field(default_factory=set)
    rejected_edge: Optional[Tuple[str,str]] = None
    total_weight : float                    = 0.0
    description  : str                      = ""


# ---------------------------------------------------------------------------
# Step generators
# ---------------------------------------------------------------------------

def _bfs_steps(graph: Graph, start: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    visited: Set[str] = {start}
    queue: deque = deque([start])
    active_edges: Set[Tuple[str,str]] = set()

    steps.append(AlgoStep(visited=set(), frontier={start}, active_node=start,
                          description=f"Init: enqueue '{start}'"))

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
                    visited=set(current_visited), frontier=set(queue),
                    active_node=node, active_edges=set(active_edges), active_edge=edge,
                    description=f"'{node}' -> discover '{neighbor}'"))
        steps.append(AlgoStep(
            visited=set(visited) - set(queue), frontier=set(queue),
            active_node=node, active_edges=set(active_edges),
            description=f"'{node}' settled"))
    return steps


def _dfs_steps(graph: Graph, start: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    visited: Set[str] = set()
    stack: List[str] = [start]
    active_edges: Set[Tuple[str,str]] = set()

    steps.append(AlgoStep(visited=set(), frontier={start}, active_node=start,
                          description=f"Init: push '{start}'"))

    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        frontier = set(stack) - visited
        steps.append(AlgoStep(visited=set(visited), frontier=frontier,
                               active_node=node, active_edges=set(active_edges),
                               description=f"Visit '{node}'"))
        for neighbor, _ in sorted(graph.neighbors(node), key=lambda x: x[0], reverse=True):
            if neighbor not in visited:
                stack.append(neighbor)
                edge = (min(node, neighbor), max(node, neighbor))
                active_edges.add(edge)
                steps.append(AlgoStep(
                    visited=set(visited), frontier=set(stack) - visited,
                    active_node=node, active_edges=set(active_edges), active_edge=edge,
                    description=f"'{node}' -> push '{neighbor}'"))
    return steps


def _dijkstra_steps(graph: Graph, start: str, end: str) -> List[AlgoStep]:
    steps: List[AlgoStep] = []
    distances: Dict[str, float] = {n: float("inf") for n in graph.nodes()}
    previous: Dict[str, Optional[str]] = {n: None for n in graph.nodes()}
    distances[start] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, start)]
    visited: Set[str] = set()
    active_edges: Set[Tuple[str,str]] = set()

    def lbl(n):
        d = distances[n]
        return "inf" if d == float("inf") else str(int(d) if d == int(d) else round(d, 1))

    steps.append(AlgoStep(visited=set(), frontier={start}, active_node=start,
                           dist_labels={n: lbl(n) for n in graph.nodes()},
                           description=f"Init '{start}' d=0"))

    while pq:
        dist, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        steps.append(AlgoStep(visited=set(visited),
                               frontier={n for _, n in pq} - visited,
                               active_node=node, active_edges=set(active_edges),
                               dist_labels={n: lbl(n) for n in graph.nodes()},
                               description=f"Expand '{node}' d={lbl(node)}"))
        for neighbor, weight in graph.neighbors(node):
            nd = dist + weight
            if nd < distances[neighbor]:
                distances[neighbor] = nd
                previous[neighbor] = node
                heapq.heappush(pq, (nd, neighbor))
                edge = (min(node, neighbor), max(node, neighbor))
                active_edges.add(edge)
                steps.append(AlgoStep(
                    visited=set(visited), frontier={n for _, n in pq} - visited,
                    active_node=node, active_edges=set(active_edges), active_edge=edge,
                    dist_labels={n: lbl(n) for n in graph.nodes()},
                    description=f"Relax -> '{neighbor}' = {lbl(neighbor)}"))

    path_nodes: Set[str] = set()
    path_edges: Set[Tuple[str,str]] = set()
    cur = end
    while cur is not None:
        path_nodes.add(cur)
        prev = previous.get(cur)
        if prev:
            path_edges.add((min(prev, cur), max(prev, cur)))
        cur = prev
    total = distances.get(end, float("inf"))
    ts = "unreachable" if total == float("inf") else str(round(total, 2))
    steps.append(AlgoStep(visited=set(visited), active_edges=set(active_edges),
                           dist_labels={n: lbl(n) for n in graph.nodes()},
                           path_nodes=path_nodes, path_edges=path_edges,
                           description=f"Done. Cost={ts}"))
    return steps


def _prim_steps(graph: Graph, start: str) -> List[AlgoStep]:
    if not graph.has_node(start):
        raise KeyError(f"Node '{start}' not found.")
    steps: List[AlgoStep] = []
    visited: Set[str] = {start}
    mst_edge_set: Set[Tuple[str,str]] = set()
    total = 0.0
    pq: List[Tuple[float, str, str]] = []
    for nb, w in graph.neighbors(start):
        heapq.heappush(pq, (w, start, nb))

    def frontier():
        return {n for _, _, n in pq if n not in visited}

    steps.append(AlgoStep(visited={start}, frontier=frontier(), active_node=start,
                           description=f"Init Prim at '{start}'"))

    while pq and len(visited) < graph.order():
        w, u, v = heapq.heappop(pq)
        edge = (min(u, v), max(u, v))
        if v in visited:
            steps.append(AlgoStep(visited=set(visited), frontier=frontier(),
                                   active_edge=edge, rejected_edge=edge,
                                   mst_edges=set(mst_edge_set), total_weight=total,
                                   description=f"Skip {u}-{v} (stale)"))
            continue
        visited.add(v)
        mst_edge_set.add(edge)
        total += w
        for nb, nw in graph.neighbors(v):
            if nb not in visited:
                heapq.heappush(pq, (nw, v, nb))
        steps.append(AlgoStep(visited=set(visited), frontier=frontier(),
                               active_node=v, active_edge=edge,
                               mst_edges=set(mst_edge_set), total_weight=total,
                               description=f"Add {u}-{v} w={w}  total={total}"))

    done = "MST complete" if len(mst_edge_set) >= graph.order() - 1 else "Partial MST (disconnected)"
    steps.append(AlgoStep(visited=set(visited), mst_edges=set(mst_edge_set),
                           total_weight=total, description=f"{done}. W={total}"))
    return steps


def _kruskal_steps(graph: Graph) -> List[AlgoStep]:
    nodes = graph.nodes()
    if not nodes:
        return [AlgoStep(description="Graph is empty.")]
    ds = DisjointSet(nodes)
    edges = sorted(graph.edges(), key=lambda e: e.weight)
    mst_edge_set: Set[Tuple[str,str]] = set()
    total = 0.0
    steps: List[AlgoStep] = []
    for edge in edges:
        key = (min(edge.u, edge.v), max(edge.u, edge.v))
        steps.append(AlgoStep(active_edge=key, mst_edges=set(mst_edge_set),
                               total_weight=total,
                               description=f"Consider {edge.u}-{edge.v} w={edge.weight}"))
        if ds.union(edge.u, edge.v):
            mst_edge_set.add(key)
            total += edge.weight
            steps.append(AlgoStep(active_edge=key, mst_edges=set(mst_edge_set),
                                   total_weight=total,
                                   description=f"Accept {edge.u}-{edge.v}  total={total}"))
            if len(mst_edge_set) == len(nodes) - 1:
                break
        else:
            steps.append(AlgoStep(rejected_edge=key, mst_edges=set(mst_edge_set),
                                   total_weight=total,
                                   description=f"Reject {edge.u}-{edge.v} (cycle)"))
    steps.append(AlgoStep(mst_edges=set(mst_edge_set), total_weight=total,
                           description=f"MST complete. W={total}"))
    return steps


def _point_segment_dist(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    lsq = dx*dx + dy*dy
    if lsq == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy) / lsq))
    return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))


# ---------------------------------------------------------------------------
# AlgoPlayer
# ---------------------------------------------------------------------------

@dataclass
class AlgoPlayer:
    algo_name : str
    steps     : List[AlgoStep]
    index     : int   = 0
    playing   : bool  = False
    speed_idx : int   = 1
    _tick     : float = 0.0

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

    def step_forward(self):
        if self.index < len(self.steps) - 1:
            self.index += 1

    def step_back(self):
        if self.index > 0:
            self.index -= 1

    def speed_up(self):
        self.speed_idx = min(self.speed_idx + 1, len(SPEED_LEVELS) - 1)

    def slow_down(self):
        self.speed_idx = max(self.speed_idx - 1, 0)


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def _draw_cut_circle(surface, fill_color, ring_color, cx, cy, radius, ring_width=2):
    """
    Draw a circle with a distinctive two-tone ring.
    Outer ring uses ring_color, inner fill uses fill_color.
    A thin bright hairline sits between them for a technical/machined look.
    """
    # Outer ring
    pygame.draw.circle(surface, ring_color, (cx, cy), radius)
    # Hairline separator (1px brighter ring)
    pygame.draw.circle(surface, _lerp_color(ring_color, (255,255,255), 0.3),
                       (cx, cy), radius - ring_width + 1, 1)
    # Fill
    pygame.draw.circle(surface, fill_color, (cx, cy), radius - ring_width)


def _lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _draw_panel_section(surface, font, x, y, label):
    """Draw a section label with flanking lines — circuit-trace style."""
    lbl = font.render(label, True, UI_LABEL)
    lw  = lbl.get_width()
    line_y = y + lbl.get_height() // 2
    # Left trace
    pygame.draw.line(surface, UI_DIM, (x, line_y), (x + 8, line_y), 1)
    surface.blit(lbl, (x + 12, y))
    # Right trace
    pygame.draw.line(surface, UI_DIM, (x + 14 + lw, line_y),
                     (x + 14 + lw + 8, line_y), 1)
    return y + lbl.get_height() + 6


def _draw_key_badge(surface, font, x, y, key_str, desc_str, key_color, desc_color):
    """Render  [KEY]  description  with a pill around the key."""
    key = font.render(key_str, True, key_color)
    desc = font.render(desc_str, True, desc_color)
    kw, kh = key.get_width(), key.get_height()
    pad = 4
    badge = pygame.Rect(x, y, kw + pad * 2, kh + pad)
    pygame.draw.rect(surface, (30, 25, 12), badge, border_radius=3)
    pygame.draw.rect(surface, UI_DIM, badge, 1, border_radius=3)
    surface.blit(key, (x + pad, y + pad // 2))
    surface.blit(desc, (x + badge.width + 6, y + pad // 2))
    return y + kh + pad + 5


# ---------------------------------------------------------------------------
# GraphVisualizer
# ---------------------------------------------------------------------------

class GraphVisualizer:

    def __init__(self, graph: Graph):
        self.graph = graph

        pygame.init()

        self.width, self.height = 1150, 740
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ROUTEFORGE  //  Graph Visualizer")

        self.clock   = pygame.time.Clock()
        self.running = True

        # Fonts — monospace heavy for the terminal feel
        self.font_title  = pygame.font.SysFont("Courier New",  15, bold=True)
        self.font_node   = pygame.font.SysFont("Courier New",  13, bold=True)
        self.font_label  = pygame.font.SysFont("Courier New",  11, bold=True)
        self.font_ui     = pygame.font.SysFont("Courier New",  12)
        self.font_status = pygame.font.SysFont("Courier New",  11)
        self.font_dist   = pygame.font.SysFont("Courier New",  10, bold=True)
        self.font_section= pygame.font.SysFont("Courier New",  10, bold=True)

        # Edit state
        self.edge_start    = None
        self.pending_edge  = None
        self.hover_node    = None
        self.input_mode    = False
        self.weight_input  = ""
        self._node_counter = 0

        # Status
        self._status_msg   = ""
        self._status_color = STATUS_OK
        self._status_timer = 0

        # Algorithm state
        self._mode         : str                  = "edit"
        self._algo_player  : Optional[AlgoPlayer] = None
        self._pending_algo : str                  = ""
        self._pick_start   : Optional[str]        = None

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _set_status(self, msg, ok=True, duration=150):
        self._status_msg   = msg
        self._status_color = STATUS_OK if ok else STATUS_ERR
        self._status_timer = duration

    def _ensure_positions(self):
        nodes = self.graph.nodes()
        if not nodes:
            return
        cx = (self.width + PANEL_WIDTH) // 2
        cy = self.height // 2
        total = len(nodes)
        for node in nodes:
            if node not in self.graph.positions:
                idx   = list(nodes).index(node)
                angle = (2 * math.pi * idx) / max(total, 1) - math.pi / 2
                x = cx + int(LAYOUT_RADIUS * math.cos(angle))
                y = cy + int(LAYOUT_RADIUS * math.sin(angle))
                self.graph.set_position(node, x, y)

    # -----------------------------------------------------------------------
    # Algorithm launchers
    # -----------------------------------------------------------------------

    def _start_pick(self, algo: str):
        if not self.graph.nodes():
            self._set_status("Graph is empty.", ok=False)
            return
        self._cancel_action()
        self._pending_algo = algo
        self._pick_start   = None
        self._mode         = "pick_start"
        labels = {"bfs": "BFS", "dfs": "DFS", "dijkstra": "Dijkstra", "prim": "Prim"}
        self._set_status(f"{labels[algo]}: select START node", duration=999)

    def _launch_kruskal(self):
        if not self.graph.nodes():
            self._set_status("Graph is empty.", ok=False)
            return
        self._cancel_action()
        self._pending_algo = "kruskal"
        steps = _kruskal_steps(self.graph)
        self._algo_player  = AlgoPlayer(algo_name="Kruskal MST", steps=steps)
        self._mode         = "algo"
        self._set_status("Kruskal MST  //  Space=play  R=reset", duration=300)

    def _launch_algo(self, start: str, end: Optional[str] = None):
        algo = self._pending_algo
        try:
            if algo == "bfs":
                steps = _bfs_steps(self.graph, start)
                name  = f"BFS  //  '{start}'"
            elif algo == "dfs":
                steps = _dfs_steps(self.graph, start)
                name  = f"DFS  //  '{start}'"
            elif algo == "prim":
                steps = _prim_steps(self.graph, start)
                name  = f"Prim MST  //  '{start}'"
            else:
                steps = _dijkstra_steps(self.graph, start, end)
                name  = f"Dijkstra  //  '{start}'->'{end}'"
        except KeyError as exc:
            self._set_status(str(exc), ok=False)
            self._mode = "edit"
            return
        self._algo_player = AlgoPlayer(algo_name=name, steps=steps)
        self._mode        = "algo"
        self._set_status(f"{name}  //  Space=play  R=reset", duration=300)

    def _reset_to_edit(self):
        self._mode         = "edit"
        self._algo_player  = None
        self._pending_algo = ""
        self._pick_start   = None
        self._cancel_action()
        self._set_status("Edit mode.")

    # -----------------------------------------------------------------------
    # Panel drawing
    # -----------------------------------------------------------------------

    def _draw_panel_bg(self):
        """Panel background with right-side border accent."""
        panel_rect = pygame.Rect(0, 0, PANEL_WIDTH, self.height)
        pygame.draw.rect(self.screen, PANEL_BG_COLOR, panel_rect)

        # Right border — double line with gap
        pygame.draw.line(self.screen, PANEL_BORDER,
                         (PANEL_WIDTH - 3, 0), (PANEL_WIDTH - 3, self.height), 1)
        pygame.draw.line(self.screen, UI_DIM,
                         (PANEL_WIDTH - 1, 0), (PANEL_WIDTH - 1, self.height), 1)

    def _draw_panel_header(self):
        """Top logo block."""
        # Amber top bar
        pygame.draw.rect(self.screen, AMBER, (0, 0, PANEL_WIDTH - 3, 3))

        title1 = self.font_title.render("ROUTEFORGE", True, AMBER_BRIGHT)
        title2 = self.font_section.render("GRAPH VISUALIZER  v1.0", True, AMBER_DIM)
        self.screen.blit(title1, (16, 12))
        self.screen.blit(title2, (16, 32))

        pygame.draw.line(self.screen, PANEL_BORDER, (12, 52), (PANEL_WIDTH - 16, 52), 1)

    def _draw_panel_footer(self):
        """Node/edge counter at the bottom."""
        y = self.height - 54
        pygame.draw.line(self.screen, PANEL_BORDER, (12, y), (PANEL_WIDTH - 16, y), 1)
        y += 8

        stats = [
            ("NODES", str(self.graph.order())),
            ("EDGES", str(self.graph.size())),
        ]
        for label, val in stats:
            lbl  = self.font_section.render(label, True, UI_LABEL)
            vtxt = self.font_title.render(val, True, AMBER)
            self.screen.blit(lbl,  (16, y))
            self.screen.blit(vtxt, (PANEL_WIDTH - 16 - vtxt.get_width(), y))
            y += 18

    def _draw_panel_edit(self):
        y = 62

        # ── GRAPH OPS ───────────────────────────────────────────
        y = _draw_panel_section(self.screen, self.font_section, 14, y, "GRAPH OPS")
        ops = [
            ("LMB",    "add node / start edge"),
            ("ENTER",  "confirm weight"),
            ("RMB",    "delete node or edge"),
            ("ESC",    "cancel"),
        ]
        for key, desc in ops:
            y = _draw_key_badge(self.screen, self.font_ui, 16, y,
                                key, desc, AMBER, UI_VALUE)
        y += 4

        # ── ALGORITHMS ──────────────────────────────────────────
        y = _draw_panel_section(self.screen, self.font_section, 14, y, "ALGORITHMS")
        algos = [
            ("B", "Breadth-First Search"),
            ("D", "Depth-First Search"),
            ("K", "Dijkstra"),
            ("P", "Prim MST"),
            ("U", "Kruskal MST"),
        ]
        for key, desc in algos:
            y = _draw_key_badge(self.screen, self.font_ui, 16, y,
                                key, desc, AMBER_BRIGHT, UI_VALUE)

    def _draw_panel_pick(self):
        y = 62
        labels = {"bfs": "BFS", "dfs": "DFS", "dijkstra": "Dijkstra", "prim": "Prim"}
        algo_label = labels.get(self._pending_algo, "")

        title = self.font_title.render(f"// {algo_label}", True, AMBER_BRIGHT)
        self.screen.blit(title, (16, y))
        y += title.get_height() + 8

        if self._mode == "pick_start":
            prompt, col = "SELECT START NODE", PICK_START_RING
        else:
            prompt, col = "SELECT END NODE", PICK_END_RING

        p = self.font_ui.render(prompt, True, col)
        self.screen.blit(p, (16, y))
        y += p.get_height() + 6

        if self._pick_start:
            s = self.font_ui.render(f"start: {self._pick_start}", True, PICK_START_RING)
            self.screen.blit(s, (16, y))
            y += s.get_height() + 6

        hint = self.font_section.render("[ESC] cancel", True, UI_DIM)
        self.screen.blit(hint, (16, y))

    def _draw_panel_algo(self):
        p = self._algo_player
        if p is None:
            return
        y = 62

        # Algorithm name
        name_surf = self.font_title.render(p.algo_name, True, AMBER_BRIGHT)
        # Clip if too wide
        if name_surf.get_width() > PANEL_WIDTH - 30:
            name_surf = self.font_section.render(p.algo_name, True, AMBER_BRIGHT)
        self.screen.blit(name_surf, (16, y))
        y += name_surf.get_height() + 4

        # Progress bar
        bar_w = PANEL_WIDTH - 32
        frac  = p.index / max(len(p.steps) - 1, 1)
        pygame.draw.rect(self.screen, (30, 26, 14), (16, y, bar_w, 5), border_radius=2)
        if frac > 0:
            pygame.draw.rect(self.screen, AMBER,
                             (16, y, int(bar_w * frac), 5), border_radius=2)
        y += 10

        step_txt = self.font_section.render(
            f"STEP  {p.index + 1} / {len(p.steps)}", True, UI_LABEL)
        self.screen.blit(step_txt, (16, y))
        y += step_txt.get_height() + 6

        # Description — word-wrap
        desc  = p.current_step.description
        words = desc.split()
        lines, cur = [], ""
        for w in words:
            if len(cur) + len(w) + 1 > 28:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        if cur:
            lines.append(cur)
        for line in lines[:3]:
            l = self.font_ui.render(line, True, UI_VALUE)
            self.screen.blit(l, (16, y))
            y += l.get_height() + 2
        y += 8

        # MST total weight
        step = p.current_step
        if step.total_weight > 0 or step.mst_edges:
            wt = self.font_ui.render(f"MST weight: {step.total_weight}", True, AMBER_DIM)
            self.screen.blit(wt, (16, y))
            y += wt.get_height() + 6

        pygame.draw.line(self.screen, PANEL_BORDER, (12, y), (PANEL_WIDTH - 16, y), 1)
        y += 8

        # Legend
        y = _draw_panel_section(self.screen, self.font_section, 14, y, "LEGEND")
        legend_items = [
            (ALGO_ACTIVE_RING,   NODE_DEFAULT_FILL, "Active"),
            (ALGO_FRONTIER_RING, ALGO_FRONTIER_FILL, "Frontier"),
            (ALGO_VISITED_RING,  ALGO_VISITED_FILL, "Visited"),
        ]
        if "Dijkstra" in p.algo_name:
            legend_items.append((ALGO_PATH_RING, ALGO_PATH_FILL, "Path"))
        if "Prim" in p.algo_name or "Kruskal" in p.algo_name:
            legend_items.append((ALGO_MST_EDGE, NODE_DEFAULT_FILL, "MST edge"))
            legend_items.append((ALGO_REJECT_EDGE, NODE_DEFAULT_FILL, "Rejected"))

        for ring, fill, lbl in legend_items:
            _draw_cut_circle(self.screen, fill, ring, 24, y + 7, 7, 2)
            l = self.font_ui.render(lbl, True, UI_VALUE)
            self.screen.blit(l, (36, y))
            y += 17
        y += 4

        pygame.draw.line(self.screen, PANEL_BORDER, (12, y), (PANEL_WIDTH - 16, y), 1)
        y += 8

        # Playback controls
        y = _draw_panel_section(self.screen, self.font_section, 14, y, "PLAYBACK")
        controls = [
            ("SPC",  "play / pause"),
            ("< >",  "step"),
            ("+ -",  "speed"),
            ("R",    "reset"),
        ]
        for key, desc in controls:
            y = _draw_key_badge(self.screen, self.font_ui, 16, y,
                                key, desc, AMBER, UI_VALUE)

        # State pill
        y += 4
        playing = p.playing
        state   = "PLAYING" if playing else "PAUSED"
        scol    = STATUS_OK if playing else (180, 150, 40)
        spd     = self.font_section.render(f"{state}  //  {p.speed}x", True, scol)
        self.screen.blit(spd, (16, y))

    def _draw_panel(self):
        self._draw_panel_bg()
        self._draw_panel_header()
        self._draw_panel_footer()

        if self._mode == "edit":
            self._draw_panel_edit()
        elif self._mode in ("pick_start", "pick_end"):
            self._draw_panel_pick()
        else:
            self._draw_panel_algo()

    # -----------------------------------------------------------------------
    # Canvas drawing
    # -----------------------------------------------------------------------

    def _draw_grid(self):
        """Scanline-style dot grid — horizontal spacing tighter than vertical."""
        xs = 38
        ys = 38
        for gx in range(PANEL_WIDTH + xs, self.width, xs):
            for gy in range(ys, self.height, ys):
                pygame.draw.circle(self.screen, GRID_COLOR, (gx, gy), 1)

    def _edge_color_thickness(self, edge, step):
        if step is None:
            return EDGE_DEFAULT, 2
        if edge in step.path_edges:
            return ALGO_PATH_EDGE, 4
        if step.rejected_edge and edge == step.rejected_edge:
            return ALGO_REJECT_EDGE, 3
        if edge in step.mst_edges:
            return ALGO_MST_EDGE, 3
        if edge == step.active_edge:
            return ALGO_EDGE_ACTIVE, 3
        if edge in step.active_edges:
            return ALGO_EDGE_USED, 2
        return EDGE_DEFAULT, 1

    def _draw_edges(self):
        step = self._algo_player.current_step if self._algo_player else None

        for u in self.graph.nodes():
            for v, w in self.graph.neighbors(u):
                if u >= v:
                    continue
                p1 = self.graph.get_position(u)
                p2 = self.graph.get_position(v)
                if p1 is None or p2 is None:
                    continue
                x1, y1 = p1
                x2, y2 = p2
                edge = (min(u, v), max(u, v))
                color, thickness = self._edge_color_thickness(edge, step)

                # Draw the edge
                pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), thickness)

                # Tiny end-caps for a finished-look
                if thickness >= 2:
                    pygame.draw.circle(self.screen, color, (x1, y1), thickness // 2)
                    pygame.draw.circle(self.screen, color, (x2, y2), thickness // 2)

                # Weight badge
                mx, my = (x1 + x2) // 2, (y1 + y2) // 2
                lbl = self.font_dist.render(str(w), True, WEIGHT_TEXT)
                rect = lbl.get_rect(center=(mx, my))
                bg   = rect.inflate(8, 4)
                pygame.draw.rect(self.screen, WEIGHT_BG, bg, border_radius=3)
                pygame.draw.rect(self.screen, UI_DIM, bg, 1, border_radius=3)
                self.screen.blit(lbl, rect)

    def _draw_pending_edge_line(self):
        if self._mode != "edit" or self.edge_start is None or self.input_mode:
            return
        p1 = self.graph.get_position(self.edge_start)
        if p1 is None:
            return
        mx, my = pygame.mouse.get_pos()
        # Dashed line approximation
        x1, y1 = p1
        dx, dy = mx - x1, my - y1
        length = math.hypot(dx, dy)
        if length < 1:
            return
        steps = int(length / 12)
        for i in range(steps):
            t0 = i / max(steps, 1)
            t1 = (i + 0.5) / max(steps, 1)
            sx, sy = int(x1 + dx * t0), int(y1 + dy * t0)
            ex, ey = int(x1 + dx * t1), int(y1 + dy * t1)
            pygame.draw.line(self.screen, EDGE_PENDING, (sx, sy), (ex, ey), 2)

    def _node_ring_fill(self, node: str):
        step = self._algo_player.current_step if self._algo_player else None

        # Pick mode
        if self._mode == "pick_start" and node == self._pick_start:
            return NODE_SELECTED_FILL, PICK_START_RING
        if self._mode == "pick_end" and node == self._pick_start:
            return NODE_SELECTED_FILL, PICK_START_RING

        if step is not None:
            if node in step.path_nodes:
                return ALGO_PATH_FILL, ALGO_PATH_RING
            if node == step.active_node:
                return ALGO_ACTIVE_FILL, ALGO_ACTIVE_RING
            if node in step.visited:
                return ALGO_VISITED_FILL, ALGO_VISITED_RING
            if node in step.frontier:
                return ALGO_FRONTIER_FILL, ALGO_FRONTIER_RING
            return NODE_DEFAULT_FILL, NODE_DEFAULT_RING

        # Edit mode
        if node == self.edge_start:
            return NODE_SELECTED_FILL, NODE_SELECTED_RING
        if node == self.hover_node:
            return NODE_DEFAULT_FILL, NODE_HOVER_RING
        return NODE_DEFAULT_FILL, NODE_DEFAULT_RING

    def _draw_nodes(self):
        step = self._algo_player.current_step if self._algo_player else None

        for node in self.graph.nodes():
            pos = self.graph.get_position(node)
            if pos is None:
                continue
            x, y = pos
            fill, ring = self._node_ring_fill(node)

            # Glow halo for active/selected
            is_active = (node == self.edge_start or
                         (step and node == step.active_node) or
                         node == self.hover_node)
            if is_active:
                glow = pygame.Surface((NODE_RADIUS * 6, NODE_RADIUS * 6), pygame.SRCALPHA)
                gc   = (*ring, 28)
                pygame.draw.circle(glow, gc,
                                   (NODE_RADIUS * 3, NODE_RADIUS * 3), NODE_RADIUS + 10)
                self.screen.blit(glow, (x - NODE_RADIUS * 3, y - NODE_RADIUS * 3))

            _draw_cut_circle(self.screen, fill, ring, x, y, NODE_RADIUS, ring_width=2)

            # Node label
            lbl = self.font_node.render(node, True, NODE_TEXT_COLOR)
            self.screen.blit(lbl, lbl.get_rect(center=(x, y)))

            # Dijkstra distance label above node
            if step and step.dist_labels:
                ds = step.dist_labels.get(node, "")
                if ds:
                    dl = self.font_dist.render(ds, True, DIST_LABEL_COLOR)
                    dr = dl.get_rect(center=(x, y - NODE_RADIUS - 9))
                    # tiny pill behind it
                    bg = dr.inflate(6, 3)
                    pygame.draw.rect(self.screen, WEIGHT_BG, bg, border_radius=2)
                    self.screen.blit(dl, dr)

    def _draw_weight_input(self):
        if not self.input_mode or self.pending_edge is None:
            return
        u, v   = self.pending_edge
        p1 = self.graph.get_position(u)
        p2 = self.graph.get_position(v)
        if p1 is None or p2 is None:
            return
        x1, y1 = p1
        x2, y2 = p2
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2

        box_w, box_h = 230, 52
        bx = min(max(mx - box_w // 2, PANEL_WIDTH + 8), self.width  - box_w - 8)
        by = min(max(my - box_h - 20, 8),               self.height - box_h - 36)

        box = pygame.Rect(bx, by, box_w, box_h)

        # Shadow
        shadow = box.inflate(4, 4).move(3, 3)
        shadow_surf = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        self.screen.blit(shadow_surf, shadow.topleft)

        pygame.draw.rect(self.screen, (16, 14, 10), box, border_radius=5)
        pygame.draw.rect(self.screen, AMBER, box, 1, border_radius=5)
        # Top accent bar
        accent = pygame.Rect(bx + 1, by + 1, box_w - 2, 2)
        pygame.draw.rect(self.screen, AMBER_DIM, accent)

        # Label
        edge_lbl = self.font_section.render(f"EDGE  {u} -- {v}", True, AMBER_DIM)
        self.screen.blit(edge_lbl, (bx + 10, by + 8))

        # Input line
        prompt = self.font_title.render(
            "WEIGHT > " + self.weight_input + "_", True, AMBER_BRIGHT)
        self.screen.blit(prompt, (bx + 10, by + 24))

        hint = self.font_section.render("[ENTER] confirm   [ESC] cancel", True, UI_DIM)
        self.screen.blit(hint, (bx + 10, by + box_h + 4))

    def _draw_status(self):
        if self._status_timer <= 0 or not self._status_msg:
            return
        surf = self.font_status.render("> " + self._status_msg, True, self._status_color)
        self.screen.blit(surf, surf.get_rect(bottomright=(self.width - 14, self.height - 10)))
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
            if math.hypot(x - pos[0], y - pos[1]) <= NODE_RADIUS:
                return node
        return None

    def _edge_at(self, x, y) -> Optional[Tuple[str, str]]:
        best, best_d = None, EDGE_HIT_THRESHOLD
        for u in self.graph.nodes():
            for v, _ in self.graph.neighbors(u):
                if u >= v:
                    continue
                p1 = self.graph.get_position(u)
                p2 = self.graph.get_position(v)
                if p1 is None or p2 is None:
                    continue
                d = _point_segment_dist(x, y, p1[0], p1[1], p2[0], p2[1])
                if d < best_d:
                    best_d = d
                    best = (min(u, v), max(u, v))
        return best

    # -----------------------------------------------------------------------
    # Event handling
    # -----------------------------------------------------------------------

    def _handle_right_click(self, mx, my):
        if self._mode == "algo":
            return
        if self.input_mode:
            self._cancel_action()
            self._set_status("Edge creation cancelled.")
            return
        if self._mode in ("pick_start", "pick_end"):
            self._reset_to_edit()
            return
        if self._mode != "edit" or mx < PANEL_WIDTH:
            return

        node = self._node_at(mx, my)
        if node is not None:
            if self.graph.remove_node(node):
                if self.edge_start == node:
                    self.edge_start = None
                self._set_status(f"Node '{node}' removed.")
            return

        edge = self._edge_at(mx, my)
        if edge is not None:
            u, v = edge
            if self.graph.remove_edge(u, v):
                self._set_status(f"Edge {u}-{v} removed.")
            return

        self._cancel_action()
        self._set_status("Selection cleared.")

    @staticmethod
    def _parse_weight(text):
        text = text.strip()
        if not text or text.count(".") > 1:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _cancel_action(self):
        self.edge_start   = None
        self.pending_edge = None
        self.input_mode   = False
        self.weight_input = ""

    def handle_events(self, dt: float):
        self._ensure_positions()
        mx, my = pygame.mouse.get_pos()

        if self._mode == "edit" and not self.input_mode:
            self.hover_node = self._node_at(mx, my)
        else:
            self.hover_node = None

        if self._mode == "algo" and self._algo_player:
            self._algo_player.advance_time(dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (4, 5):
                    continue
                if event.button == 2:
                    continue
                if event.button == 3:
                    self._handle_right_click(mx, my)
                    continue
                if event.button != 1:
                    continue
                if mx < PANEL_WIDTH:
                    continue
                self._handle_left_click(mx, my)

    def _handle_keydown(self, event):
        key = event.key

        if key == pygame.K_ESCAPE:
            if self._mode in ("algo", "pick_start", "pick_end"):
                self._reset_to_edit()
            else:
                self._cancel_action()
                self._set_status("Cancelled.")
            return

        if self._mode == "edit" and self.input_mode:
            self._handle_weight_keydown(event)
            return

        if self._mode == "algo" and self._algo_player:
            p = self._algo_player
            if key == pygame.K_SPACE:
                p.playing = not p.playing
            elif key == pygame.K_RIGHT:
                p.step_forward(); p.playing = False
            elif key == pygame.K_LEFT:
                p.step_back();    p.playing = False
            elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                p.speed_up()
                self._set_status(f"Speed {p.speed}x")
            elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                p.slow_down()
                self._set_status(f"Speed {p.speed}x")
            elif key == pygame.K_r:
                self._reset_to_edit()
            return

        if self._mode in ("edit", "pick_start", "pick_end") and not self.input_mode:
            if key == pygame.K_b:
                self._start_pick("bfs")
            elif key == pygame.K_d:
                self._start_pick("dfs")
            elif key == pygame.K_k:
                self._start_pick("dijkstra")
            elif key == pygame.K_p:
                self._start_pick("prim")
            elif key == pygame.K_u:
                self._launch_kruskal()
            elif key == pygame.K_r:
                self._reset_to_edit()

    def _handle_left_click(self, x, y):
        clicked = self._node_at(x, y)

        if self._mode == "pick_start":
            if clicked is None:
                self._set_status("Click a node.", duration=120)
                return
            self._pick_start = clicked
            if self._pending_algo == "dijkstra":
                self._mode = "pick_end"
                self._set_status(f"Start='{clicked}'. Select END node.", duration=999)
            else:
                self._launch_algo(clicked)
            return

        if self._mode == "pick_end":
            if clicked is None:
                self._set_status("Click a node.", duration=120)
                return
            if clicked == self._pick_start:
                self._set_status("End must differ from start.", ok=False, duration=150)
                return
            self._launch_algo(self._pick_start, clicked)
            return

        if self._mode == "algo":
            return
        if self.input_mode:
            return

        if clicked:
            self._handle_node_click(clicked)
        else:
            self._handle_empty_click(x, y)

    def _handle_weight_keydown(self, event):
        if event.key == pygame.K_RETURN:
            weight = self._parse_weight(self.weight_input)
            if weight is None:
                self._set_status("Invalid weight.", ok=False, duration=180)
                return
            try:
                validate_weight(weight)
            except ValueError as exc:
                self._set_status(str(exc), ok=False, duration=200)
                return
            u, v = self.pending_edge
            if self.graph.has_edge(u, v):
                self._set_status(f"Edge {u}-{v} already exists.", ok=False)
                self._cancel_action()
                return
            try:
                self.graph.add_edge(u, v, weight)
            except ValueError as exc:
                self._set_status(str(exc), ok=False, duration=200)
                self._cancel_action()
                return
            self._set_status(f"Edge {u}-{v} w={weight} added.")
            self._cancel_action()

        elif event.key == pygame.K_BACKSPACE:
            self.weight_input = self.weight_input[:-1]

        elif event.key == pygame.K_ESCAPE:
            self._cancel_action()
            self._set_status("Edge cancelled.")

        else:
            ch = event.unicode
            if ch.isdigit():
                self.weight_input += ch
            elif ch == "." and "." not in self.weight_input:
                self.weight_input += ch

    def _handle_node_click(self, node):
        if self.edge_start is None:
            self.edge_start = node
            self._set_status(f"'{node}' selected. Click target.")
        elif node == self.edge_start:
            self.edge_start = None
            self._set_status("Deselected.")
        else:
            self.pending_edge = (self.edge_start, node)
            self.input_mode   = True
            self.weight_input = ""
            self._set_status(f"Edge {self.edge_start}-{node}: enter weight.")

    def _handle_empty_click(self, x, y):
        if self.edge_start is not None:
            self._cancel_action()
            self._set_status("Edge cancelled.")
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
        self._set_status(f"Node '{name}' added.")

    # -----------------------------------------------------------------------
    # Main loop
    # -----------------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()