# 🧠 NeuroWatch — Neuromorphic Crowd Safety Monitor

**Hackathon Project | Real-time crowd risk detection using event-driven, brain-inspired processing**

NeuroWatch detects dangerous crowd surges (like stampede precursors at large gatherings such as Kumbh Mela) using a spike-based "neuromorphic" pipeline: video → spike events → LIF neurons + STDP → risk score → automated rescue routing + alerts.

---

## 🚀 Quick Start

### 1. Backend (Flask + Socket.IO)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Backend runs at **http://localhost:5000**

Test it:
```bash
curl "http://localhost:5000/api/risk?scenario=normal"
curl "http://localhost:5000/api/risk?scenario=kumbh_surge"
curl "http://localhost:5000/api/risk?scenario=crush"
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**

> **Note:** The frontend works even if the backend isn't running — it automatically falls back to **Simulation Mode** using built-in mock data, so you can demo the UI standalone. The top bar shows "Live Backend" (green) or "Simulation Mode" (gray).

---

## 📁 Project Structure

```
NeuroWatch/
├── backend/
│   ├── app.py                  # Flask + Socket.IO server
│   ├── crowd_detector.py       # Spike grid generation (3 scenarios)
│   ├── spike_generator.py      # LIF neurons + STDP weight updates
│   ├── risk_engine.py          # Risk scoring + rescue planning
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx             # Routing + shared data context
│       ├── main.jsx
│       ├── index.css           # Dark theme design system
│       ├── pages/
│       │   ├── Dashboard.jsx   # Main live dashboard
│       │   └── AlertsPage.jsx  # Alert history + filters
│       └── components/
│           ├── HeatMap.jsx
│           ├── RiskGauge.jsx
│           ├── VenueMap.jsx
│           ├── RescuePanel.jsx
│           ├── AlertFeed.jsx
│           ├── AnnouncementBanner.jsx
│           ├── useNeuroWatchData.js   # Socket.IO + mock fallback hook
│           ├── NeuroWatchContext.jsx  # Shared state provider
│           └── mockData.js            # Simulation mode data
│
├── data/
│   └── venue_layout.json       # Zones, gates, evacuation routes
│
├── README.md
└── demo_script.md
```

---

## 🧪 How It Works

1. **`crowd_detector.py`** simulates a 10×10 grid of "spike" intensities — like an event-based camera that only reports *changes* in the scene, not full frames. Three scenarios are built in: `normal`, `kumbh_surge`, `crush`.

2. **`spike_generator.py`** runs each grid cell through a **Leaky Integrate-and-Fire (LIF)** neuron. When adjacent neurons fire together repeatedly, an **STDP (Spike-Timing-Dependent Plasticity)** rule strengthens their connection — this detects *synchronized* crowd surges, a key early-warning signal before a crush.

3. **`risk_engine.py`** combines spike density, flow variance, and spike rate into a **0–100 risk score**, maps it to a status (`SAFE → CAUTION → WARNING → HIGH RISK → EMERGENCY`), and generates a rescue plan: which zone is dangerous, which evacuation route to use, how many officers to deploy, and whether a possible victim (low-motion person surrounded by high motion) has been detected.

4. **Frontend** displays everything live via Socket.IO: a pulsing heatmap, animated risk gauge, top-down venue map with the danger zone glowing and an animated rescue route, a rescue panel, a scrolling alert feed, and an emergency announcement banner with text-to-speech.

---

## 🎮 Demo Flow

1. Open the dashboard — starts in **Normal** mode (risk ~15-25, all green).
2. Click **Kumbh Surge** — heatmap shows a hotspot near the Food Court (C3), risk climbs to ~50-65, status turns **WARNING**, venue map highlights C3 and shows Route B to Gate 2.
3. Click **Crush Scenario** — risk spikes to ~90+, status becomes **EMERGENCY**, venue map highlights C4 with Route C to the Emergency Exit, a possible victim is flagged near D5, the announcement banner appears and is **spoken aloud** via text-to-speech, and the alert feed logs the emergency event.
4. Visit **Alert History** to see the full log, filter by severity, or clear it.

---

## 👥 Team

| Member | Area |
|--------|------|
| M1 | Backend core — Flask API, crowd detection, scenario modes |
| M2 | Neuromorphic engine — LIF/STDP, risk scoring, rescue logic |
| M3 | Frontend dashboard — HeatMap, RiskGauge, design system |
| M4 | Venue map & rescue routing — VenueMap, RescuePanel, venue layout |
| M5 | Alerts, integration, TTS announcements, docs & presentation |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO, NumPy
- **Frontend:** React 18, Vite, React Router, Socket.IO Client
- **Design:** Custom dark theme (Inter + JetBrains Mono), SVG-based venue map and gauges
- **Browser API:** SpeechSynthesis for emergency announcements
