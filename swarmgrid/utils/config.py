"""
Central place for the placeholder constants your flowchart calls out.
Fill these in tonight during Box 1-2 — don't leave them abstract while coding.
"""

# --- Fleet ---
NUM_ROBOTS = 5
RESCUE_CAPABLE_IDS = ["R5"]  # dual-role: normal AMR + rescue when needed

# --- Battery / eligibility (Box 2) ---
MIN_BATTERY_TO_BID = 0.20        # 20% — below this, robot can't take new tasks
LOW_BATTERY_THRESHOLD = 0.25     # triggers "navigate to charging station" (Box 7)
CRITICAL_BATTERY_THRESHOLD = 0.10

# --- Failure detection (Box 8-9) ---
HEARTBEAT_INTERVAL_SEC = 1.0
HEARTBEAT_MISS_THRESHOLD = 3          # missed beats before "suspected issue"
RECOVERY_GRACE_PERIOD_SEC = 5.0       # time allowed to respond before -> FAILED
STATUS_VERIFICATION_TIMEOUT_SEC = 3.0

# --- Rescue (Box 10) ---
RESCUE_PRIORITY_WEIGHT = 1000.0   # added to bid cost so rescue tasks dominate auction
SAFE_PAUSE_POINTS = [
    # (x, y) placeholders — replace with real warehouse coordinates
    (2.0, 2.0),
    (2.0, 18.0),
    (18.0, 2.0),
    (18.0, 18.0),
]

# --- Space-time reservation (Box 5) ---
RESERVATION_CELL_SIZE = 1.0       # grid cell size, meters
RESERVATION_TIME_STEP = 0.5       # seconds per discretized time slot

# --- Safety firewall (Box 6) ---
MAX_LINEAR_SPEED = 1.0            # m/s, kinematic limit checked by firewall
MAX_ANGULAR_SPEED = 1.5           # rad/s

# --- Task generation (Box 2) ---
DEFAULT_TASK_DEADLINE_SEC = 120.0
