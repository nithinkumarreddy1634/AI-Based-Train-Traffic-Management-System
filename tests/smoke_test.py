"""
System Smoke Test for "AI-Based Train Traffic Management System"

Verifies all 7 core subsystems:
1. Backend
2. Database
3. ML Model
4. Simulation
5. Optimizer
6. Safety Engine
7. APIs
"""

import sys
from pathlib import Path

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import check_database_connection, SessionLocal
from app.models.railway import Station, Train
from simulation import simulation_engine
from ml import delay_prediction_service
from optimization import DEFAULT_OPTIMIZER
from safety import DEFAULT_SAFETY_VALIDATOR

client = TestClient(app)


def run_smoke_test() -> bool:
    results = {}

    # 1. Backend
    try:
        r = client.get("/")
        results["Backend"] = "PASS" if r.status_code == 200 else "FAIL"
    except Exception as e:
        results["Backend"] = f"FAIL ({e})"

    # 2. Database
    try:
        alive = check_database_connection()
        db = SessionLocal()
        station_count = db.query(Station).count()
        train_count = db.query(Train).count()
        db.close()
        results["Database"] = "PASS" if (alive and station_count >= 5 and train_count >= 5) else "FAIL"
    except Exception as e:
        results["Database"] = f"FAIL ({e})"

    # 3. ML Model
    try:
        meta = delay_prediction_service.get_metadata()
        sample_pred = delay_prediction_service.predict({
            "train_type": "EXPRESS",
            "priority": "HIGH",
            "current_delay_minutes": 5.0,
            "scheduled_speed_kmph": 80.0,
            "current_speed_kmph": 75.0,
        })
        results["ML Model"] = "PASS" if (meta and isinstance(sample_pred.get("predicted_delay_minutes"), (int, float))) else "FAIL"
    except Exception as e:
        results["ML Model"] = f"FAIL ({e})"

    # 4. Simulation
    try:
        sim_state = simulation_engine.get_status()
        results["Simulation"] = "PASS" if isinstance(sim_state, dict) and "running" in sim_state else "FAIL"
    except Exception as e:
        results["Simulation"] = f"FAIL ({e})"

    # 5. Optimizer
    try:
        trains_sample = [
            {"train_id": 1, "train_number": "12001", "train_name": "T1", "priority": "HIGH", "current_speed_kmph": 80.0, "current_position_km": 5.0, "status": "RUNNING", "current_delay_minutes": 2.0, "scheduled_departure_time": "10:00"},
            {"train_id": 2, "train_number": "12002", "train_name": "T2", "priority": "NORMAL", "current_speed_kmph": 60.0, "current_position_km": 1.0, "status": "RUNNING", "current_delay_minutes": 5.0, "scheduled_departure_time": "10:05"},
        ]
        opt_res = DEFAULT_OPTIMIZER.optimize_traffic(trains=trains_sample)
        results["Optimizer"] = "PASS" if (opt_res and opt_res.optimization_id) else "FAIL"
    except Exception as e:
        results["Optimizer"] = f"FAIL ({e})"

    # 6. Safety
    try:
        sample_rec = {
            "optimization_id": 1,
            "target_section_id": 1,
            "train_recommendations": [
                {
                    "train_id": 1,
                    "train_number": "12001",
                    "assigned_track_id": 1,
                    "target_speed_kmph": 80.0,
                    "entry_time_sec": 0.0,
                    "exit_time_sec": 120.0,
                    "headway_to_lead_sec": 180.0,
                    "hold_at_station": False,
                }
            ],
        }
        val_res = DEFAULT_SAFETY_VALIDATOR.validate(sample_rec)
        results["Safety"] = "PASS" if (val_res and hasattr(val_res, "is_approved")) else "FAIL"
    except Exception as e:
        results["Safety"] = f"FAIL ({e})"

    # 7. APIs
    try:
        r_health = client.get("/api/health")
        r_net = client.get("/api/network")
        r_trains = client.get("/api/trains")
        results["APIs"] = "PASS" if (r_health.status_code == 200 and r_net.status_code == 200 and r_trains.status_code == 200) else "FAIL"
    except Exception as e:
        results["APIs"] = f"FAIL ({e})"

    # Print clean summary matching specification
    all_pass = all(v == "PASS" for v in results.values())

    print("================================")
    print("SYSTEM SMOKE TEST")
    print("================================")
    print("")
    for name, status in results.items():
        print(f"{name:<14}{status}")
    print("")
    print(f"RESULT: {'PASS' if all_pass else 'FAIL'}")
    print("================================")

    return all_pass


def test_system_smoke():
    """Pytest wrapper for system smoke test."""
    assert run_smoke_test() is True


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
