# Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-120%2F120%20Passing%20(100%25)-brightgreen.svg)](#8-automated-testing--quality-assurance)
[![Phase](https://img.shields.io/badge/Status-Phase%2012%20Production%20Ready-success.svg)](#3-system-phases--capabilities)
[![License](https://img.shields.io/badge/License-Academic%20Prototype-lightgrey.svg)](#12-disclaimer--academic-prototype-notice)

> **IMPORTANT DISCLAIMER & PROTOTYPE NOTICE**:  
> This software is an **academic simulation, algorithmic modeling, and decision-support prototype** developed for scientific research into railway section capacity, delay propagation, and scheduling optimization. **It does not interface with safety-critical field signaling, rail interlocking equipment, or directly control physical locomotives.** All train movements, track circuits, and emergency scenarios are strictly simulated within software boundaries. Phase 8 Safety Validation serves as an internal algorithmic gate to guarantee that no unsafe dispatch plan is executed within the simulation environment.

---

## Table of Contents

1. [Problem Statement & Background](#1-problem-statement--background)
2. [Project Objectives](#2-project-objectives)
3. [System Phases & Capabilities](#3-system-phases--capabilities)
4. [End-to-End System Architecture](#4-end-to-end-system-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Repository Structure](#6-repository-structure)
7. [Installation & Setup Guide](#7-installation--setup-guide)
8. [Automated Testing & Quality Assurance](#8-automated-testing--quality-assurance)
9. [REST & WebSocket API Reference](#9-rest--websocket-api-reference)
10. [Documentation Suite](#10-documentation-suite)
11. [Demonstration & Viva Presentation Guide](#11-demonstration--viva-presentation-guide)
12. [Disclaimer & Academic Prototype Notice](#12-disclaimer--academic-prototype-notice)

---

## 1. Problem Statement & Background

Modern railway networks face severe bottleneck challenges in saturated track sections (corridors between major junctions or terminal stations). When unexpected disturbances occur—such as track speed restrictions, prolonged platform dwell times, adverse weather, or locomotive performance deviations—delays cascade non-linearly across the entire section.

Traditional dispatchers rely on static rulebooks, First-Come-First-Served (FCFS) heuristics, or manual experience. In high-density corridors, this often leads to:
* **Artificial Capacity Loss**: Suboptimal loop-line holding of high-priority trains.
* **Reactionary Braking**: Unnecessary stopping before restrictive signals due to lack of predictive headway management.
* **Cascading Knock-on Delays**: Delays on a single train propagating downstream to otherwise on-time trains.
* **Sub-Optimal Section Throughput**: Inability to dynamically exploit minute-level headway margins to clear additional trains safely.

---

## 2. Project Objectives

The primary objective of this project is to develop an intelligent, end-to-end decision-support simulation system that:

1. **Monitors Railway Infrastructure & Fleets**: Tracks block occupancy, station platform dwells, and train kinematics in real time via high-performance REST APIs and WebSocket telemetry.
2. **Predicts Delays using Machine Learning**: Employs an operational ML regression model trained on 15 real-time features to forecast arrival delays before they propagate.
3. **Optimizes Dispatching via Multi-Objective AI**: Dynamically sequences train precedence, selects tracks, and schedules overtakes to maximize section throughput (trains/hour) while minimizing overall delay and passenger waiting time.
4. **Enforces Infallible Formal Safety Validation (Phase 8)**: Validates every proposed dispatch plan against 9 formal railway safety rules before approval, ensuring zero collisions, headway adherence, and emergency halts.
5. **Provides Transparent Explainable AI (Phase 10)**: Delivers clear, deterministic natural-language justifications, feature importance attributions, and candidate trade-off comparisons so traffic controllers understand *why* each decision was recommended.
6. **Empowers Human Traffic Controllers (Phase 11)**: Integrates a unified real-time control room supporting safety-interlocked manual overrides, synthetic emergency disruption handling, and scenario management.
7. **Proves AI Superiority Empirically (Phase 9)**: Evaluates AI against traditional scheduling across 6 standardized benchmark scenarios with identical initial states, computing composite scores, throughput gains, and comprehensive CSV/JSON reports.

---

## 3. System Phases & Capabilities

The project was constructed across 12 distinct, fully integrated engineering phases:

| Phase | Name | Key Deliverables & Capabilities |
| :---: | :--- | :--- |
| **1** | **Foundation & System Setup** | FastAPI backend, SQLite database, SQLAlchemy models, Pydantic schemas, React + Vite frontend scaffold, health probes. |
| **2** | **Network & Train Infrastructure** | Stations, sections, bidirectional tracks, train fleet management, CRUD APIs, synoptic map. |
| **3** | **Kinematic Train Simulation** | Discrete-time physics engine ($v = u + at$, braking curves, dwell times), real-time WebSocket telemetry stream. |
| **4** | **Dynamic Occupancy & Basic Safety** | Block-reservation logic, signal state machines (Green/Double Yellow/Yellow/Red), track clearance verification. |
| **5** | **Conflict Detection & Bottlenecks** | Headway violation detection, opposing movement conflicts, crossing junction hazards, bottleneck queue analysis. |
| **6** | **ML Delay Prediction** | HistGradientBoosting regressor (6,500 synthetic samples, 15 features, $R^2 \approx 0.94$), feature importance scoring. |
| **7** | **AI Traffic Optimization Engine** | Multi-objective dispatch optimizer maximizing throughput and minimizing total delay, penalty-based candidate ranking. |
| **8** | **Formal Safety Validation Engine** | Dedicated 9-rule formal verification gate acting as an infallible filter between the AI optimizer and the simulation. Zero unsafe plans applied. |
| **9** | **AI vs Traditional Evaluation** | Scientific benchmark engine comparing AI against FCFS/timetable dispatch under identical initial conditions across 6 scenarios with composite scoring. |
| **10** | **Explainable AI Decision Engine** | Transparent justifications: feature attribution, calibrated confidence, 4-candidate trade-off table, human controller feedback logging. |
| **11** | **Intelligent Control Center** | Unified operational dashboard, scenario manager, safety-interlocked manual overrides, synthetic emergency injector & mitigation, 12-step automated demo runner. |
| **12** | **Production Readiness & Integration** | Structured logging, centralized error handlers, database seeder, complete documentation suite (`docs/`), 120 automated tests passing (100%). |

---

## 4. End-to-End System Architecture

```text
                                  +-------------------------------------------------------------+
                                  |                 REAL-TIME TRAFFIC STATE                     |
                                  |     (Kinematic Simulation Engine & WebSocket Telemetry)     |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                  CONFLICT DETECTION ENGINE                  |
                                  |      (Headway Spacing, Opposing Movement, Junction Blk)     |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                  ML DELAY PREDICTION ENGINE                 |
                                  |      (HistGradientBoosting, 15 Features, Arrival Delta)     |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                 AI TRAFFIC OPTIMIZATION ENGINE              |
                                  |    (Multi-Objective Solver: Throughput, Delay, Precedence)  |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                  EXPLAINABLE AI DECISION ENGINE             |
                                  |     (Feature Attribution, Calibrated Confidence, Candidates)|
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                 SAFETY VALIDATION ENGINE (GATE)             |
                                  |         (Formal 9-Rule Infallible Compliance Check)         |
                                  +------------------------------+------------------------------+
                                                                 |
                                        +------------------------+------------------------+
                                        |                                                 |
                                [PASS: APPROVED]                                  [FAIL: REJECTED]
                                        |                                                 |
                                        v                                                 v
                      +-----------------------------------+             +-----------------------------------+
                      |      HUMAN CONTROLLER APPROVAL    |             |       FALLBACK DISPATCH RULE      |
                      |   (Approve / Reject / Override)   |             |   (Hold at Signal / Maintain Gap) |
                      +-----------------+-----------------+             +-----------------+-----------------+
                                        |                                                 |
                                        +------------------------+------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                 SIMULATION STATE APPLICATION                |
                                  |      (Speeds, Route Reservations & Motion Step Committed)   |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 v
                                  +-------------------------------------------------------------+
                                  |              PERFORMANCE ANALYTICS & EVALUATION             |
                                  |    (Throughput TPH, Delay Reduction %, Benchmark Export)    |
                                  +-------------------------------------------------------------+
```

---

## 5. Technology Stack

### Backend
* **Python**: 3.14+
* **Framework**: FastAPI 0.110+ (Asynchronous REST API & WebSockets)
* **ASGI Server**: Uvicorn 0.28+
* **Database & ORM**: SQLite with SQLAlchemy 2.0 (Thread-safe session management)
* **Validation & Settings**: Pydantic v2 & Pydantic-Settings
* **Machine Learning**: Scikit-Learn (HistGradientBoostingRegressor), NumPy, Pandas, Joblib
* **Testing**: Pytest 9.1+ with HTTPX TestClient

### Frontend
* **UI Library**: React 18
* **Build Tool & Dev Server**: Vite 5.4
* **Icons**: Lucide React
* **HTTP & WebSocket**: Axios & Native WebSocket Client
* **Styling**: Modern dark-mode responsive dispatch-center CSS design

---

## 6. Repository Structure

```text
.
├── backend/
│   ├── analytics/                   # Phase 9 Benchmark engine, scenarios & metrics
│   ├── app/
│   │   ├── config/                  # Settings, environment & structured logging
│   │   ├── database/                # SQLite engine & database session management
│   │   ├── models/                  # SQLAlchemy ORM models (Stations, Sections, Tracks, Trains)
│   │   ├── routes/                  # 10 modular REST API route controllers
│   │   ├── schemas/                 # Pydantic v2 request/response schemas
│   │   └── services/                # Business logic, telemetry, and health probes
│   ├── control_center/              # Phase 11 Control room, overrides, emergencies, demo
│   ├── explainability/              # Phase 10 Feature attribution, confidence, justifications
│   ├── ml/                          # Phase 6 ML delay prediction model & training pipeline
│   ├── optimization/                # Phase 7 Multi-objective traffic optimizer
│   ├── safety/                      # Phase 8 Formal 9-rule safety validation engine
│   └── requirements.txt             # Python backend dependencies
├── data/
│   ├── sample/                      # Sample seed definitions (stations, sections, trains)
│   ├── generated/                   # Generated evaluation datasets & export logs
│   └── seed.py                      # Idempotent database seeder with CLI flags
├── docs/                            # Comprehensive documentation suite
│   ├── setup.md                     # Complete installation & setup instructions
│   ├── architecture.md              # System architecture & component interaction diagrams
│   ├── methodology.md               # Scientific methodology & mathematical formulations
│   ├── api.md                       # Comprehensive REST & WebSocket API specification
│   ├── ml.md                        # Machine learning delay prediction documentation
│   ├── optimization.md              # Multi-objective optimization formulations & weights
│   ├── safety.md                    # Formal 9-rule safety validation & emergency handling
│   ├── analytics.md                 # Scientific benchmark methodology & metrics
│   └── demo.md                      # 12-step presentation script & viva defense guide
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable UI widgets (Header, Sidebar, Scoreboards)
│   │   ├── pages/                   # 8 full-featured operational dashboard pages
│   │   └── utils/                   # Shared time, delay, speed, and metric formatters
│   ├── package.json                 # Node dependencies & scripts
│   └── vite.config.js               # Vite bundler configuration
├── tests/                           # Complete test suite (120 tests across all 12 phases)
│   ├── test_api.py                  # System health and core API integration tests
│   ├── test_railway.py              # Railway CRUD, network topology, and validation tests
│   ├── test_simulation.py           # Kinematic train physics and WebSocket tests
│   ├── test_phase4.py               # Track occupancy and signaling safety tests
│   ├── test_phase5.py               # Conflict detection and bottleneck analysis tests
│   ├── test_phase6.py               # ML delay prediction regression tests
│   ├── test_phase7.py               # AI traffic optimization tests
│   ├── test_phase8.py               # Formal safety validation engine tests
│   ├── test_phase9.py               # AI vs Traditional benchmark evaluation tests
│   ├── test_phase10.py              # Explainable AI and feature attribution tests
│   ├── test_phase11.py              # Real-time control center, overrides, and emergency tests
│   └── test_phase12_end_to_end.py   # Full 12-step end-to-end integration test
├── .env.example                     # Environment configuration template
├── README.md                        # Primary project documentation
└── requirements.txt                 # Unified root dependencies file
```

---

## 7. Installation & Setup Guide

### Prerequisites
* **Python 3.10+** (Python 3.14 tested and supported)
* **Node.js 18+** and **npm**
* **Git**

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone <repository-url>
cd "Maximizing Section Throughput Using Al- Powered Precise Train Traffic Control"

# Copy environment settings template
copy .env.example .env     # On Windows PowerShell / CMD
# or: cp .env.example .env # On Linux / macOS
```

### Step 2: Set Up Python Virtual Environment & Install Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt
```

### Step 3: Seed Railway Network Database
```powershell
# Populate database with standard 5-station, 7-section, 14-track corridor
python -m data.seed --seed 42 --reset
```
*Outputs: 5 stations, 7 sections, 14 directional tracks, and 12 trains initialized into SQLite.*

### Step 4: Install Frontend Packages
```powershell
cd frontend
npm install
cd ..
```

### Step 5: Launch Backend & Frontend Servers

**Terminal 1 (FastAPI Backend):**
```powershell
.\.venv\Scripts\uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
* Backend API: `http://127.0.0.1:8000`
* Interactive OpenAPI Swagger UI: `http://127.0.0.1:8000/docs`
* Comprehensive Subsystems Health: `http://127.0.0.1:8000/api/health`

**Terminal 2 (Vite React Frontend):**
```powershell
cd frontend
npm run dev
```
* Frontend Dashboard: `http://localhost:5173`

---

## 8. Automated Testing & Quality Assurance

The system maintains a comprehensive test suite of **120 tests** verifying all functional, algorithmic, safety, and integration requirements.

Execute the test suite with:
```powershell
pytest tests/ -v
```

### Test Suite Summary:
```text
============================= test session starts =============================
collected 120 items

tests\test_api.py ....                                                   [  3%]
tests\test_phase10.py .......                                            [  9%]
tests\test_phase11.py .......                                            [ 15%]
tests\test_phase12_end_to_end.py .                                       [ 15%]
tests\test_phase4.py .........                                           [ 23%]
tests\test_phase5.py ...............                                     [ 35%]
tests\test_phase6.py ...........                                         [ 45%]
tests\test_phase7.py .............                                       [ 55%]
tests\test_phase8.py ................                                    [ 69%]
tests\test_phase9.py ..........                                          [ 77%]
tests\test_railway.py .................                                  [ 91%]
tests\test_simulation.py ..........                                      [100%]

====================== 120 passed, 0 failed in 40.12s =========================
```

---

## 9. REST & WebSocket API Reference

The FastAPI backend exposes 10 distinct module route groups. All endpoints return structured JSON with uniform error envelopes and input validation.

| Group | Method & Path | Summary & Purpose |
| :--- | :--- | :--- |
| **System** | `GET /api/health` | Comprehensive health check of all 7 internal subsystems. |
| **Infrastructure** | `GET /api/network` | Complete topological graph of stations, sections, tracks, and trains. |
| **Infrastructure** | `GET /api/stations`, `sections`, `tracks`, `trains` | Complete CRUD operations for all railway physical and fleet entities. |
| **Simulation** | `POST /api/simulation/start`, `pause`, `step`, `reset` | Clock stepping and kinematic train movement controls. |
| **Simulation** | `GET /ws/simulation` | High-frequency WebSocket telemetry broadcast stream (2 Hz). |
| **Conflicts** | `GET /api/conflicts/active` | Live list of headway violations, opposing conflicts, and bottleneck queues. |
| **ML Delays** | `POST /api/ml/predict-delay` | HistGradientBoosting delay prediction based on live features. |
| **ML Delays** | `GET /api/ml/model-info` | Metadata, hyperparameters, feature importance, and validation metrics. |
| **Optimization** | `POST /api/optimization/optimize` | Solves multi-objective train sequencing to maximize throughput. |
| **Safety** | `POST /api/safety/validate` | Validates proposed dispatch plan against 9 statutory safety rules. |
| **Safety** | `POST /api/safety/emergency` | Triggers immediate network-wide or train-specific emergency stop. |
| **Analytics** | `POST /api/analytics/run` | Executes head-to-head AI vs Traditional benchmark simulation run. |
| **Analytics** | `GET /api/analytics/compare/{id}` | Returns comparative KPIs, composite score, and percentage gains. |
| **Analytics** | `GET /api/analytics/export/{id}` | Exports comprehensive benchmark results to CSV or JSON format. |
| **Explainability**| `GET /api/explainability/latest` | Returns natural-language justifications and feature attributions. |
| **Explainability**| `POST /api/explainability/feedback` | Records human traffic controller approval/rejection audit trail. |
| **Control Room** | `POST /api/control/scenario/load` | Initializes standardized scenario (e.g., `ai_demo`, `bottleneck_corridor`). |
| **Control Room** | `POST /api/control/override` | Safety-interlocked manual controller dispatch command (`HOLD`, `SPEED`). |
| **Control Room** | `POST /api/control/emergency` | Injects synthetic incident (`TRACK_BLOCKAGE`, `SIGNAL_FAILURE`). |
| **Control Room** | `POST /api/control/emergency/{id}/mitigate` | Generates and executes AI emergency recovery plan with safety check. |
| **Control Room** | `POST /api/control/demo/start`, `step` | Controls the automated 12-step end-to-end presentation sequence. |

*For complete request schemas, response codes, and query parameters, see [docs/api.md](docs/api.md).*

---

## 10. Documentation Suite

Full technical specifications, mathematical formulations, and user guides are organized in the `docs/` directory:

1. [**Setup & Installation Guide** (`docs/setup.md`)](docs/setup.md): Step-by-step installation, dependency management, `.env` options, and troubleshooting.
2. [**System Architecture** (`docs/architecture.md`)](docs/architecture.md): Architectural design, data flow diagrams, and component interactions across all 11 subsystems.
3. [**Scientific Methodology** (`docs/methodology.md`)](docs/methodology.md): Complete mathematical formulations for kinematics, safety headway, delay propagation, and optimization.
4. [**REST & WebSocket API Specification** (`docs/api.md`)](docs/api.md): Exhaustive API endpoint catalog, JSON payloads, response structures, and error codes.
5. [**Machine Learning Delay Prediction** (`docs/ml.md`)](docs/ml.md): Dataset synthesis, 15 feature descriptions, model selection, training procedure, and feature importance rankings.
6. [**Multi-Objective Optimization Engine** (`docs/optimization.md`)](docs/optimization.md): Optimization formulations, decision variables, constraint definitions, weights, and heuristic search algorithms.
7. [**Formal Safety Validation & Emergencies** (`docs/safety.md`)](docs/safety.md): The 9 formal safety rules, fail-safe architecture, emergency disruption mitigation, and audit logging.
8. [**Performance Analytics & Evaluation** (`docs/analytics.md`)](docs/analytics.md): Benchmark methodology, 6 standard scenarios, statistical metrics, composite score derivation, and export formats.
9. [**Live Presentation & Viva Guide** (`docs/demo.md`)](docs/demo.md): 12-step presentation script, oral defense guide, key metrics, and anticipated committee Q&A.

---

## 11. Demonstration & Viva Presentation Guide

To conduct a live demonstration for an evaluation committee or stakeholder review:

1. **Launch Both Services**: Ensure the FastAPI backend (`http://127.0.0.1:8000`) and Vite frontend (`http://localhost:5173`) are running.
2. **Navigate to Control Center**: Open `http://localhost:5173` and select the **Control Center** tab.
3. **Trigger the 12-Step Demo Runner**: Click the **Start Automated Demo** button on the top banner.
4. **Follow the Script**: Reference [docs/demo.md](docs/demo.md) for the exact talking points, formulas, and visual highlights corresponding to each of the 12 automated steps:
   * **Steps 1–3**: Network topology, initial train positions, and kinematic simulation stepping.
   * **Steps 4–5**: Real-time headway conflict detection and ML delay prediction.
   * **Steps 6–8**: AI multi-objective sequencing, Phase 8 safety validation proof, and explainable AI justifications.
   * **Steps 9–10**: Injecting synthetic emergency (`TRACK_BLOCKAGE`) and triggering AI mitigation plan.
   * **Steps 11–12**: Safety-interlocked controller override demonstration and final AI vs Traditional performance scorecard.

---

## 12. Disclaimer & Academic Prototype Notice

This software is an academic simulation and AI decision-support prototype developed strictly for educational and scientific research purposes. It is **not** certified for, nor capable of, controlling physical railway infrastructure, field interlocking systems, track circuits, or rolling stock locomotives. All performance gains and delay metrics reported by the system are derived within simulated track environments. The internal safety validation engine operates as an algorithmic gate within software memory and does not replace statutory fail-safe railway signaling standards (e.g., CENELEC EN 50126 / EN 50128 / EN 50129).

---

**Developed for the project:**  
*Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control*  
*Phase 12: Production Readiness, Deployment, Documentation & Final Integration*
