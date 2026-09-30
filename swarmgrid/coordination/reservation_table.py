"""
Reservation Table (Box 5)

Fast hash-based space-time reservation store: vertex conflicts (two robots
in the same cell at the same time) and edge/swap conflicts (two robots
crossing paths mid-move) both get checked here.

This is deliberately kept as a plain-Python class (no ROS dependency) so
you can unit test it directly and swap the storage backend later if a
single shared node becomes a bottleneck — for now, one instance running
as a ROS node all robots query via service calls is the simplest thing
that works.

TODO tonight:
  - Decide: single shared reservation node (simpler, slight central-ish
    smell) vs each robot keeping its own synced copy via broadcast
    (truer to decentralized, more work). Given your "no central
    controller" success criterion, lean toward broadcast-and-merge if
    time allows; shared node as a fallback if you're short on hours.
"""

from typing import Dict, Optional, Set, Tuple

CellTime = Tuple[int, int, int]  # (x, y, t)


class ReservationTable:
    def __init__(self):
        self._vertex: Dict[CellTime, str] = {}       # (x,y,t) -> robot_id
        self._edges: Dict[Tuple[CellTime, CellTime], str] = {}  # ((x,y,t),(x2,y2,t+1)) -> robot_id

    def is_free(self, cell: CellTime, robot_id: str) -> bool:
        holder = self._vertex.get(cell)
        return holder is None or holder == robot_id

    def check_swap_conflict(self, a_from: CellTime, a_to: CellTime,
                             b_from: CellTime, b_to: CellTime) -> bool:
        """True if two robots would swap positions in one timestep (illegal)."""
        return a_from[:2] == b_to[:2] and a_to[:2] == b_from[:2] and a_from[2] == b_from[2]

    def reserve(self, path: list, robot_id: str) -> bool:
        """
        path: list of (x, y, t) waypoints. Reserves all cells if none conflict;
        returns False (and reserves nothing) if any cell is already taken by
        another robot.
        """
        for cell in path:
            if not self.is_free(cell, robot_id):
                return False
        for cell in path:
            self._vertex[cell] = robot_id
        return True

    def release_robot(self, robot_id: str):
        """Used on task completion, or Box 9 failure -> free everything this robot held."""
        for cell in [c for c, r in self._vertex.items() if r == robot_id]:
            del self._vertex[cell]

    def conflicting_robot(self, cell: CellTime) -> Optional[str]:
        return self._vertex.get(cell)
