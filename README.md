# 🚆 AI-Powered Precise Train Traffic Control

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Vite-5.4-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Tests-120%2F120%20Passing-2EA44F?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests"/>
  <img src="https://img.shields.io/badge/Status-Phase%2012%20Production%20Ready-success?style=for-the-badge" alt="Status"/>
</p>

<p align="center">
  <strong>Real-Time Simulation • ML Delay Prediction • AI Dispatch Optimization • Formal Safety Validation • Explainable AI</strong>
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f172a,100:2563eb&height=180&section=header&text=AI%20Train%20Traffic%20Control&fontSize=38&fontColor=ffffff&animation=fadeIn&fontAlignY=38" alt="AI Train Traffic Control"/>
</p>

> **Academic simulation & decision-support prototype:** This project models railway traffic, delay propagation, scheduling, optimization, and safety validation entirely in software. It does **not** connect to field signaling, interlocking equipment, track circuits, or physical locomotives. All train movements and emergency scenarios are simulated.

---

## ✨ Project Overview

**AI-Powered Precise Train Traffic Control** is an end-to-end intelligent railway traffic simulation and decision-support system designed to improve section throughput while reducing delay propagation.

The platform combines:

- 🚄 Real-time kinematic train simulation
- 📡 WebSocket telemetry
- 🚦 Dynamic track occupancy and signaling
- 🔍 Conflict and bottleneck detection
- 🤖 Machine-learning delay prediction
- 🧠 Multi-objective AI dispatch optimization
- 🛡️ Formal 9-rule safety validation
- 🔎 Explainable AI decisions
- 👨‍✈️ Human traffic-controller interaction
- 📊 AI-vs-traditional benchmark evaluation
- 🚨 Synthetic emergency disruption and mitigation

### 🎯 Core Goal

> **Maximize railway section throughput while minimizing delays and passenger waiting time, subject to explicit safety constraints.**

---

# 🧩 Why This Project?

Modern railway corridors can experience cascading delays when a disturbance affects one or more trains.

Typical challenges include:

- **Artificial Capacity Loss** — inefficient use of loop lines and available headway margins.
- **Reactionary Braking** — unnecessary stopping caused by limited predictive scheduling.
- **Cascading Delays** — one delayed train propagating delays to other services.
- **Sub-optimal Throughput** — failure to dynamically exploit available section capacity.

The system addresses these challenges by combining **simulation + machine learning + optimization + explainability + formal safety validation**.

---

# 🚀 Core Capabilities

| Capability | What It Does |
|---|---|
| 🚆 Train Simulation | Models train movement using discrete-time kinematics |
| 📡 Live Telemetry | Streams simulation state through WebSockets |
| 🚦 Signaling | Simulates Green / Double Yellow / Yellow / Red states |
| 🔍 Conflict Detection | Detects headway, opposing movement, and junction conflicts |
| 🤖 ML Prediction | Forecasts arrival delay using 15 operational features |
| 🧠 AI Optimization | Selects dispatch sequences to improve throughput and delay |
| 🛡️ Safety Gate | Validates every proposed plan against 9 safety rules |
| 🔎 Explainable AI | Shows feature attribution, confidence, and alternatives |
| 👨‍✈️ Control Center | Supports controller approval, override, and scenarios |
| 📊 Benchmarking | Compares AI dispatch against traditional scheduling |
| 🚨 Emergency Simulation | Injects and mitigates synthetic disruptions |

---

# 🏗️ End-to-End Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    🚆 REAL-TIME TRAFFIC STATE                      │
│       Kinematic Simulation Engine + WebSocket Telemetry            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     🔍 CONFLICT DETECTION                          │
│     Headway • Opposing Movement • Junction • Bottleneck Queues     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🤖 ML DELAY PREDICTION                          │
│         HistGradientBoosting • 15 Features • R² ≈ 0.94            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   🧠 AI TRAFFIC OPTIMIZATION                       │
│          Throughput • Delay • Precedence • Track Selection         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   🔎 EXPLAINABLE AI ENGINE                         │
│      Feature Attribution • Confidence • Candidate Trade-offs      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  🛡️ FORMAL SAFETY VALIDATION                       │
│                    9-Rule Safety Verification                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ✅ PLAN APPROVED        ❌ PLAN REJECTED
                    │                     │
                    ▼                     ▼
          👨‍✈️ HUMAN CONTROLLER      🧯 FALLBACK RULE
             APPROVAL /             Hold / Maintain
              OVERRIDE                  Gap
                    │                     │
                    └──────────┬──────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    🚆 SIMULATION STATE                             │
│              Speeds • Routes • Reservations • Motion               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    📊 PERFORMANCE ANALYTICS                        │
│       Throughput • Delay Reduction • AI vs Traditional             │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 🧱 Development Phases

The system was developed through **12 integrated engineering phases**.

| Phase | Module | Key Deliverables |
|:---:|---|---|
| **1** | Foundation & Setup | FastAPI, SQLite, SQLAlchemy, Pydantic, React, Vite, health probes |
| **2** | Network & Infrastructure | Stations, sections, tracks, train fleet, CRUD APIs, synoptic map |
| **3** | Kinematic Simulation | Train physics, braking curves, dwell times, WebSocket telemetry |
| **4** | Dynamic Occupancy & Safety | Block reservation, signal state machines, track clearance |
| **5** | Conflict Detection | Headway violations, opposing movements, junction hazards, bottlenecks |
| **6** | ML Delay Prediction | HistGradientBoosting, 6,500 synthetic samples, 15 features, R² ≈ 0.94 |
| **7** | AI Traffic Optimization | Multi-objective dispatch optimization and candidate ranking |
| **8** | Formal Safety Validation | 9-rule safety gate between optimizer and simulation |
| **9** | AI vs Traditional Evaluation | 6 standardized benchmark scenarios |
| **10** | Explainable AI | Feature attribution, calibrated confidence, trade-off candidates |
| **11** | Intelligent Control Center | Dashboard, overrides, emergencies, scenario manager, demo runner |
| **12** | Production Readiness | Logging, error handling, seeding, docs, 120 automated tests |

---

# 🤖 Machine Learning — Delay Prediction

The ML subsystem predicts train arrival delay using operational features available during simulation.

### Model

**HistGradientBoostingRegressor**

### Training Data

- **6,500 synthetic samples**
- **15 operational features**
- Reported validation performance: **R² ≈ 0.94**

### Pipeline

```text
Operational State
       │
       ▼
15 Real-Time Features
       │
       ▼
Feature Processing
       │
       ▼
HistGradientBoosting
       │
       ▼
Predicted Arrival Delay
       │
       ▼
AI Dispatch Optimizer
```

---

# 🧠 AI Traffic Optimization

The optimization engine dynamically evaluates dispatch candidates.

The objective is to balance:

```text
                 ┌─────────────────┐
                 │ AI DISPATCH     │
                 │ OPTIMIZER       │
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        🚆 Throughput  ⏱️ Delay    👥 Passenger
                                      Waiting
             └────────────┼────────────┘
                          ▼
                 Candidate Ranking
                          │
                          ▼
                 Proposed Dispatch
                          │
                          ▼
                 🛡️ Safety Gate
```

The optimizer is designed to maximize section throughput while minimizing total delay and passenger waiting time.

---

# 🛡️ Formal Safety Validation

Safety validation is implemented as a dedicated algorithmic gate between AI optimization and simulation state application.

```text
AI Proposed Plan
       │
       ▼
┌───────────────────────┐
│ 9 Safety Rule Checks  │
└───────────┬───────────┘
            │
      ┌─────┴─────┐
      ▼           ▼
   PASS          FAIL
      │           │
      ▼           ▼
 APPROVED      REJECTED
      │           │
      ▼           ▼
Controller     Fallback
Approval       Dispatch
```

The project reports **zero unsafe plans applied within the simulation environment**.

> This software safety gate is an internal simulation safeguard. It does not replace certified railway signaling, interlocking, or statutory railway safety systems.

---

# 🔎 Explainable AI

The system is designed to make AI recommendations understandable to traffic controllers.

Each decision can expose:

- Feature attribution
- Confidence information
- Natural-language justification
- Candidate alternatives
- Trade-off comparisons
- Human controller feedback

### Example Decision Flow

```text
Current Traffic State
        ↓
Predicted Delays
        ↓
Candidate Dispatch Plans
        ↓
Optimization Score
        ↓
Safety Validation
        ↓
Explainable Recommendation
        ↓
Controller Decision
```

---

# 👨‍✈️ Intelligent Control Center

The control center provides a unified operational interface for simulation and decision support.

### Includes

- Real-time network state
- Train positions
- Active conflicts
- Delay predictions
- AI recommendations
- Safety status
- Manual overrides
- Emergency scenarios
- Benchmark results
- Automated 12-step demonstration

### Control Actions

```text
┌────────────────────────────────────────┐
│        TRAFFIC CONTROLLER              │
├────────────────────────────────────────┤
│  ▶ Approve AI Dispatch                 │
│  ✋ Hold Train                         │
│  ⚡ Speed Command                      │
│  🚨 Emergency Stop                     │
│  🧯 Mitigate Incident                  │
│  🔄 Reset Scenario                     │
└────────────────────────────────────────┘
```

---

# 🚨 Emergency Scenario Simulation

The project supports synthetic emergency scenarios such as:

- `TRACK_BLOCKAGE`
- `SIGNAL_FAILURE`

Emergency workflow:

```text
🚨 Incident Injected
        ↓
Traffic State Updated
        ↓
Conflict / Impact Analysis
        ↓
AI Recovery Plan
        ↓
🛡️ Safety Validation
        ↓
Recovery Action
        ↓
Updated Simulation
```

All emergency scenarios remain inside the software simulation environment.

---

# 📊 AI vs Traditional Benchmark

The analytics engine compares AI dispatching with traditional scheduling under identical initial conditions.

### Benchmark Scope

- **6 standardized scenarios**
- Identical initial states
- Throughput comparison
- Delay comparison
- Composite scoring
- Percentage gains
- CSV / JSON export

```text
                 SAME INITIAL STATE
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       🤖 AI DISPATCH        📋 TRADITIONAL
             │                     │
             ▼                     ▼
       Performance A          Performance B
             │                     │
             └──────────┬──────────┘
                        ▼
               📊 COMPARISON ENGINE
                        │
                        ▼
               Benchmark Report
```

---

# 🧰 Technology Stack

## Backend

- 🐍 Python 3.14+
- ⚡ FastAPI 0.110+
- 🚀 Uvicorn 0.28+
- 🗄️ SQLite
- 🧱 SQLAlchemy 2.0
- ✅ Pydantic v2
- 📊 NumPy
- 🐼 Pandas
- 🤖 Scikit-Learn
- 💾 Joblib

## Frontend

- ⚛️ React 18
- ⚡ Vite 5.4
- 🎨 Modern dark-mode responsive UI
- 🖼️ Lucide React
- 🔗 Axios
- 📡 Native WebSocket Client

## Testing

- 🧪 Pytest 9.1+
- 🌐 HTTPX TestClient
- 🔄 Integration Testing
- 🛡️ Safety Validation Testing
- 🤖 ML / Optimization Testing
- 🔌 API Testing
- 🔗 End-to-End Testing

---

# 📁 Repository Structure

```text
.
├── backend/
│   ├── analytics/                  # Phase 9 benchmark engine
│   ├── app/
│   │   ├── config/                 # Settings & structured logging
│   │   ├── database/               # SQLite engine & sessions
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── routes/                 # REST API routes
│   │   ├── schemas/                # Pydantic schemas
│   │   └── services/               # Business logic & telemetry
│   ├── control_center/             # Phase 11 control center
│   ├── explainability/             # Phase 10 Explainable AI
│   ├── ml/                         # Phase 6 ML model
│   ├── optimization/               # Phase 7 optimizer
│   ├── safety/                     # Phase 8 safety engine
│   └── requirements.txt
│
├── data/
│   ├── sample/                     # Sample railway data
│   ├── generated/                  # Evaluation datasets
│   └── seed.py                     # Database seeder
│
├── docs/
│   ├── setup.md
│   ├── architecture.md
│   ├── methodology.md
│   ├── api.md
│   ├── ml.md
│   ├── optimization.md
│   ├── safety.md
│   ├── analytics.md
│   └── demo.md
│
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   ├── pages/                  # Dashboard pages
│   │   └── utils/                  # Shared formatters
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   ├── test_api.py
│   ├── test_railway.py
│   ├── test_simulation.py
│   ├── test_phase4.py
│   ├── test_phase5.py
│   ├── test_phase6.py
│   ├── test_phase7.py
│   ├── test_phase8.py
│   ├── test_phase9.py
│   ├── test_phase10.py
│   ├── test_phase11.py
│   └── test_phase12_end_to_end.py
│
├── .env.example
├── README.md
└── requirements.txt
```

---

# ⚙️ Installation & Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Git

---

## 1️⃣ Clone the Repository

```bash
git clone <repository-url>
cd "Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control"
```

---

## 2️⃣ Create Python Environment

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3️⃣ Configure Environment

```bash
copy .env.example .env
```

For Linux/macOS:

```bash
cp .env.example .env
```

---

## 4️⃣ Seed Railway Network

```bash
python -m data.seed --seed 42 --reset
```

This initializes the standard simulated corridor with:

- 5 stations
- 7 sections
- 14 directional tracks
- 12 trains

---

## 5️⃣ Install Frontend

```bash
cd frontend
npm install
cd ..
```

---

# ▶️ Run the Application

## Terminal 1 — FastAPI Backend

```powershell
.\.venv\Scripts\uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### Backend

```text
http://127.0.0.1:8000
```

### Swagger API

```text
http://127.0.0.1:8000/docs
```

### Health

```text
http://127.0.0.1:8000/api/health
```

---

## Terminal 2 — React Frontend

```bash
cd frontend
npm run dev
```

### Dashboard

```text
http://localhost:5173
```

---

# 🧪 Automated Testing

The project includes **120 automated tests** covering all major phases.

Run:

```bash
pytest tests/ -v
```

Expected result:

```text
===================== test session starts =====================

collected 120 items

...

================ 120 passed, 0 failed =================
```

### Test Coverage

| Area | Coverage |
|---|---|
| API | ✅ |
| Railway Network | ✅ |
| Train Simulation | ✅ |
| Occupancy & Signaling | ✅ |
| Conflict Detection | ✅ |
| ML Prediction | ✅ |
| AI Optimization | ✅ |
| Safety Validation | ✅ |
| Benchmark Analytics | ✅ |
| Explainable AI | ✅ |
| Control Center | ✅ |
| End-to-End Integration | ✅ |

---

# 🔌 REST & WebSocket API

| Module | Method | Endpoint | Purpose |
|---|---|---|---|
| System | `GET` | `/api/health` | Complete subsystem health |
| Infrastructure | `GET` | `/api/network` | Railway topology |
| Infrastructure | `GET` | `/api/stations` | Station data |
| Infrastructure | `GET` | `/api/sections` | Section data |
| Infrastructure | `GET` | `/api/tracks` | Track data |
| Infrastructure | `GET` | `/api/trains` | Train data |
| Simulation | `POST` | `/api/simulation/start` | Start simulation |
| Simulation | `POST` | `/api/simulation/pause` | Pause simulation |
| Simulation | `POST` | `/api/simulation/step` | Advance simulation |
| Simulation | `POST` | `/api/simulation/reset` | Reset simulation |
| Simulation | `GET` | `/ws/simulation` | 2 Hz WebSocket telemetry |
| Conflicts | `GET` | `/api/conflicts/active` | Active conflicts |
| ML | `POST` | `/api/ml/predict-delay` | Predict delay |
| ML | `GET` | `/api/ml/model-info` | Model metadata |
| Optimization | `POST` | `/api/optimization/optimize` | Optimize dispatch |
| Safety | `POST` | `/api/safety/validate` | Validate dispatch plan |
| Safety | `POST` | `/api/safety/emergency` | Emergency stop |
| Analytics | `POST` | `/api/analytics/run` | Run benchmark |
| Analytics | `GET` | `/api/analytics/compare/{id}` | Compare results |
| Analytics | `GET` | `/api/analytics/export/{id}` | Export results |
| Explainability | `GET` | `/api/explainability/latest` | Latest AI explanation |
| Explainability | `POST` | `/api/explainability/feedback` | Controller feedback |
| Control | `POST` | `/api/control/scenario/load` | Load scenario |
| Control | `POST` | `/api/control/override` | Manual override |
| Control | `POST` | `/api/control/emergency` | Inject incident |
| Control | `POST` | `/api/control/emergency/{id}/mitigate` | Mitigate incident |
| Control | `POST` | `/api/control/demo/start` | Start demo |
| Control | `POST` | `/api/control/demo/step` | Advance demo |

📖 Complete API documentation: [`docs/api.md`](docs/api.md)

---

# 📚 Documentation

The repository contains a complete technical documentation suite.

| Document | Description |
|---|---|
| [`docs/setup.md`](docs/setup.md) | Installation and troubleshooting |
| [`docs/architecture.md`](docs/architecture.md) | Architecture and data flow |
| [`docs/methodology.md`](docs/methodology.md) | Mathematical methodology |
| [`docs/api.md`](docs/api.md) | REST & WebSocket API |
| [`docs/ml.md`](docs/ml.md) | ML model and features |
| [`docs/optimization.md`](docs/optimization.md) | Optimization methodology |
| [`docs/safety.md`](docs/safety.md) | Safety validation and emergency handling |
| [`docs/analytics.md`](docs/analytics.md) | Benchmark methodology |
| [`docs/demo.md`](docs/demo.md) | Demo and viva presentation guide |

---

# 🎬 Demonstration Flow

For a live project demonstration:

```text
1. 🚀 Start Backend
       ↓
2. 🌐 Start Frontend
       ↓
3. 🗺️ Open Control Center
       ↓
4. 🚆 Show Network & Train State
       ↓
5. 📡 Start Simulation
       ↓
6. 🔍 Show Conflict Detection
       ↓
7. 🤖 Show ML Delay Prediction
       ↓
8. 🧠 Run AI Optimization
       ↓
9. 🛡️ Demonstrate Safety Validation
       ↓
10. 🚨 Inject Emergency
       ↓
11. 🧯 Run AI Mitigation
       ↓
12. 📊 Show AI vs Traditional Results
```

---

# 📈 Project Highlights

```text
                🚆 AI TRAIN TRAFFIC CONTROL
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   📡 SIMULATION       🤖 MACHINE           🧠 AI
   & TELEMETRY         LEARNING          OPTIMIZATION
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  🔎 EXPLAINABLE AI
                           │
                           ▼
                  🛡️ SAFETY GATE
                           │
                           ▼
                  👨‍✈️ HUMAN CONTROL
                           │
                           ▼
                  📊 BENCHMARKING
```

### Current Project Metrics

| Metric | Value |
|---|---:|
| 🧪 Automated Tests | **120 / 120 Passing** |
| 🤖 ML Training Samples | **6,500** |
| 🔢 ML Features | **15** |
| 📈 Reported ML R² | **≈ 0.94** |
| 🛡️ Formal Safety Rules | **9** |
| 📊 Benchmark Scenarios | **6** |
| 🚆 Seeded Trains | **12** |
| 🚉 Seeded Stations | **5** |
| 🛤️ Simulated Sections | **7** |
| 🛤️ Directional Tracks | **14** |

---

# 🔮 Future Enhancements

Potential future extensions include:

- 🌐 Integration with larger railway network simulations
- 🧠 More advanced optimization algorithms
- 📈 Real-world historical delay datasets
- 🔔 Advanced alert and notification systems
- ☁️ Cloud deployment
- 📊 Advanced operational analytics
- 🔐 Role-based access control
- 🗺️ Larger interactive railway maps
- 🧪 Hardware-in-the-loop research environments
- 🌍 Multi-corridor simulation

---

# ⚠️ Disclaimer

This software is an **academic simulation and AI decision-support prototype** developed for educational and scientific research.

It is **not certified for**:

- Physical railway infrastructure control
- Field interlocking systems
- Track circuits
- Signaling equipment
- Locomotive control
- Safety-critical railway operation

All reported performance metrics are generated within simulated environments.

The internal safety-validation engine is an algorithmic software safeguard and **does not replace statutory or certified railway safety systems**, including standards such as CENELEC EN 50126, EN 50128, or EN 50129.

---

# 👨‍💻 Project

### Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control

**Phase 12 — Production Readiness, Deployment, Documentation & Final Integration**

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:2563eb,100:0f172a&height=120&section=footer&animation=fadeIn" alt="Footer"/>
</p>

<p align="center">
  <strong>🚆 Simulate • Predict • Optimize • Validate • Explain</strong>
</p>

<p align="center">
  Built with ❤️ using Python, FastAPI, React, Machine Learning & AI
</p>
