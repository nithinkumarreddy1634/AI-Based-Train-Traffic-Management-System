"""
Phase 5 Comprehensive Automated Test Suite.
Tests:
- All 5 conflict types (SAME_SECTION, REAR_END, OPPOSITE_DIRECTION, JUNCTION, INSUFFICIENT_HEADWAY)
- Headway kinematics & stopping distance calculation
- Time-to-conflict (TTC) projections
- Deterministic severity and urgency evaluator
- Conflict resolution lifecycle (ACTIVE -> RESOLVED)
- Alert deduplication
- Section congestion analysis & bottleneck scoring
- FastAPI REST endpoints (/api/conflicts, /api/congestion, /api/bottlenecks)
"""

import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient

from conflict_detection.conflict_types import (
    Conflict,
    ConflictType,
    ConflictSeverity,
    ConflictUrgency,
    ConflictStatus,
    CongestionLevel,
)
from conflict_detection.headway import HeadwayCalculator
from conflict_detection.severity import SeverityEvaluator
from conflict_detection.predictor import (
    TimeToConflictPredictor,
    ConflictResolutionTracker,
    AlertDeduplicator,
)
from conflict_detection.conflict_rules import ConflictRulesEngine
from conflict_detection.service import CongestionService
from conflict_detection.detector import ConflictDetector
from backend.app.main import app

client = TestClient(app)


def create_mock_train(
    train_id: int,
    train_number: str,
    position_km: float,
    speed_kmph: float,
    direction: str = "UP",
    section_id: int = 1,
    priority: int = 2,
    status: str = "RUNNING"
):
    """Creates a mock train object matching TrainSimulator attributes."""
    return SimpleNamespace(
        train_id=train_id,
        train_number=train_number,
        train_name=f"Express {train_number}",
        train_type="EXPRESS",
        priority=priority,
        current_position_km=position_km,
        speed_kmph=speed_kmph,
        direction=direction,
        current_section_id=section_id,
        current_station_id=None,
        status=status,
        current_delay_minutes=0.0
    )


class TestHeadwayAndKinematics:
    def test_stopping_distance_calculation(self):
        # 72 km/h = 20 m/s. Decel = 0.6 m/s^2. Reaction = 2.5s.
        # braking = 400 / 1.2 = 333.33m. Reaction = 20 * 2.5 = 50m. Total = 383.33m = 0.383 km.
        dist = HeadwayCalculator.calculate_stopping_distance_km(72.0)
        assert 0.35 <= dist <= 0.42

        # 0 speed has 0 stopping distance
        assert HeadwayCalculator.calculate_stopping_distance_km(0.0) == 0.0

    def test_required_headway_includes_buffer(self):
        req = HeadwayCalculator.calculate_required_headway_km(100.0)
        # Minimum absolute headway is 2.0 km
        assert req >= 2.0

    def test_relative_speed_same_and_opposite_directions(self):
        # Same direction
        v_rel_same = HeadwayCalculator.calculate_relative_speed_kmph(100.0, "UP", 70.0, "UP")
        assert v_rel_same == 30.0

        # Opposite direction
        v_rel_opp = HeadwayCalculator.calculate_relative_speed_kmph(80.0, "UP", 60.0, "DOWN")
        assert v_rel_opp == 140.0


class TestTimeToConflictAndSeverity:
    def test_ttc_projection(self):
        # Separation = 10 km, closing speed = 60 km/h -> TTC = (10/60)*3600 = 600s
        ttc = TimeToConflictPredictor.calculate_ttc_seconds(10.0, 60.0)
        assert ttc == 600.0

        # Diverging or stationary has None
        assert TimeToConflictPredictor.calculate_ttc_seconds(10.0, 0.0) is None

    def test_severity_critical_for_head_on(self):
        sev, urg = SeverityEvaluator.evaluate(
            conflict_type=ConflictType.OPPOSITE_DIRECTION,
            time_to_conflict_seconds=90.0,
            distance_km=2.0,
            is_single_track=True
        )
        assert sev == ConflictSeverity.CRITICAL
        assert urg == ConflictUrgency.IMMEDIATE


class TestConflictRules:
    def test_same_section_conflict(self):
        t1 = create_mock_train(1, "12001", position_km=10.0, speed_kmph=60.0, section_id=1)
        t2 = create_mock_train(2, "12002", position_km=12.0, speed_kmph=50.0, section_id=1)
        sec_info = {"name": "Section A-B", "length_km": 25.0}

        conflict = ConflictRulesEngine.evaluate_same_section(t1, t2, 1, sec_info, is_single_track=True)
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.SAME_SECTION
        assert conflict.train_id_1 == 1
        assert conflict.train_id_2 == 2
        assert "Section A-B" in conflict.explanation

    def test_rear_end_conflict(self):
        # t2 is behind t1 (pos 5 vs 6), both UP, t2 is moving faster (90 vs 40)
        t1 = create_mock_train(1, "12001", position_km=6.0, speed_kmph=40.0, direction="UP")
        t2 = create_mock_train(2, "12002", position_km=5.0, speed_kmph=90.0, direction="UP")
        sec_info = {"name": "Corridor Section", "length_km": 30.0}

        conflict = ConflictRulesEngine.evaluate_rear_end(t1, t2, 1, sec_info)
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.REAR_END
        assert conflict.train_number_1 == "12002"  # following train
        assert conflict.train_number_2 == "12001"  # leading train
        assert "closing on leading" in conflict.explanation

    def test_opposite_direction_conflict(self):
        # t1 moves UP from km 5, t2 moves DOWN from km 8. Closing distance = 3 km
        t1 = create_mock_train(1, "12001", position_km=5.0, speed_kmph=60.0, direction="UP")
        t2 = create_mock_train(2, "12002", position_km=8.0, speed_kmph=60.0, direction="DOWN")
        sec_info = {"name": "Single Line Section", "length_km": 20.0}

        conflict = ConflictRulesEngine.evaluate_opposite_direction(t1, t2, 1, sec_info, is_single_track=True)
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.OPPOSITE_DIRECTION
        assert conflict.severity == ConflictSeverity.CRITICAL

    def test_junction_conflict(self):
        t1 = create_mock_train(1, "12001", position_km=18.0, speed_kmph=60.0, direction="UP", section_id=1)
        t2 = create_mock_train(2, "12002", position_km=22.0, speed_kmph=60.0, direction="DOWN", section_id=2)
        junction_stn = {"name": "Central Junction", "distance_from_source_km": 20.0}

        conflict = ConflictRulesEngine.evaluate_junction(
            train_a=t1,
            train_b=t2,
            junction_station=junction_stn,
            eta_diff_seconds=30.0,
            dist_a_km=2.0,
            dist_b_km=2.0
        )
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.JUNCTION
        assert "Central Junction" in conflict.explanation

    def test_insufficient_headway(self):
        # t1 at 10.0, t2 at 8.8 (gap = 1.2 km < 2.0 km minimum headway), same speed (not fast rear-end closure)
        t1 = create_mock_train(1, "12001", position_km=10.0, speed_kmph=50.0, direction="UP")
        t2 = create_mock_train(2, "12002", position_km=8.8, speed_kmph=50.0, direction="UP")
        sec_info = {"name": "Double Track Section"}

        conflict = ConflictRulesEngine.evaluate_insufficient_headway(t1, t2, 1, sec_info)
        assert conflict is not None
        assert conflict.conflict_type == ConflictType.INSUFFICIENT_HEADWAY
        assert conflict.distance_km == 1.2


class TestResolutionTrackerAndDeduplication:
    def test_lifecycle_resolution(self):
        tracker = ConflictResolutionTracker()
        c1 = Conflict(
            conflict_id="CONF-1",
            conflict_type=ConflictType.SAME_SECTION,
            severity=ConflictSeverity.HIGH,
            urgency=ConflictUrgency.SOON,
            train_id_1=1,
            train_number_1="12001",
            train_id_2=2,
            train_number_2="12002",
            section_id=1,
            distance_km=1.5
        )

        # Tick 1: Detected
        newly_det, newly_res = tracker.update([c1], current_sim_time=100.0)
        assert len(newly_det) == 1
        assert len(tracker.get_all_active()) == 1

        # Tick 2: Resolved (empty current conflict list)
        newly_det, newly_res = tracker.update([], current_sim_time=145.0)
        assert len(newly_res) == 1
        assert len(tracker.get_all_active()) == 0
        assert len(tracker.get_history()) == 1
        assert tracker.get_history()[0]["status"] == "RESOLVED"
        assert tracker.get_history()[0]["duration_seconds"] == 45.0

    def test_alert_deduplication(self):
        dedup = AlertDeduplicator(cooldown_seconds=60.0)
        c1 = Conflict(
            conflict_id="CONF-1",
            conflict_type=ConflictType.INSUFFICIENT_HEADWAY,
            severity=ConflictSeverity.LOW,
            urgency=ConflictUrgency.MONITOR,
            train_id_1=1,
            train_number_1="12001",
            train_id_2=2,
            train_number_2="12002",
            section_id=1
        )

        # 1st emit should succeed
        assert dedup.should_emit(c1, current_sim_time=10.0) is True
        # Immediate subsequent emit during cooldown should be suppressed
        assert dedup.should_emit(c1, current_sim_time=15.0) is False
        # Escalate to CRITICAL -> should emit immediately
        c1.severity = ConflictSeverity.CRITICAL
        assert dedup.should_emit(c1, current_sim_time=20.0) is True


class TestCongestionAndBottlenecks:
    def test_congestion_analysis(self):
        t1 = create_mock_train(1, "12001", 10.0, 0.0, status="WAITING")
        t2 = create_mock_train(2, "12002", 12.0, 0.0, status="WAITING")
        sec_data = {"name": "Test Section", "length_km": 20.0}

        res = CongestionService.analyze_section_congestion(
            section_id=1,
            section_data=sec_data,
            trains_in_section=[t1, t2],
            utilization_percent=85.0,
            max_speed_kmph=100.0
        )
        assert res["congestion_level"] == CongestionLevel.CRITICAL.value
        assert res["waiting_train_count"] == 2
        assert res["speed_drop_percent"] == 100.0

    def test_bottleneck_scoring(self):
        congestion_data = [
            {
                "section_id": 1,
                "section_name": "Section A",
                "active_train_count": 2,
                "waiting_train_count": 2,
                "average_speed_kmph": 20.0,
                "speed_drop_percent": 80.0,
                "utilization_percent": 90.0,
            },
            {
                "section_id": 2,
                "section_name": "Section B",
                "active_train_count": 0,
                "waiting_train_count": 0,
                "average_speed_kmph": 100.0,
                "speed_drop_percent": 0.0,
                "utilization_percent": 10.0,
            }
        ]

        bottlenecks = CongestionService.calculate_bottlenecks(congestion_data)
        assert len(bottlenecks) == 2
        # Section A should be ranked #1
        assert bottlenecks[0]["section_id"] == 1
        assert bottlenecks[0]["bottleneck_score"] > bottlenecks[1]["bottleneck_score"]
        assert bottlenecks[0]["traffic_level"] == "CRITICAL"


class TestConflictRestAPIs:
    def test_api_conflicts_endpoints(self):
        # 1. GET /api/conflicts
        r1 = client.get("/api/conflicts")
        assert r1.status_code == 200
        data1 = r1.json()
        assert "conflicts" in data1
        assert "count" in data1

        # 2. GET /api/conflicts/active
        r2 = client.get("/api/conflicts/active")
        assert r2.status_code == 200
        assert "conflicts" in r2.json()

        # 3. GET /api/conflicts/history
        r3 = client.get("/api/conflicts/history")
        assert r3.status_code == 200
        assert "history" in r3.json()

        # 4. GET /api/congestion
        r4 = client.get("/api/congestion")
        assert r4.status_code == 200
        assert "congestion" in r4.json()

        # 5. GET /api/bottlenecks
        r5 = client.get("/api/bottlenecks")
        assert r5.status_code == 200
        assert "bottlenecks" in r5.json()

