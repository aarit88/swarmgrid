"""
Fleet Monitor (Box 8)

Aggregates heartbeats + telemetry from all robot_agents so failure_detector
(Box 9) has a single place to check for missed heartbeats / immobility /
abnormal behavior, and so you have one place to pull demo metrics from
(total task completion time, collision count, replans triggered, etc. —
your "Generate performance metrics" end box).

TODO tonight:
  - Wire real metric counters (collision_count should stay 0 — that's your
    headline success criterion, log every firewall rejection so you can
    prove it never actually resulted in a collision, just a wait/yield).
  - Decide log format now (CSV vs JSON-lines) so your presentation numbers
    are easy to pull at the end.
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from swarmgrid.utils.config import HEARTBEAT_MISS_THRESHOLD


class FleetMonitor(Node):
    def __init__(self):
        super().__init__('fleet_monitor')
        self.last_heartbeat = {}  # robot_id -> timestamp
        self.metrics = {
            'tasks_completed': 0,
            'collisions': 0,          # should stay 0 — success criterion
            'replans_triggered': 0,
            'failures_detected': 0,
            'rescues_completed': 0,
        }
        self.create_subscription(String, '/swarmgrid/heartbeat', self.on_heartbeat, 10)
        self.create_timer(1.0, self.check_missed_heartbeats)
        self.get_logger().info('Fleet monitor online.')

    def on_heartbeat(self, msg: String):
        data = json.loads(msg.data)
        self.last_heartbeat[data['robot_id']] = time.time()

    def check_missed_heartbeats(self):
        now = time.time()
        for robot_id, last_seen in self.last_heartbeat.items():
            if now - last_seen > HEARTBEAT_MISS_THRESHOLD:
                self.get_logger().warn(f'{robot_id}: suspected issue (missed heartbeats).')
                # TODO: publish to /swarmgrid/suspected_failure, let
                # failure_detector (Box 9) run status verification.


def main(args=None):
    rclpy.init(args=args)
    node = FleetMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
