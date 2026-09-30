# SwarmGrid (SIH26123)

Decentralized 5-robot AMR warehouse fleet-coordination system, Gazebo + ROS 2.

## Flowchart box -> file map

| Box | What | File |
|---|---|---|
| 1 | Initialization | `launch/swarmgrid_launch.py`, `utils/config.py` |
| 2 | Task generation + eligibility check | `auction/task_manager.py`, `utils/cost_function.py` |
| 3 | Decentralized auction | `auction/robot_agent.py` |
| 4 | Path planning (A* / Cooperative A*) | `planning/path_planner.py` |
| 5 | Movement coordination (PIBT + reservations) | `coordination/pibt_coordinator.py`, `coordination/reservation_table.py` |
| 6 | Safety firewall (final authority) | `safety/action_firewall.py` |
| 7 | Task execution | `monitoring/task_executor.py` |
| 8 | Continuous monitoring + failure detection engine | `monitoring/fleet_monitor.py`, `failure/failure_detector.py` |
| 9 | Failure handling & task reallocation | `failure/failure_detector.py` (publishes `/swarmgrid/task_released`) |
| 10 | Rescue & towing (R5) | `rescue/rescue_controller.py` |

## Build & run

```bash
# From your ROS 2 workspace src/ folder:
git clone <this> swarmgrid   # or just drop this folder in as-is
cd ~/your_ws
colcon build --packages-select swarmgrid
source install/setup.bash

ros2 launch swarmgrid swarmgrid_launch.py
```

## Tonight's priority order (per the 2-night/1-day plan)

1. **Box 1-4**: get `task_manager` + `robot_agent` + `path_planner` talking —
   robots should bid, win, and print "starting path planning." Collisions
   are fine at this stage.
2. **Box 5-6** (daytime): wire `reservation_table` into `path_planner`'s
   `cooperative_astar`, and get `action_firewall` actually rejecting unsafe
   moves. This is where "zero collisions" gets proven — don't rush it.
3. **Box 9-10** (night 2): `failure_detector`'s `debug_force_fail` topic lets
   you trigger a demo rescue without building real failure injection —
   use it.
4. **Hard cutoff**: pick a time (e.g. 4-5am night 2) after which you stop
   coding regardless of state and move to voiceover + presentation.

## Known placeholders to fill in before it actually runs

- `utils/config.py` — weights, thresholds, safe pause points are all
  placeholder numbers/coordinates. Tune against your real warehouse scale.
- `planning/path_planner.py` — grid size + obstacles are empty; load your
  real warehouse map.
- `auction/robot_agent.py` — distance/energy/congestion bid inputs are
  placeholders until `path_planner` is wired in for real.
- No custom `swarmgrid_msgs` package yet — everything rides on
  `std_msgs/String` with JSON payloads for speed. Fine for a hackathon
  prototype; revisit only if you have spare time.
