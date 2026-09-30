"""
Failure Detector (Box 8-9)

Consumes "suspected issue" signals (from fleet_monitor's missed-heartbeat
check), runs status verification (send inquiry, re-check telemetry, allow
short recovery time), and if not recovered: marks the robot FAILED,
releases its current task back to the pool, broadcasts the failure, and
triggers rescue_controller.

TODO tonight (per your "manual trigger" shortcut for the demo):
  - Add a debug service/topic to force-fail a robot on command
    (e.g. `ros2 topic pub /swarmgrid/debug_force_fail ...`) so you don't
    need to build organic failure injection to get a demo-able rescue run.
    Keep the real detection path working alongside it, don't replace it.
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from swarmgrid.utils.config import RECOVERY_GRACE_PERIOD_SEC, STATUS_VERIFICATION_TIMEOUT_SEC


class FailureDetector(Node):
    def __init__(self):
        super().__init__('failure_detector')
        self.verifying = {}  # robot_id -> verification_start_time
        self.failed_robots = set()

        self.create_subscription(String, '/swarmgrid/suspected_failure', self.on_suspected, 10)
        # Debug/manual override for demo scenarios (per your shortcut plan)
        self.create_subscription(String, '/swarmgrid/debug_force_fail', self.on_force_fail, 10)

        self.failure_pub = self.create_publisher(String, '/swarmgrid/robot_failed', 10)
        self.reallocate_pub = self.create_publisher(String, '/swarmgrid/task_released', 10)

        self.create_timer(1.0, self.check_verification_timeouts)
        self.get_logger().info('Failure detector online.')

    def on_suspected(self, msg: String):
        data = json.loads(msg.data)
        robot_id = data['robot_id']
        if robot_id not in self.verifying and robot_id not in self.failed_robots:
            self.verifying[robot_id] = time.time()
            self.get_logger().warn(f'{robot_id}: starting status verification.')

    def on_force_fail(self, msg: String):
        """Demo shortcut: `ros2 topic pub /swarmgrid/debug_force_fail std_msgs/String '{data: R3}'`"""
        robot_id = msg.data.strip()
        self._mark_failed(robot_id, task_id=None)

    def check_verification_timeouts(self):
        now = time.time()
        for robot_id, start in list(self.verifying.items()):
            if now - start > STATUS_VERIFICATION_TIMEOUT_SEC + RECOVERY_GRACE_PERIOD_SEC:
                del self.verifying[robot_id]
                self._mark_failed(robot_id, task_id=None)

    def _mark_failed(self, robot_id: str, task_id):
        if robot_id in self.failed_robots:
            return
        self.failed_robots.add(robot_id)
        self.get_logger().error(f'{robot_id} marked FAILED.')

        failed_msg = String()
        failed_msg.data = json.dumps({'robot_id': robot_id, 'timestamp': time.time()})
        self.failure_pub.publish(failed_msg)

        # Box 9: release current task (if any) back to the pool for re-auction.
        released_msg = String()
        released_msg.data = json.dumps({'robot_id': robot_id, 'task_id': task_id})
        self.reallocate_pub.publish(released_msg)
        # TODO: rescue_controller (Box 10) should subscribe to /swarmgrid/robot_failed
        # and pick the nearest rescue-capable robot from there.


def main(args=None):
    rclpy.init(args=args)
    node = FailureDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
