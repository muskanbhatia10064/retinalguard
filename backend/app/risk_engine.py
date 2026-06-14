"""
risk_engine.py
"The brain — Part 2": converts spike density, flow variance, and
spike rate into an overall risk score (0-100), status label, and a
recommended rescue plan including evacuation route and victim
detection.
"""

import numpy as np

# Mapping from grid (row, col) -> zone id, mirrors data/venue_layout.json
ZONE_MAP = {
    (0, 0): "A1", (0, 1): "A2",
    (1, 0): "B1", (1, 1): "B2",
    (2, 3): "C3", (3, 4): "C4",
    (4, 5): "D5", (5, 6): "E6",
    (6, 7): "F7", (7, 8): "G8",
    (8, 9): "H9", (9, 9): "J10",
}

# Which evacuation route applies to each zone (matches venue_layout.json routes)
ZONE_TO_ROUTE = {
    "A1": "A", "A2": "A", "B1": "A", "B2": "A",
    "C3": "B", "D5": "B", "E6": "B",
    "C4": "C", "F7": "C", "G8": "C", "H9": "C", "J10": "C",
}

ROUTE_EXIT_GATE = {
    "A": "Gate 1",
    "B": "Gate 2",
    "C": "Gate 3 (Emergency)",
}

ANNOUNCEMENTS = {
    "WARNING": (
        "Attention: Crowd density rising in the venue. "
        "Please move calmly toward designated exits and follow staff instructions."
    ),
    "HIGH RISK": (
        "Attention: High crowd density detected. For your safety, please move away "
        "from congested areas and proceed toward the nearest marked exit calmly."
    ),
    "EMERGENCY": (
        "EMERGENCY: Please move away from the danger zone immediately and proceed "
        "to the Emergency Exit. Follow officer instructions and remain calm."
    ),
}


def get_status(risk: float) -> str:
    """Maps a risk score (0-100) to a status label."""
    if risk < 25:
        return "SAFE"
    elif risk < 50:
        return "CAUTION"
    elif risk < 70:
        return "WARNING"
    elif risk < 85:
        return "HIGH RISK"
    else:
        return "EMERGENCY"


def compute_risk(spike_density: float, flow_variance: float, spike_rate: float) -> float:
    """
    risk = 0.4 x density + 0.3 x flow_variance + 0.3 x spike_rate
    Inputs are in [0,1]. A gain factor amplifies the combined signal
    so that normal/surge/crush scenarios map to roughly 15/65/92.
    """
    raw = 0.4 * spike_density + 0.3 * flow_variance + 0.3 * spike_rate
    GAIN = 2.9
    return float(np.clip(raw * 100 * GAIN, 0, 100))


def _find_hottest_zone(grid: np.ndarray):
    """Finds the grid cell with highest intensity that maps to a known zone."""
    flat_indices = np.argsort(grid, axis=None)[::-1]  # descending
    for idx in flat_indices:
        r, c = divmod(int(idx), grid.shape[1])
        if (r, c) in ZONE_MAP:
            return ZONE_MAP[(r, c)], grid[r, c]
    return None, 0.0


def detect_victim(grid: np.ndarray):
    """
    Finds a low-motion cell surrounded by high-motion cells
    (potential trapped/immobile person in a crush scenario).

    Returns: {"zone": str, "confidence": float} or None
    """
    rows, cols = grid.shape
    best = None
    best_confidence = 0.0

    for r in range(rows):
        for c in range(cols):
            if (r, c) not in ZONE_MAP:
                continue
            center = grid[r, c]
            if center > 0.25:
                continue  # not low-motion enough

            neighbors = []
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        neighbors.append(grid[nr, nc])

            if not neighbors:
                continue

            avg_neighbor = float(np.mean(neighbors))
            if avg_neighbor > 0.35:
                confidence = float(np.clip((avg_neighbor - center), 0, 1))
                if confidence > best_confidence:
                    best_confidence = confidence
                    best = ZONE_MAP[(r, c)]

    if best and best_confidence > 0.2:
        return {"zone": best, "confidence": round(best_confidence, 2)}
    return None


def get_rescue_plan(risk: float, grid: np.ndarray) -> dict:
    """
    Returns a full rescue plan dict consumed by the frontend:
    {
      status, action, zone, route, exitGate, officers, announcement
    }
    """
    status = get_status(risk)
    zone, intensity = _find_hottest_zone(grid)

    if status in ("SAFE", "CAUTION") or zone is None:
        return {
            "status": status,
            "action": "Monitor — no action required" if status == "SAFE"
                      else "Increase observation frequency in high-traffic zones",
            "zone": None,
            "route": None,
            "exitGate": None,
            "officers": 2 if status == "SAFE" else 4,
            "announcement": "",
        }

    route = ZONE_TO_ROUTE.get(zone, "C")
    exit_gate = ROUTE_EXIT_GATE.get(route, "Gate 3 (Emergency)")

    if status == "WARNING":
        action = f"Increase crowd control near {zone}; prepare evacuation Route {route}"
        officers = 6
    elif status == "HIGH RISK":
        action = f"Begin partial evacuation of {zone} via Route {route}; deploy additional units"
        officers = 10
    else:  # EMERGENCY
        action = f"IMMEDIATE EVACUATION — deploy all available units to {zone}, Route {route}"
        officers = 14

    return {
        "status": status,
        "action": action,
        "zone": zone,
        "route": route,
        "exitGate": exit_gate,
        "officers": officers,
        "announcement": ANNOUNCEMENTS.get(status, ""),
    }
