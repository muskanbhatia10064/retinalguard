"""
spike_generator.py
"The brain" — Leaky Integrate-and-Fire (LIF) neuron simulation with
STDP-inspired weight updates, operating on the 10x10 spike grid from
crowd_detector.py.

Each grid cell maps to one LIF neuron. Co-firing adjacent cells
(STDP-style Hebbian rule) strengthen their connection weights —
this is used to detect spreading/synchronized crowd surges, which
is a key precursor to crush events.
"""

import numpy as np

GRID_SIZE = 10

# LIF neuron state
_membrane_potential = np.zeros((GRID_SIZE, GRID_SIZE))
_threshold = 1.0
_leak = 0.15  # leak factor per step
_refractory = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

# STDP weight matrix: connection strength between each cell and its
# right-neighbor and down-neighbor (simple 2D lattice STDP)
_weights_right = np.full((GRID_SIZE, GRID_SIZE - 1), 0.5)
_weights_down = np.full((GRID_SIZE - 1, GRID_SIZE), 0.5)

STDP_LR = 0.05  # learning rate
STDP_DECAY = 0.01


def lif_step(spike_grid: np.ndarray) -> np.ndarray:
    """
    Runs one LIF update step.

    Input: spike_grid (10x10, intensities in [0,1]) — treated as input current
    Output: binary spike output grid (10x10, 1 = fired, 0 = no fire)
    """
    global _membrane_potential, _refractory

    # Decrease refractory counters
    _refractory = np.maximum(_refractory - 1, 0)

    # Integrate input current, leak existing potential
    _membrane_potential = _membrane_potential * (1 - _leak) + spike_grid

    # Neurons in refractory period can't fire
    can_fire = _refractory == 0
    fired = (_membrane_potential >= _threshold) & can_fire

    # Reset potential for fired neurons, set refractory period
    _membrane_potential[fired] = 0
    _refractory[fired] = 2

    return fired.astype(np.float32)


def stdp_update(fired_grid: np.ndarray):
    """
    STDP-inspired update: if two adjacent cells fire together (within
    the same timestep, approximating near-simultaneous spikes), their
    connection weight increases. Otherwise weights slowly decay.
    """
    global _weights_right, _weights_down

    # Right-neighbor co-firing
    co_right = fired_grid[:, :-1] * fired_grid[:, 1:]
    _weights_right += STDP_LR * co_right
    _weights_right -= STDP_DECAY * (1 - co_right)
    _weights_right = np.clip(_weights_right, 0, 1)

    # Down-neighbor co-firing
    co_down = fired_grid[:-1, :] * fired_grid[1:, :]
    _weights_down += STDP_LR * co_down
    _weights_down -= STDP_DECAY * (1 - co_down)
    _weights_down = np.clip(_weights_down, 0, 1)


def get_spike_density_score(spike_grid: np.ndarray) -> float:
    """
    Runs LIF + STDP for one step and returns a density score in [0,1]
    that reflects both raw spike intensity AND synchronized firing
    (high STDP weights = neurons firing together = surge precursor).
    """
    fired = lif_step(spike_grid)
    stdp_update(fired)

    raw_density = float(spike_grid.mean())
    fired_density = float(fired.mean())
    sync_strength = float((_weights_right.mean() + _weights_down.mean()) / 2)

    # Weighted combination: raw intensity, actual firing rate, synchrony
    score = 0.5 * raw_density + 0.3 * fired_density + 0.2 * sync_strength
    return float(np.clip(score, 0, 1))


def get_weight_snapshot():
    """Returns current STDP weight matrices (for debugging/visualization)."""
    return {
        "weights_right": _weights_right.tolist(),
        "weights_down": _weights_down.tolist(),
    }


def reset():
    """Reset all neuron states — call when switching scenarios."""
    global _membrane_potential, _refractory, _weights_right, _weights_down
    _membrane_potential = np.zeros((GRID_SIZE, GRID_SIZE))
    _refractory = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
    _weights_right = np.full((GRID_SIZE, GRID_SIZE - 1), 0.5)
    _weights_down = np.full((GRID_SIZE - 1, GRID_SIZE), 0.5)
