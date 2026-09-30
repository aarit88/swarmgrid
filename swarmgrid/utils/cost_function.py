"""
Shared bid-cost function for SwarmGrid's decentralized auction (Box 3).

Cost = w_d*D + w_e*E + w_c*C + w_t*T + w_b*B

Where each robot computes this LOCALLY before broadcasting a bid.
Lowest valid cost wins; ties break on robot_id (deterministic, e.g. lexicographic).

TODO (tonight, Box 1-4 session):
  - Tune the weights below against your actual warehouse scale / robot speed.
  - Replace the placeholder distance/energy estimates with real values pulled
    from path_planner's A* output once that module exists.
"""

from dataclasses import dataclass


# --- Tunable weights: define these NOW, even as placeholders, don't leave abstract ---
W_DISTANCE = 1.0     # w_d
W_ENERGY = 0.5       # w_e
W_CONGESTION = 0.8   # w_c
W_TIME = 1.2         # w_t
W_BATTERY_RISK = 2.0  # w_b — penalize bidding when battery is marginal


@dataclass
class BidInputs:
    path_distance: float        # D: A*/Cooperative A* path length (meters or cells)
    energy_estimate: float      # E: estimated energy draw for this path
    congestion_score: float     # C: number of conflicting reservations / busy cells on path
    completion_time: float      # T: estimated ticks/seconds to complete task
    battery_level: float        # 0.0 - 1.0, current battery
    deadline_slack: float       # seconds until deadline minus completion_time; negative = at risk


def battery_risk(battery_level: float, deadline_slack: float) -> float:
    """Penalize low battery and tight/negative deadline slack. Simple linear model to start."""
    risk = (1.0 - battery_level)
    if deadline_slack < 0:
        risk += abs(deadline_slack) * 0.1  # scale factor, tune later
    return risk


def compute_bid_cost(inputs: BidInputs) -> float:
    b = battery_risk(inputs.battery_level, inputs.deadline_slack)
    return (
        W_DISTANCE * inputs.path_distance
        + W_ENERGY * inputs.energy_estimate
        + W_CONGESTION * inputs.congestion_score
        + W_TIME * inputs.completion_time
        + W_BATTERY_RISK * b
    )


def is_eligible_to_bid(battery_level: float, min_battery: float,
                        in_critical_task: bool, in_rescue_mode: bool,
                        path_feasible: bool, health_active: bool) -> bool:
    """Box 2 eligibility check, before a robot is even allowed to compute a bid."""
    if not health_active:
        return False
    if in_rescue_mode:
        return False
    if in_critical_task:
        return False
    if battery_level < min_battery:
        return False
    if not path_feasible:
        return False
    return True
