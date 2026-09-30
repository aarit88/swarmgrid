"""
Task Executor (Box 7)

Per-robot state machine: navigate to pickup -> pickup parcel (attach
payload) -> navigate to delivery -> deliver parcel (detach payload) ->
task completed -> release task & update state -> check battery ->
(charge if low) -> return to idle.

TODO tonight:
  - This is straightforward sequencing logic; good candidate to build
    fast and not over-engineer, save your hours for Box 5/6/9/10.
  - Hook actual Gazebo navigation (nav2 goal or direct cmd_vel) in place
    of the placeholder state transitions.
"""

from enum import Enum, auto

import rclpy
from rclpy.node import Node

from swarmgrid.utils.config import LOW_BATTERY_THRESHOLD


class ExecState(Enum):
    IDLE = auto()
    NAVIGATE_TO_PICKUP = auto()
    PICKUP = auto()
    NAVIGATE_TO_DELIVERY = auto()
    DELIVER = auto()
    TASK_COMPLETE = auto()
    CHARGING = auto()


class TaskExecutor(Node):
    def __init__(self):
        super().__init__('task_executor')
        self.declare_parameter('robot_id', 'R1')
        self.robot_id = self.get_parameter('robot_id').value
        self.state = ExecState.IDLE
        self.battery = 1.0
        self.get_logger().info(f'{self.robot_id} task executor idle.')
        # TODO: subscribe to /swarmgrid/task_assigned filtered to this robot_id,
        # drive the state machine below, publish nav goals.

    def step(self):
        """Placeholder single-tick state transition — replace with real
        nav feedback-driven transitions."""
        if self.state == ExecState.TASK_COMPLETE:
            if self.battery < LOW_BATTERY_THRESHOLD:
                self.state = ExecState.CHARGING
            else:
                self.state = ExecState.IDLE


def main(args=None):
    rclpy.init(args=args)
    node = TaskExecutor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
