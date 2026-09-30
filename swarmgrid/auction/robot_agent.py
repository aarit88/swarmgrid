"""
Robot Agent (Box 2-3)

One instance per robot (launch with a `robot_id` param: R1..R5).
Listens for broadcast tasks, runs the eligibility check, computes a bid
using the shared cost function, and participates in the deterministic
winner-selection auction.

This is intentionally the most "core" file — everything else (path
planning, PIBT, firewall) hangs off a winning robot's post-auction state.

Publishes:
  /swarmgrid/bids            (String/JSON: {task_id, robot_id, cost})
  /swarmgrid/task_assigned   (String/JSON: {task_id, winner})
  /swarmgrid/heartbeat       (String/JSON: {robot_id, timestamp, state})
Subscribes:
  /swarmgrid/task_broadcast
  /swarmgrid/bids            (to see everyone's bids and self-select winner)
  /swarmgrid/rescue_mission  (Box 10: pulls this robot into rescue mode)

TODO tonight:
  - Replace fake distance/energy/congestion placeholders with real numbers
    from path_planner once box 4 exists.
  - This currently assumes every robot sees every bid and independently
    computes the same winner (fully decentralized, no arbiter) — keep that
    property, it's core to your "no central controller" success criterion.
"""

import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from swarmgrid.utils.config import (
    HEARTBEAT_INTERVAL_SEC,
    MIN_BATTERY_TO_BID,
    RESCUE_PRIORITY_WEIGHT,
)
from swarmgrid.utils.cost_function import BidInputs, compute_bid_cost, is_eligible_to_bid


class RobotAgent(Node):
    def __init__(self):
        super().__init__('robot_agent')
        self.declare_parameter('robot_id', 'R1')
        self.robot_id = self.get_parameter('robot_id').value

        self.state = {
            'battery': 1.0,
            'health_active': True,
            'in_critical_task': False,
            'in_rescue_mode': False,
            'current_task': None,
            'position': [0.0, 0.0],
        }

        self.bids_by_task = {}  # task_id -> {robot_id: cost}

        self.bid_pub = self.create_publisher(String, '/swarmgrid/bids', 10)
        self.assign_pub = self.create_publisher(String, '/swarmgrid/task_assigned', 10)
        self.heartbeat_pub = self.create_publisher(String, '/swarmgrid/heartbeat', 10)

        self.create_subscription(String, '/swarmgrid/task_broadcast', self.on_task_broadcast, 10)
        self.create_subscription(String, '/swarmgrid/bids', self.on_bid_received, 10)
        self.create_subscription(String, '/swarmgrid/rescue_mission', self.on_rescue_mission, 10)

        self.create_timer(HEARTBEAT_INTERVAL_SEC, self.publish_heartbeat)

        self.get_logger().info(f'{self.robot_id} agent started.')

    # --- Box 2: eligibility + bid ---
    def on_task_broadcast(self, msg: String):
        task = json.loads(msg.data)
        task_id = task['task_id']
        self.bids_by_task.setdefault(task_id, {})

        eligible = is_eligible_to_bid(
            battery_level=self.state['battery'],
            min_battery=MIN_BATTERY_TO_BID,
            in_critical_task=self.state['in_critical_task'],
            in_rescue_mode=self.state['in_rescue_mode'],
            path_feasible=True,  # TODO: query path_planner once it exists
            health_active=self.state['health_active'],
        )
        if not eligible:
            self.get_logger().debug(f'{self.robot_id} not eligible for {task_id}, skipping.')
            return

        # TODO: pull real values from path_planner (Box 4) instead of placeholders
        bid_inputs = BidInputs(
            path_distance=self._distance_estimate(task),
            energy_estimate=1.0,
            congestion_score=0.0,
            completion_time=self._distance_estimate(task),  # placeholder 1:1 with distance
            battery_level=self.state['battery'],
            deadline_slack=task['deadline'] - time.time() - self._distance_estimate(task),
        )
        cost = compute_bid_cost(bid_inputs)

        out = String()
        out.data = json.dumps({'task_id': task_id, 'robot_id': self.robot_id, 'cost': cost})
        self.bid_pub.publish(out)

    def on_bid_received(self, msg: String):
        bid = json.loads(msg.data)
        task_id, robot_id, cost = bid['task_id'], bid['robot_id'], bid['cost']
        self.bids_by_task.setdefault(task_id, {})[robot_id] = cost

        # Every robot independently decides if it's a winner it should act on.
        # (Simple version — no timeout logic yet; add a "bids closed" timer
        # tonight once you see how fast bids actually arrive.)
        winner = self._determine_winner(task_id)
        if winner == self.robot_id and self.state['current_task'] is None:
            self.state['current_task'] = task_id
            out = String()
            out.data = json.dumps({'task_id': task_id, 'winner': self.robot_id})
            self.assign_pub.publish(out)
            self.get_logger().info(f'{self.robot_id} won task {task_id}, starting path planning.')
            # TODO: hand off to path_planner (Box 4) here.

    def _determine_winner(self, task_id: str):
        bids = self.bids_by_task.get(task_id, {})
        if not bids:
            return None
        # Lowest cost wins; tie-break by robot_id (deterministic across all robots)
        return sorted(bids.items(), key=lambda kv: (kv[1], kv[0]))[0][0]

    # --- Box 10: rescue mission override ---
    def on_rescue_mission(self, msg: String):
        data = json.loads(msg.data)
        if data.get('assigned_robot') != self.robot_id:
            return
        self.get_logger().warn(f'{self.robot_id} pulled into RESCUE mode for {data.get("target_robot")}.')
        self.state['in_rescue_mode'] = True
        # TODO: drop current_task at nearest safe pause point (Box 9/10),
        # then hand off to rescue_controller.

    def publish_heartbeat(self):
        msg = String()
        msg.data = json.dumps({
            'robot_id': self.robot_id,
            'timestamp': time.time(),
            'battery': self.state['battery'],
            'state': 'rescue' if self.state['in_rescue_mode'] else 'active',
        })
        self.heartbeat_pub.publish(msg)

    @staticmethod
    def _distance_estimate(task) -> float:
        px, py = task['pickup']
        dx, dy = task['delivery']
        return ((dx - px) ** 2 + (dy - py) ** 2) ** 0.5


def main(args=None):
    rclpy.init(args=args)
    node = RobotAgent()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
