"""
app.py
NeuroWatch Backend — Flask + Flask-SocketIO server.

Endpoints:
  GET /api/risk?scenario=normal|kumbh_surge|crush
      Returns current spike grid, risk score, status, rescue plan, victim info.

  GET /api/scenario/<name>
      Sets the active scenario (normal | kumbh_surge | crush).

Socket.IO:
  Emits "update" event every ~800ms with the same payload as /api/risk,
  using the currently active scenario.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
import time
import datetime

import crowd_detector
import spike_generator
import risk_engine

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

VALID_SCENARIOS = {"normal", "kumbh_surge", "crush"}

# Shared state
_state = {
    "scenario": "normal",
}
_alert_seq = 0


def build_payload(scenario: str) -> dict:
    """Builds the full data payload for a given scenario."""
    global _alert_seq

    grid = crowd_detector.get_spike_grid(scenario)
    flow_variance = crowd_detector.get_flow_variance(scenario)
    spike_rate = crowd_detector.get_spike_rate()

    spike_density = spike_generator.get_spike_density_score(grid)

    risk = risk_engine.compute_risk(spike_density, flow_variance, spike_rate)
    status = risk_engine.get_status(risk)
    rescue = risk_engine.get_rescue_plan(risk, grid)
    victim = risk_engine.detect_victim(grid)

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    # Build an alert entry (frontend can choose to log it)
    _alert_seq += 1
    alert = {
        "id": _alert_seq,
        "timestamp": timestamp,
        "risk": round(risk),
        "zone": rescue.get("zone"),
        "status": status,
        "message": rescue.get("action", "Monitoring..."),
    }

    return {
        "scenario": scenario,
        "timestamp": timestamp,
        "spikeGrid": grid.tolist(),
        "spikeDensity": round(spike_density, 3),
        "flowVariance": round(flow_variance, 3),
        "spikeRate": round(spike_rate, 3),
        "risk": round(risk, 1),
        "status": status,
        "dangerZone": rescue.get("zone"),
        "victim": victim,
        "rescue": rescue,
        "alert": alert,
    }


@app.route("/api/risk", methods=["GET"])
def get_risk():
    scenario = request.args.get("scenario", _state["scenario"])
    if scenario not in VALID_SCENARIOS:
        scenario = "normal"
    payload = build_payload(scenario)
    return jsonify(payload)


@app.route("/api/scenario/<name>", methods=["GET", "POST"])
def set_scenario(name):
    if name not in VALID_SCENARIOS:
        return jsonify({"error": "invalid scenario", "valid": list(VALID_SCENARIOS)}), 400

    if _state["scenario"] != name:
        spike_generator.reset()  # reset LIF/STDP state on scenario change

    _state["scenario"] = name
    return jsonify({"scenario": name, "status": "ok"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "scenario": _state["scenario"]})


# ---------------------------------------------------------------------------
# Background broadcaster — emits live updates via Socket.IO every ~800ms
# ---------------------------------------------------------------------------

def _broadcaster():
    while True:
        payload = build_payload(_state["scenario"])
        socketio.emit("update", payload)
        time.sleep(0.8)


_broadcaster_thread = None


@socketio.on("connect")
def on_connect():
    global _broadcaster_thread
    if _broadcaster_thread is None or not _broadcaster_thread.is_alive():
        _broadcaster_thread = threading.Thread(target=_broadcaster, daemon=True)
        _broadcaster_thread.start()


@socketio.on("set_scenario")
def on_set_scenario(data):
    name = data.get("scenario") if isinstance(data, dict) else None
    if name in VALID_SCENARIOS:
        if _state["scenario"] != name:
            spike_generator.reset()
        _state["scenario"] = name


if __name__ == "__main__":
    print("NeuroWatch backend running at http://localhost:5000")
    print("Try: http://localhost:5000/api/risk?scenario=crush")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
