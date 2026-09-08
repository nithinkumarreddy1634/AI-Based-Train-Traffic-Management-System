# REST & WebSocket API Specification

**Base URL**: `http://127.0.0.1:8000`  
**WebSocket URL**: `ws://127.0.0.1:8000`  
**Interactive Swagger UI**: `http://127.0.0.1:8000/docs`  
**ReDoc Technical UI**: `http://127.0.0.1:8000/redoc`  

---

## 1. System Endpoints

### `GET /`
Returns service root information and phase status.
- **Response**: `200 OK`
```json
{
  "status": "online",
  "message": "AI-Powered Train Traffic Control API is running",
  "project": "Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control",
  "version": "1.0.0",
  "phase": "Phase 12: Production Readiness & Final Integration",
  "docs_url": "/docs"
}
```

### `GET /health`
Probes database connectivity and server uptime.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-09-07T18:30:00Z",
  "uptime_seconds": 124.5,
  "version": "1.0.0",
  "environment": "development"
}
```

### `GET /api/health`
Comprehensive health check probe reporting status across all 8 subsystems.
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "backend": "healthy",
  "database": "healthy",
  "simulation": "ready",
  "ml_model": "loaded",
  "optimizer": "ready",
  "safety": "active",
  "websocket": "ready"
}
```

---

## 2. Railway Infrastructure Endpoints

| Method | Path | Summary |
| :--- | :--- | :--- |
| `GET` | `/api/stations` | List all stations with coordinates and platform counts |
| `GET` | `/api/stations/{id}` | Retrieve station details by ID |
| `POST` | `/api/stations` | Create a new station |
| `PUT` | `/api/stations/{id}` | Update station parameters |
| `DELETE` | `/api/stations/{id}` | Delete a station |
| `GET` | `/api/sections` | List all railway corridor sections with track counts |
| `GET` | `/api/sections/{id}` | Retrieve section details by ID |
| `POST` | `/api/sections` | Create a section connecting station pairs |
| `PUT` | `/api/sections/{id}` | Update section parameters |
| `DELETE` | `/api/sections/{id}` | Delete a section |
| `GET` | `/api/tracks` | List all directional tracks with live train occupancies |
| `GET` | `/api/tracks/{id}` | Retrieve track details by ID |
| `POST` | `/api/tracks` | Add a track to a section |
| `PUT` | `/api/tracks/{id}` | Update track status or train occupancy |
| `GET` | `/api/trains` | List all trains with filtering (`train_type`, `priority`, `status`, `search`) |
| `GET` | `/api/trains/{id}` | Retrieve live train kinematics, route, and delay |
| `POST` | `/api/trains` | Register a new train in the database |
| `PUT` | `/api/trains/{id}` | Update train telemetry or position |
| `DELETE` | `/api/trains/{id}` | Remove a train and clear occupied track |
| `GET` | `/api/network` | Complete topological network graph |
| `GET` | `/api/schedules` | Complete train timetable schedule entries |
| `GET` | `/api/dashboard/stats` | Aggregated operational metrics for dashboard |

---

## 3. Simulation & Real-Time Telemetry Endpoints

### `POST /api/simulation/start`
Starts continuous simulation execution ticker.

### `POST /api/simulation/pause`
Pauses the running simulation clock.

### `POST /api/simulation/step`
Advances the simulation clock by one discrete step ($\Delta t = 1.0\text{ s}$).

### `POST /api/simulation/reset`
Resets train positions, speeds, and delays to initial baseline.

### `POST /api/simulation/speed`
Adjusts simulation clock speed multiplier:
```json
{
  "speed_multiplier": 2.0
}
```

### `GET /api/simulation/status`
Returns simulation clock, running state, active train count, and throughput.

### `WebSocket /ws/train-updates`
Continuous bi-directional WebSocket streaming live train telemetry, track occupancy, conflicts, and ML predictions at 1 Hz.

---

## 4. Machine Learning Delay Prediction Endpoints

### `GET /api/ml/model-info`
Returns model metadata, version, training date, evaluation metrics, and feature importances.
- **Response**: `200 OK`
```json
{
  "status": "Loaded",
  "model_name": "HistGradientBoosting",
  "version": "1.0.0",
  "dataset": "Synthetic",
  "dataset_size": 6500,
  "training_date": "2026-09-07T18:46:13.383331",
  "model_file": "ml/saved_models/delay_prediction_model.pkl",
  "features_used": ["scheduled_duration", "distance_remaining_km", "..."],
  "metrics": {
    "MAE": 0.851,
    "RMSE": 1.118,
    "R2": 0.9782
  }
}
```

### `POST /api/ml/predict-delay`
Performs real-time delay inference:
```json
{
  "train_type": "EXPRESS",
  "priority": "HIGH",
  "scheduled_duration": 60.0,
  "distance_remaining_km": 35.0,
  "current_speed_kmph": 75.0,
  "maximum_speed_kmph": 120.0,
  "current_delay_minutes": 5.0,
  "number_of_stops_remaining": 2,
  "station_dwell_time": 4.0,
  "number_of_trains_in_section": 3,
  "section_utilization": 72.0,
  "traffic_density": 65.0,
  "waiting_train_count": 1,
  "time_of_day": "EVENING",
  "day_type": "WEEKDAY"
}
```

---

## 5. AI Traffic Optimization & Safety Endpoints

### `POST /api/optimization/optimize`
Runs multi-objective solver on active corridor traffic and returns candidate dispatching sequences.

### `POST /api/optimization/apply/{id}`
Submits a recommendation for application to the simulation. **Fails safe** if Phase 8 safety validator rejects the recommendation.

### `POST /api/safety/validate`
Directly verifies a prospective schedule against the 9 formal safety rules.

### `POST /api/safety/emergency`
Triggers or clears an immediate network-wide emergency halt.

---

## 6. Performance Analytics Endpoints

| Method | Path | Summary |
| :--- | :--- | :--- |
| `GET` | `/api/analytics/scenarios` | Catalog of 7 standardized benchmark scenarios |
| `POST` | `/api/analytics/run` | Execute Traditional vs AI benchmark experiment |
| `GET` | `/api/analytics/experiments` | List historical benchmark experiment runs |
| `GET` | `/api/analytics/experiments/{id}` | Detailed experiment report with per-run telemetry |
| `GET` | `/api/analytics/compare/{id}` | Comparative KPIs and composite performance score |
| `GET` | `/api/analytics/metrics/{id}` | Granular train-by-train and time-series metrics |
| `GET` | `/api/analytics/export/{id}` | Export benchmark experiment data as CSV or JSON |

---

## 7. Explainable AI Endpoints

| Method | Path | Summary |
| :--- | :--- | :--- |
| `GET` | `/api/explainability/latest` | Real-time decision explanation for current state |
| `GET` | `/api/explainability/recommendation/{id}` | Full decision explanation payload for a recommendation |
| `GET` | `/api/explainability/history` | Historical log of explainable AI decisions |
| `POST` | `/api/explainability/feedback` | Human controller approval/rejection logging |
| `GET` | `/api/explainability/summary-stats` | Controller adoption rate and safety compliance metrics |

---

## 8. Control Center & Emergency Management Endpoints

| Method | Path | Summary |
| :--- | :--- | :--- |
| `GET` | `/api/control/state` | Unified real-time operational state of network & tracks |
| `GET` | `/api/control/health` | Health and connectivity check of all 8 core subsystems |
| `GET` | `/api/control/scenarios` | Preconfigured scenario library with traffic profiles |
| `POST` | `/api/control/scenario/load` | Load and initialize an operational scenario |
| `POST` | `/api/control/scenario/create` | Synthesize a custom scenario with parameter limits |
| `POST` | `/api/control/emergency` | Inject a simulated emergency into active section/train |
| `GET` | `/api/control/emergency/active` | Query currently active emergency disruptions |
| `POST` | `/api/control/emergency/{id}/mitigate` | Trigger AI recovery plan with headway spacing & safety check |
| `POST` | `/api/control/emergency/{id}/resolve` | Resolve emergency and restore standard operations |
| `POST` | `/api/control/override` | Safety-interlocked manual controller dispatch override (HTTP 422 on safety failure) |
| `GET` | `/api/control/overrides` | Audit history of controller manual interventions |
| `GET` | `/api/control/events` | Circular log of system, safety, and dispatch events |
| `GET` | `/api/control/ai-vs-human` | Comparative efficiency and safety metrics: AI vs Controller |
| `POST` | `/api/control/demo/start` | Launch 12-step automated pipeline demonstration |
| `POST` | `/api/control/demo/step` | Advance demonstration stepper to next phase |
| `POST` | `/api/control/demo/reset` | Reset demonstration session to step 1 |

