"""
crowd_detector.py
Simulates the "data pipeline" — converts raw video frames into a
10x10 spike intensity grid (Address-Event Representation style).

In a real deployment this would do frame differencing on a video
stream from a Dynamic Vision Sensor / standard camera. For the
hackathon PoC we simulate realistic spike patterns for 3 scenarios.
"""

import numpy as np
import time

GRID_SIZE = 10

# Rolling history of spike grids, used for spike rate calculations
_history = []
_MAX_HISTORY = 20


def _base_noise(level=0.03):
    return np.random.uniform(0, level, size=(GRID_SIZE, GRID_SIZE))


def get_spike_grid(scenario: str) -> np.ndarray:
    """
    Returns a 10x10 numpy array of spike intensities in [0, 1].

    scenario: "normal" | "kumbh_surge" | "crush"
    """
    grid = _base_noise(0.08)

    if scenario == "normal":
        # Light, scattered activity
        grid += _base_noise(0.03)

    elif scenario == "kumbh_surge":
        # Growing hotspot near Food Court / Bathing Ghat (rows 2-3, cols 3-4)
        hotspot = np.random.uniform(0.75, 0.98, size=(2, 2))
        grid[2:4, 3:5] += hotspot
        # secondary moderate activity nearby
        grid[1:3, 2:4] += np.random.uniform(0.4, 0.55, size=(2, 2))

    elif scenario == "crush":
        # Severe, concentrated hotspot around C4 (row 3, col 4)
        hotspot = np.random.uniform(0.75, 0.98, size=(3, 3))
        grid[2:5, 3:6] += hotspot
        # C4 itself pushed to near-max (primary danger zone)
        grid[3, 4] = np.random.uniform(0.95, 1.0)
        # spillover to neighboring zones (kept lower than C4)
        grid[1:3, 2:4] += np.random.uniform(0.2, 0.35, size=(2, 2))
        # ensure C3 stays below C4
        grid[2, 3] = min(grid[2, 3], 0.85)
        # victim signature: a low-motion (trapped) cell surrounded by
        # high-motion cells, placed at D5 (adjacent to C4 hotspot)
        grid[4, 5] = np.random.uniform(0.05, 0.15)

    else:
        grid += _base_noise(0.05)

    grid = np.clip(grid, 0, 1)

    _history.append(grid.copy())
    if len(_history) > _MAX_HISTORY:
        _history.pop(0)

    return grid


def get_spike_rate(n: int = 10) -> float:
    """
    Average spike intensity over the last n frames in history.
    Returns a value in [0, 1].
    """
    if not _history:
        return 0.0
    recent = _history[-n:]
    return float(np.mean([g.mean() for g in recent]))


def get_flow_variance(scenario: str) -> float:
    """
    Simulates optical flow turbulence — how chaotic the motion is.
    Higher variance = more turbulent / panicked movement.
    Returns a value in [0, 1].
    """
    base = {
        "normal": 0.05,
        "kumbh_surge": 0.35,
        "crush": 0.85,
    }.get(scenario, 0.05)

    noise = np.random.uniform(-0.05, 0.05)
    return float(np.clip(base + noise, 0, 1))


def get_spike_density_score(grid: np.ndarray) -> float:
    """
    Overall spike density score for the current frame, in [0, 1].
    """
    return float(np.clip(grid.mean() * 1.4, 0, 1))
