"""
Rescue Controller (Box 10)

Per your architecture decision: rescue stays a SEPARATE system from the
auction/optimization layer. This module only knows "eligible robots" and
"safe pause points" — it does NOT know about tasks, bids, or parcels
beyond "pick this up and drop it at a safe point."

Sequence (matches flowchart):
  1. Receive rescue mission (highest priority) when a robot is marked FAILED
  2. Navigate to failed robot
  3. Connect / tow failed robot (atomic move — see action_firewall's
     towing-atomicity check)
  4. If the failed robot was carrying a parcel: retrieve it too, drop at
     nearest safe pause point (per your two-atomic-actions decision, since
     payload/towing capacity is undefined in simulation-only scope —
     treat "tow robot" and "retrieve stranded parcel" as separate actions)
  5. Navigate to service/charging station, release failed robot
  6. Service / repair / charge failed robot
  7. Return to fleet (normal operation)

Once R5 drops parcels at a safe pause point, the OPTIMIZATION layer (task
pool via task_manager/robot_agent) picks them back up as fresh tasks —
this module doesn't re-auction anything itself.

TODO tonight:
  - Simplify first pass: assume R5 is always available and never itself
    mid-task when a failure happens (per your "cut list" fallback #2,
    only add the busy_with_task vs rescuing state juggling if time remains).
  - Nearest-safe-pause-point selection is currently "just pick the first
    one" — replace with real distance calc once path_planner exists.
"""

import json
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from swarmgrid.utils.config import RESCUE_CAPABLE_IDS, SAFE_PAUSE_POINTS


class RescueState(Enum):
    IDLE = auto()
    EN_ROUTE_TO_FAILED_ROBOT = auto()
    TOWING = auto()
    RETRIEVING_PARCEL = auto()
    EN_ROUTE_TO_SERVICE = auto()
    RELEASING = auto()


class RescueController(Node):
    def __init__(self):
        super().__init__('rescue_controller')
        self.declare_parameter('robot_id', 'R5')
        self.robot_id = self.get_parameter('robot_id').value
        self.is_rescue_capable = self.robot_id in RESCUE_CAPABLE_IDS
        self.state = RescueState.IDLE
        self.active_target = None  # robot_id currently being rescued

        self.create_subscription(String, '/swarmgrid/robot_failed', self.on_robot_failed, 10)
        self.mission_pub = self.create_publisher(String, '/swarmgrid/rescue_mission', 10)
        self.stranded_parcel_pub = self.create_publisher(String, '/swarmgrid/stranded_parcel', 10)

        if self.is_rescue_capable:
            self.get_logger().info(f'{self.robot_id} online as rescue-capable AMR.')

    def on_robot_failed(self, msg: String):
        if not self.is_rescue_capable or self.state != RescueState.IDLE:
            return  # simplest-first: only act if idle; queueing multiple failures is a later upgrade

        data = json.loads(msg.data)
        target = data['robot_id']
        if target == self.robot_id:
            return

        self.active_target = target
        self.state = RescueState.EN_ROUTE_TO_FAILED_ROBOT

        mission_msg = String()
        mission_msg.data = json.dumps({'assigned_robot': self.robot_id, 'target_robot': target})
        self.mission_pub.publish(mission_msg)
        self.get_logger().warn(f'{self.robot_id}: rescue mission -> {target}')

        # TODO: drive actual navigation here. Placeholder immediately
        # advances state for now so the pipeline is testable end-to-end.
        self._advance_to_towing()

    def _advance_to_towing(self):
        self.state = RescueState.TOWING
        # Per your decision: tow + parcel retrieval are two separate atomic
        # actions, not one combined carry (payload/towing capacity undefined
        # in sim-only scope).
        self._retrieve_stranded_parcel_if_any()

    def _retrieve_stranded_parcel_if_any(self):
        self.state = RescueState.RETRIEVING_PARCEL
        # TODO: query whether self.active_target had an in-progress task/parcel.
        # Placeholder: always assume yes for now, publish to safe pause point.
        drop_point = SAFE_PAUSE_POINTS[0]  # TODO: nearest, not first
        parcel_msg = String()
        parcel_msg.data = json.dumps({
            'from_robot': self.active_target,
            'dropped_at': drop_point,
        })
        self.stranded_parcel_pub.publish(parcel_msg)
        self.get_logger().info(
            f'{self.robot_id}: stranded parcel from {self.active_target} dropped at {drop_point} '
            f'(re-entering optimization layer for re-auction).'
        )
        self._advance_to_service()

    def _advance_to_service(self):
        self.state = RescueState.EN_ROUTE_TO_SERVICE
        # TODO: real navigation to nearest charging/service station.
        self._release_and_return()

    def _release_and_return(self):
        self.state = RescueState.RELEASING
        self.get_logger().info(f'{self.robot_id}: {self.active_target} released for service.')
        self.active_target = None
        self.state = RescueState.IDLE  # back to normal operation / eligible for own tasks


def main(args=None):
    rclpy.init(args=args)
    node = RescueController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
