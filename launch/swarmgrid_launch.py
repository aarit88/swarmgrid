"""
SwarmGrid launch file.

Brings up:
  - task_manager (Box 1-2)
  - one robot_agent + one task_executor per robot, R1-R5 (Box 2-3, 7)
  - path_planner, pibt_coordinator, reservation_table (Box 4-5)
  - action_firewall (Box 6)
  - fleet_monitor, failure_detector (Box 8-9)
  - rescue_controller (Box 10) — only R5 is rescue-capable per config.py,
    but it's harmless to launch on all 5; each checks its own robot_id.

Run with:
  ros2 launch swarmgrid swarmgrid_launch.py

TODO tonight:
  - Add Gazebo world spawn (gazebo_ros) once your worlds/*.world file exists.
  - Add per-robot namespaces if topics need to be robot-scoped rather than
    shared (currently everything is flat, relying on robot_id fields inside
    message payloads — fine for a hackathon prototype, revisit if it gets
    confusing).
"""

from launch import LaunchDescription
from launch_ros.actions import Node

ROBOT_IDS = ['R1', 'R2', 'R3', 'R4', 'R5']


def generate_launch_description():
    nodes = [
        Node(package='swarmgrid', executable='task_manager', name='task_manager', output='screen'),
        Node(package='swarmgrid', executable='path_planner', name='path_planner', output='screen'),
        Node(package='swarmgrid', executable='pibt_coordinator', name='pibt_coordinator', output='screen'),
        Node(package='swarmgrid', executable='action_firewall', name='action_firewall', output='screen'),
        Node(package='swarmgrid', executable='fleet_monitor', name='fleet_monitor', output='screen'),
        Node(package='swarmgrid', executable='failure_detector', name='failure_detector', output='screen'),
    ]

    for rid in ROBOT_IDS:
        nodes.append(Node(
            package='swarmgrid', executable='robot_agent',
            name=f'robot_agent_{rid}', output='screen',
            parameters=[{'robot_id': rid}],
        ))
        nodes.append(Node(
            package='swarmgrid', executable='task_executor',
            name=f'task_executor_{rid}', output='screen',
            parameters=[{'robot_id': rid}],
        ))
        nodes.append(Node(
            package='swarmgrid', executable='rescue_controller',
            name=f'rescue_controller_{rid}', output='screen',
            parameters=[{'robot_id': rid}],
        ))

    return LaunchDescription(nodes)
