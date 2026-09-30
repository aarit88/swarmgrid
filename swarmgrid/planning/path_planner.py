"""
Path Planner (Box 4)

A* for a single robot's ideal path; Cooperative A* variant considers other
robots' reserved space-time cells (from Box 5's reservation_table) so paths
are time-aware, not just space-aware.

This file ships with a working grid A* (that part doesn't depend on ROS
messages and you can unit-test it directly) plus a thin ROS wrapper stub.

TODO tonight:
  - Load your actual warehouse grid (shelves = obstacles) instead of the
    placeholder open grid below.
  - Wire cooperative_astar to query reservation_table (Box 5) once that
    node exists — right now it just calls plain astar.
  - "If path infeasible -> local replanning / fallback A*" per your
    flowchart: catch the None-path case and retry with relaxed constraints.
"""

import heapq
from typing import List, Optional, Tuple

import rclpy
from rclpy.node import Node

Point = Tuple[int, int]


def astar(start: Point, goal: Point, obstacles: set, grid_size: Tuple[int, int]) -> Optional[List[Point]]:
    """Standard grid A*, 4-connected. Returns list of (x, y) waypoints or None if infeasible."""

    def heuristic(a: Point, b: Point) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def neighbors(p: Point):
        x, y = p
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_size[0] and 0 <= ny < grid_size[1] and (nx, ny) not in obstacles:
                yield (nx, ny)

    open_set = [(heuristic(start, goal), 0, start)]
    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_set:
        _, g, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        if current in visited:
            continue
        visited.add(current)

        for nxt in neighbors(current):
            tentative_g = g + 1
            if tentative_g < g_score.get(nxt, float('inf')):
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                heapq.heappush(open_set, (tentative_g + heuristic(nxt, goal), tentative_g, nxt))

    return None  # infeasible -> caller should trigger local replanning / fallback


def cooperative_astar(start: Point, goal: Point, obstacles: set, grid_size: Tuple[int, int],
                       reserved_cells: Optional[set] = None) -> Optional[List[Tuple[int, int, int]]]:
    """
    Time-aware A*: state is (x, y, t). reserved_cells is a set of (x, y, t)
    tuples already claimed by other robots (from Box 5 reservation table).

    TODO: this is a stub that currently ignores reserved_cells and just
    stamps a static path with an incrementing timestep. Replace with real
    time-expanded A* search once reservation_table (Box 5) exists.
    """
    reserved_cells = reserved_cells or set()
    static_path = astar(start, goal, obstacles, grid_size)
    if static_path is None:
        return None
    return [(x, y, t) for t, (x, y) in enumerate(static_path)]


class PathPlannerNode(Node):
    """Thin ROS wrapper — expand with service/topic interfaces as you integrate
    with robot_agent (Box 3) and reservation_table (Box 5)."""

    def __init__(self):
        super().__init__('path_planner')
        # TODO: load real warehouse grid dimensions + obstacle set from a map file
        self.grid_size = (20, 20)
        self.obstacles = set()  # populate from shelf/static-obstacle layout
        self.get_logger().info('Path planner ready (placeholder open grid, no obstacles loaded).')


def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
