"""
PIBT Coordinator (Box 5)

Priority Inheritance with Backtracking: when robot A's next planned move
conflicts with robot B's current position/plan, resolve locally by either
having the lower-priority robot wait, or backtrack and adjust timing,
rather than triggering a global replan.

NOTE (per your fallback plan if time runs short): if PIBT proves too time-
consuming to get fully correct, degrade gracefully to simple wait/yield
conflict resolution first, then layer priority inheritance back in if
hours remain. The stub below is structured so that's an easy downgrade —
`resolve_conflict` is the one function to simplify.

TODO tonight:
  - Implement priority ordering (currently: lower robot_id = higher priority,
    simplest possible deterministic rule — swap for something smarter later
    if needed).
  - Wire into reservation_table for actual space-time checks.
"""

from dataclasses import dataclass
from typing import Optional

import rclpy
from rclpy.node import Node


@dataclass
class MoveRequest:
    robot_id: str
    from_cell: tuple
    to_cell: tuple
    priority: int  # lower = higher priority, e.g. derived from robot_id or task urgency


def higher_priority(a: MoveRequest, b: MoveRequest) -> MoveRequest:
    return a if a.priority <= b.priority else b


def resolve_conflict(a: MoveRequest, b: MoveRequest) -> dict:
    """
    Returns {'winner': robot_id, 'action_for_loser': 'wait' | 'backtrack'}

    Simplified version (safe fallback if PIBT proper runs out of time):
    higher priority always proceeds, lower priority waits one tick.

    Full PIBT extension (do this if time allows): if the loser waiting
    would itself cause a cascading conflict with a third robot, recurse
    and let priority "inherit" down the chain, backtracking the original
    winner's move if no resolution is found. Not implemented yet —
    this is exactly the kind of thing to timebox: if it's not clicking in
    ~30-45 min, ship the simple version and move on to Box 6.
    """
    winner = higher_priority(a, b)
    loser = b if winner is a else a
    return {'winner': winner.robot_id, 'loser': loser.robot_id, 'action_for_loser': 'wait'}


class PibtCoordinatorNode(Node):
    def __init__(self):
        super().__init__('pibt_coordinator')
        self.get_logger().info('PIBT coordinator ready (simple wait/yield fallback active).')
        # TODO: subscribe to per-robot planned-move topics, call resolve_conflict,
        # publish accepted/rejected moves back out.


def main(args=None):
    rclpy.init(args=args)
    node = PibtCoordinatorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
