"""
Task Manager (Box 1-2)

Generates new pickup->delivery tasks and broadcasts them to all robots via
a ROS 2 topic (standing in for true P2P, per your Unity-vs-Gazebo /
ROS-topics-as-P2P decision).

Publishes: /swarmgrid/task_broadcast  (std_msgs/String, JSON payload for now)
Subscribes: /swarmgrid/task_assigned  (to know a task left the pool)

TODO tonight:
  - Replace the JSON-over-String hack with a proper custom msg
    (e.g. swarmgrid_msgs/Task) once you've got the skeleton building.
  - Wire in a real task source (random generator for demo, or a scripted
    scenario list for your benchmark runs).
"""

import json
import random
import time
import uuid

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from swarmgrid.utils.config import DEFAULT_TASK_DEADLINE_SEC


class TaskManager(Node):
    def __init__(self):
        super().__init__('task_manager')
        self.publisher_ = self.create_publisher(String, '/swarmgrid/task_broadcast', 10)
        self.subscription = self.create_subscription(
            String, '/swarmgrid/task_assigned', self.on_task_assigned, 10)
        self.pending_tasks = {}

        # Placeholder: emit a new task every N seconds. Replace with your
        # scripted benchmark scenarios (Box: demo scenarios) when ready.
        self.timer = self.create_timer(5.0, self.generate_task)
        self.get_logger().info('Task Manager started.')

    def generate_task(self):
        task_id = str(uuid.uuid4())[:8]
        task = {
            'task_id': task_id,
            'pickup': self._random_point(),
            'delivery': self._random_point(),
            'deadline': time.time() + DEFAULT_TASK_DEADLINE_SEC,
            'priority': random.choice(['normal', 'high']),
        }
        self.pending_tasks[task_id] = task
        msg = String()
        msg.data = json.dumps(task)
        self.publisher_.publish(msg)
        self.get_logger().info(f'Broadcast task {task_id}: {task["pickup"]} -> {task["delivery"]}')

    def on_task_assigned(self, msg: String):
        data = json.loads(msg.data)
        task_id = data.get('task_id')
        if task_id in self.pending_tasks:
            del self.pending_tasks[task_id]
            self.get_logger().info(f'Task {task_id} assigned to {data.get("winner")}')

    @staticmethod
    def _random_point():
        # TODO: replace with real warehouse waypoint coordinates from your map
        return [round(random.uniform(0, 20), 2), round(random.uniform(0, 20), 2)]


def main(args=None):
    rclpy.init(args=args)
    node = TaskManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
