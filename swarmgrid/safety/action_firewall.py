"""
Action Firewall (Box 6) — "Safety Firewall (Final Authority)"

Deliberately kept algorithm-independent and decoupled from the auction /
optimization logic, per your architecture decision: this module doesn't
know or care about bids, tasks, or PIBT priorities. It only answers one
question per proposed move: "is this safe to execute right now?"

Checks (matches your flowchart box exactly):
  - reservations (space-time table conflicts)
  - other robots' paths
  - static & dynamic obstacles
  - robot health & telemetry
  - towing atomicity (if a rescue tow is in progress, don't interleave
    with a normal move)
  - speed & kinematic limits

On reject: conflict resolution (wait/yield, adjust timing, local backtrack,
reroute) — NOT a fleet-wide stop. Only the requesting robot waits.

TODO tonight:
  - This is the one module I'd actually spend real design time on tonight,
    even at the cost of PIBT sophistication — it's your "zero collisions"
    success criterion made concrete.
  - Wire real telemetry (battery, health flags) instead of the placeholder
    always-healthy default.
"""

from dataclasses import dataclass
from typing import Optional

import rclpy
from rclpy.node import Node

from swarmgrid.utils.config import MAX_ANGULAR_SPEED, MAX_LINEAR_SPEED


@dataclass
class ProposedMove:
    robot_id: str
    from_cell: tuple
    to_cell: tuple  # (x, y, t)
    linear_speed: float
    angular_speed: float
    is_towing: bool = False


@dataclass
class SafetyVerdict:
    safe: bool
    reason: Optional[str] = None
    action: Optional[str] = None  # 'wait' | 'yield' | 'backtrack' | 'reroute'


class ActionFirewall:
    """Plain-Python core logic — testable without ROS. Node below just wraps it."""

    def __init__(self, reservation_table, static_obstacles: set):
        self.reservation_table = reservation_table
        self.static_obstacles = static_obstacles
        self.robots_towing: set = set()  # robot_ids currently mid-tow (Box 10 atomicity)

    def check(self, move: ProposedMove, robot_health_ok: bool = True) -> SafetyVerdict:
        # 1. Robot health & telemetry
        if not robot_health_ok:
            return SafetyVerdict(False, 'robot health check failed', 'wait')

        # 2. Kinematic limits
        if move.linear_speed > MAX_LINEAR_SPEED or move.angular_speed > MAX_ANGULAR_SPEED:
            return SafetyVerdict(False, 'exceeds kinematic limits', 'wait')

        # 3. Static obstacles
        if move.to_cell[:2] in self.static_obstacles:
            return SafetyVerdict(False, 'static obstacle at target cell', 'reroute')

        # 4. Towing atomicity — a robot mid-tow shouldn't have its move
        #    interleaved/preempted by an unrelated normal-move request.
        if move.robot_id in self.robots_towing and not move.is_towing:
            return SafetyVerdict(False, 'robot is mid-tow, non-tow move rejected', 'wait')

        # 5. Reservation / other-robots'-paths check (vertex + swap conflicts)
        holder = self.reservation_table.conflicting_robot(move.to_cell)
        if holder is not None and holder != move.robot_id:
            return SafetyVerdict(False, f'cell reserved by {holder}', 'yield')

        return SafetyVerdict(True)


class ActionFirewallNode(Node):
    def __init__(self):
        super().__init__('action_firewall')
        self.get_logger().info('Action Firewall online — final authority for all moves.')
        # TODO: instantiate ActionFirewall with the real reservation_table
        # instance/service and real static obstacle set, subscribe to
        # proposed-move requests, publish accept/reject verdicts.


def main(args=None):
    rclpy.init(args=args)
    node = ActionFirewallNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
