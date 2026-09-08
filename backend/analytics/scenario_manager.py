"""
Benchmark Scenario Manager.

Provides 6 standardized, repeatable benchmark scenarios for evaluating
AI vs Traditional scheduling under strictly identical initial conditions.
"""

from typing import List, Dict, Any, Optional
import copy


class ScenarioManager:
    """Manages repeatable synthetic and realistic railway traffic benchmark scenarios."""

    def __init__(self):
        self._scenarios: Dict[str, Dict[str, Any]] = {
            "low_traffic": {
                "id": "low_traffic",
                "name": "Low Traffic Density",
                "description": "Corridor operating with light traffic (6 trains), minimal initial delays (0-3 min), ample headway margin.",
                "traffic_density": "low",
                "num_trains": 6,
                "delay_profile": "minimal (0-3 min)",
                "duration_seconds": 3600.0,
            },
            "medium_traffic": {
                "id": "medium_traffic",
                "name": "Medium Traffic Density",
                "description": "Standard busy corridor with 12 trains, balanced mix of Express, Passenger, and Freight, moderate delays (2-8 min).",
                "traffic_density": "medium",
                "num_trains": 12,
                "delay_profile": "moderate (2-8 min)",
                "duration_seconds": 3600.0,
            },
            "heavy_traffic": {
                "id": "heavy_traffic",
                "name": "Heavy Traffic Density",
                "description": "Near-capacity corridor with 24 trains, high track contention, mixed speeds, and cascading delay risks.",
                "traffic_density": "heavy",
                "num_trains": 24,
                "delay_profile": "high (5-15 min)",
                "duration_seconds": 3600.0,
            },
            "high_delay": {
                "id": "high_delay",
                "name": "High Delay Propagation",
                "description": "Severe cascading disruption with 14 trains carrying initial delays from 0 to 25+ minutes requiring active recovery.",
                "traffic_density": "medium-high",
                "num_trains": 14,
                "delay_profile": "extreme (0, 5, 10, 15, 20, 25 min)",
                "duration_seconds": 3600.0,
            },
            "bottleneck_corridor": {
                "id": "bottleneck_corridor",
                "name": "Bottleneck Corridor Constrained",
                "description": "16 trains competing for limited bidirectional tracks across a critical narrow junction throat.",
                "traffic_density": "high",
                "num_trains": 16,
                "delay_profile": "bottleneck-induced (4-12 min)",
                "duration_seconds": 3600.0,
            },
            "mixed_priority": {
                "id": "mixed_priority",
                "name": "Mixed Priority Heterogeneous",
                "description": "15 trains with sharp priority disparity (Superfast Express vs Heavy Freight). Evaluates priority-aware overtaking.",
                "traffic_density": "medium",
                "num_trains": 15,
                "delay_profile": "mixed (1-10 min)",
                "duration_seconds": 3600.0,
            },
            "ai_demo": {
                "id": "ai_demo",
                "name": "AI Throughput Optimization Demo",
                "description": "Comprehensive demonstration corridor with 14 trains, mixed priorities, single-track bottleneck, and cascading delays configured for end-to-end evaluation.",
                "traffic_density": "high",
                "num_trains": 14,
                "delay_profile": "cascading (3-18 min)",
                "duration_seconds": 3600.0,
            },
        }


    def list_scenarios(self, include_demo: bool = False) -> List[Dict[str, Any]]:
        """Returns metadata for benchmark scenarios."""
        if include_demo:
            return list(self._scenarios.values())
        return [s for s in self._scenarios.values() if s["id"] != "ai_demo"]

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata for a specific scenario by id."""
        return self._scenarios.get(scenario_id)

    def create_initial_state(self, scenario_id: str, base_infrastructure: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Constructs a complete, deterministic, deep-copied initial state dictionary.
        Guarantees that Traditional and AI schedulers receive IDENTICAL initial states.
        """
        sc_meta = self.get_scenario(scenario_id)
        if not sc_meta:
            sc_meta = self._scenarios["medium_traffic"]
            scenario_id = "medium_traffic"

        num_trains = sc_meta["num_trains"]

        # Default 5-station corridor topology
        stations = [
            {"station_id": 1, "station_code": "SEC01", "station_name": "Central Station", "platforms": 6, "pos_km": 0.0},
            {"station_id": 2, "station_code": "SEC02", "station_name": "North Junction", "platforms": 4, "pos_km": 18.5},
            {"station_id": 3, "station_code": "SEC03", "station_name": "East Junction", "platforms": 4, "pos_km": 42.5},
            {"station_id": 4, "station_code": "SEC04", "station_name": "South Station", "platforms": 4, "pos_km": 65.3},
            {"station_id": 5, "station_code": "SEC05", "station_name": "West Terminal", "platforms": 3, "pos_km": 32.7},
        ]

        sections = [
            {"section_id": 1, "section_name": "Central - North Junction Line", "start_station_id": 1, "end_station_id": 2, "length_km": 18.5, "speed_limit": 130.0, "tracks_count": 2},
            {"section_id": 2, "section_name": "North Junction - East Junction Line", "start_station_id": 2, "end_station_id": 3, "length_km": 24.0, "speed_limit": 110.0, "tracks_count": 2},
            {"section_id": 3, "section_name": "North Junction - West Terminal Line", "start_station_id": 2, "end_station_id": 5, "length_km": 14.2, "speed_limit": 100.0, "tracks_count": 2},
            {"section_id": 4, "section_name": "East Junction - South Station Line", "start_station_id": 3, "end_station_id": 4, "length_km": 22.8, "speed_limit": 120.0, "tracks_count": 2},
            {"section_id": 5, "section_name": "West Terminal - South Station Arc", "start_station_id": 5, "end_station_id": 4, "length_km": 28.5, "speed_limit": 100.0, "tracks_count": 2},
            {"section_id": 6, "section_name": "Central - South Express Trunk", "start_station_id": 1, "end_station_id": 4, "length_km": 16.0, "speed_limit": 140.0, "tracks_count": 2},
            {"section_id": 7, "section_name": "Central - East Junction Connector", "start_station_id": 1, "end_station_id": 3, "length_km": 12.5, "speed_limit": 110.0, "tracks_count": 2},
        ]

        tracks = []
        track_id_counter = 1
        for sec in sections:
            num_t = 1 if (scenario_id in ("bottleneck_corridor", "ai_demo") and sec["section_id"] in (1, 6)) else sec["tracks_count"]
            for t_num in range(1, num_t + 1):
                direction = "UP" if t_num == 1 else "DOWN"
                if num_t == 1:
                    direction = "BOTH"
                tracks.append({
                    "track_id": track_id_counter,
                    "section_id": sec["section_id"],
                    "track_number": t_num,
                    "direction": direction,
                    "status": "AVAILABLE",
                    "occupied_by_train": None
                })
                track_id_counter += 1

        # Synthesize trains matching scenario parameters
        trains = []
        schedules = []

        train_types = ["EXPRESS", "PASSENGER", "FREIGHT"]
        priorities = ["HIGH", "MEDIUM", "LOW"]

        for i in range(1, num_trains + 1):
            train_id = i
            train_number = f"EXP-{12000 + i}" if i % 2 == 0 else f"FRT-{50000 + i}"

            # Tailor attributes by scenario
            if scenario_id == "mixed_priority":
                # Half high-speed express, half slow freight
                if i % 2 == 1:
                    t_type = "EXPRESS"
                    pri = "HIGH"
                    speed = 120.0
                    delay = float((i * 1.5) % 8.0)
                    src, dst = 1, 4
                else:
                    t_type = "FREIGHT"
                    pri = "LOW"
                    speed = 60.0
                    delay = float((i * 2.0) % 10.0)
                    src, dst = 1, 4
            elif scenario_id == "high_delay":
                t_type = train_types[i % len(train_types)]
                pri = priorities[i % len(priorities)]
                speed = 90.0 if t_type == "EXPRESS" else (75.0 if t_type == "PASSENGER" else 55.0)
                # Staggered delay profile: 0, 5, 10, 15, 20, 25 min
                delay_ladder = [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
                delay = delay_ladder[(i - 1) % len(delay_ladder)]
                src = (i % 3) + 1
                dst = 4 if src != 4 else 1
            elif scenario_id == "bottleneck_corridor":
                t_type = train_types[i % len(train_types)]
                pri = priorities[i % len(priorities)]
                speed = 95.0 if t_type == "EXPRESS" else 65.0
                delay = float(4.0 + (i % 8) * 1.0)
                # Funnel trains through section 1
                src, dst = 1, 2
            elif scenario_id == "heavy_traffic":
                t_type = train_types[i % len(train_types)]
                pri = priorities[i % len(priorities)]
                speed = 100.0 if t_type == "EXPRESS" else (70.0 if t_type == "PASSENGER" else 50.0)
                delay = float(2.0 + (i % 14) * 0.9)
                src = ((i - 1) % 5) + 1
                dst = ((i + 2) % 5) + 1
                if src == dst:
                    dst = (src % 5) + 1
            elif scenario_id == "low_traffic":
                t_type = train_types[i % 2]
                pri = "HIGH" if i <= 3 else "MEDIUM"
                speed = 110.0 if t_type == "EXPRESS" else 80.0
                delay = float(i % 4) * 0.7
                src = 1
                dst = 4
            else:  # medium_traffic
                t_type = train_types[i % len(train_types)]
                pri = priorities[i % len(priorities)]
                speed = 105.0 if t_type == "EXPRESS" else (80.0 if t_type == "PASSENGER" else 60.0)
                delay = float(2.0 + (i % 7) * 0.8)
                src = ((i - 1) % 4) + 1
                dst = 4 if src != 4 else 1

            # Start trains distributed across positions
            direction = "UP" if (i % 2 == 0 or src < dst) else "DOWN"
            train_record = {
                "train_id": train_id,
                "train_number": train_number,
                "train_name": f"Benchmark Train {train_number}",
                "train_type": t_type,
                "priority": pri,
                "source_station_id": src,
                "destination_station_id": dst,
                "current_station_id": src if i > 4 else None,
                "current_section_id": ((i % 5) + 1) if i <= 4 else None,
                "current_position_km": float((i * 4.5) % 25.0) if i <= 4 else 0.0,
                "speed_kmph": speed if i <= 4 else 0.0,
                "direction": direction,
                "status": "RUNNING" if i <= 4 else "SCHEDULED",
                "current_delay_minutes": delay,
            }
            trains.append(train_record)

            # Schedule: src -> intermediate (if any) -> dst
            schedules.append({"train_id": train_id, "station_id": src, "stop_order": 1, "dwell_time_min": 2})
            schedules.append({"train_id": train_id, "station_id": dst, "stop_order": 2, "dwell_time_min": 0})

        state = {
            "scenario_meta": sc_meta,
            "stations": stations,
            "sections": sections,
            "tracks": tracks,
            "trains": trains,
            "schedules": schedules,
            "duration_seconds": sc_meta["duration_seconds"],
        }

        # Deep-copy before returning to ensure pristine state
        return copy.deepcopy(state)

