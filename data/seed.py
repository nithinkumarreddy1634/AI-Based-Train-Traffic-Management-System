"""
Deterministic Railway Data Generator and Seeder.

Callable via:
    python -m data.seed [--seed 42] [--reset]

Populates:
    - 5 Stations & Interlockings (Central, North, East, South, West)
    - 7 Double-Track Sections connecting corridor pairs
    - 14 Directional Tracks (UP, DOWN, BIDIRECTIONAL)
    - 12 Trains with realistic operational profiles (Express, Passenger, Freight, Local)
    - Timetable Schedules and Stop Sequences
    - 7 Standard Scenarios (Normal, Low, Medium, Heavy, High Delay, Bottleneck, Mixed Priority, AI Demo)
"""

import sys
import os
import argparse
import random
from pathlib import Path

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db, engine
from app.models import Base
from app.models.railway import (
    Station,
    RailwaySection,
    Track,
    Train,
    TrainSchedule,
    Scenario,
    StationStatus,
    SectionStatus,
    TrackDirection,
    TrackStatus,
    TrainType,
    TrainPriority,
    TrainStatus,
)


def seed_database(random_seed: int = 42, reset: bool = False):
    """Deterministically populates the SQLite database with network assets and traffic profiles."""
    random.seed(random_seed)

    if reset:
        print(f"[!] Resetting database tables...")
        Base.metadata.drop_all(bind=engine)
        init_db()
        print(f"[+] Clean database created.")
    else:
        init_db()

    db = SessionLocal()
    try:
        # 1. Stations
        if db.query(Station).count() == 0:
            print("--> Seeding Stations...")
            stations_data = [
                {"station_code": "SEC01", "station_name": "Central Station", "latitude": 28.6139, "longitude": 77.2090, "number_of_platforms": 6, "status": StationStatus.ACTIVE.value},
                {"station_code": "SEC02", "station_name": "North Junction", "latitude": 28.7041, "longitude": 77.1025, "number_of_platforms": 4, "status": StationStatus.ACTIVE.value},
                {"station_code": "SEC03", "station_name": "East Junction", "latitude": 28.6280, "longitude": 77.3000, "number_of_platforms": 4, "status": StationStatus.ACTIVE.value},
                {"station_code": "SEC04", "station_name": "South Station", "latitude": 28.5000, "longitude": 77.2200, "number_of_platforms": 4, "status": StationStatus.ACTIVE.value},
                {"station_code": "SEC05", "station_name": "West Terminal", "latitude": 28.6400, "longitude": 77.0500, "number_of_platforms": 4, "status": StationStatus.ACTIVE.value},
            ]
            for s in stations_data:
                db.add(Station(**s))
            db.commit()
            print(f"[+] Seeded {len(stations_data)} stations.")

        st_map = {s.station_code: s.station_id for s in db.query(Station).all()}

        # 2. Sections
        if db.query(RailwaySection).count() == 0:
            print("--> Seeding Railway Sections...")
            sections_data = [
                {"section_code": "SEC-01", "section_name": "Central - North Corridor", "start_station_id": st_map["SEC01"], "end_station_id": st_map["SEC02"], "length_km": 15.0, "max_speed": 110.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-02", "section_name": "North - East Link", "start_station_id": st_map["SEC02"], "end_station_id": st_map["SEC03"], "length_km": 22.5, "max_speed": 100.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-03", "section_name": "North - West Branch", "start_station_id": st_map["SEC02"], "end_station_id": st_map["SEC05"], "length_km": 12.0, "max_speed": 90.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-04", "section_name": "East - South Mainline", "start_station_id": st_map["SEC03"], "end_station_id": st_map["SEC04"], "length_km": 18.0, "max_speed": 120.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-05", "section_name": "West - South Bypass", "start_station_id": st_map["SEC05"], "end_station_id": st_map["SEC04"], "length_km": 25.0, "max_speed": 80.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-06", "section_name": "Central - South Express Trunk", "start_station_id": st_map["SEC01"], "end_station_id": st_map["SEC04"], "length_km": 14.0, "max_speed": 130.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
                {"section_code": "SEC-07", "section_name": "Central - East Connector", "start_station_id": st_map["SEC01"], "end_station_id": st_map["SEC03"], "length_km": 10.0, "max_speed": 100.0, "number_of_tracks": 2, "status": SectionStatus.NORMAL.value},
            ]
            for sec in sections_data:
                db.add(RailwaySection(**sec))
            db.commit()
            print(f"[+] Seeded {len(sections_data)} sections.")

        sec_list = db.query(RailwaySection).order_by(RailwaySection.section_id).all()

        # 3. Tracks
        if db.query(Track).count() == 0:
            print("--> Seeding Directional Tracks...")
            tracks_data = []
            for sec in sec_list:
                tracks_data.append({"section_id": sec.section_id, "track_number": 1, "track_name": f"{sec.section_code}-UP", "direction": TrackDirection.UP.value, "max_speed": sec.max_speed, "status": TrackStatus.CLEAR.value})
                tracks_data.append({"section_id": sec.section_id, "track_number": 2, "track_name": f"{sec.section_code}-DOWN", "direction": TrackDirection.DOWN.value, "max_speed": sec.max_speed, "status": TrackStatus.CLEAR.value})
            for t in tracks_data:
                db.add(Track(**t))
            db.commit()
            print(f"[+] Seeded {len(tracks_data)} directional tracks.")

        # 4. Trains
        if db.query(Train).count() == 0:
            print("--> Seeding Fleet Trains...")
            trains_data = [
                {"train_number": "EXP-101", "train_name": "Rajdhani Express", "train_type": TrainType.EXPRESS.value, "priority": TrainPriority.HIGH.value, "max_speed": 130.0, "current_speed": 95.0, "current_delay_minutes": 4.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[1].section_id, "start_station_id": st_map["SEC01"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "EXP-102", "train_name": "Shatabdi Express", "train_type": TrainType.EXPRESS.value, "priority": TrainPriority.HIGH.value, "max_speed": 120.0, "current_speed": 85.0, "current_delay_minutes": 1.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[3].section_id, "start_station_id": st_map["SEC04"], "destination_station_id": st_map["SEC01"]},
                {"train_number": "EXP-103", "train_name": "Duronto Express", "train_type": TrainType.EXPRESS.value, "priority": TrainPriority.HIGH.value, "max_speed": 120.0, "current_speed": 0.0, "current_delay_minutes": 0.0, "status": TrainStatus.SCHEDULED.value, "current_station_id": st_map["SEC05"], "start_station_id": st_map["SEC05"], "destination_station_id": st_map["SEC03"]},
                {"train_number": "PAS-201", "train_name": "Intercity Passenger", "train_type": TrainType.PASSENGER.value, "priority": TrainPriority.MEDIUM.value, "max_speed": 90.0, "current_speed": 60.0, "current_delay_minutes": 8.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[0].section_id, "start_station_id": st_map["SEC01"], "destination_station_id": st_map["SEC02"]},
                {"train_number": "PAS-202", "train_name": "Southern Commuter", "train_type": TrainType.PASSENGER.value, "priority": TrainPriority.MEDIUM.value, "max_speed": 90.0, "current_speed": 70.0, "current_delay_minutes": 3.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[3].section_id, "start_station_id": st_map["SEC03"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "PAS-203", "train_name": "Western Shuttle", "train_type": TrainType.PASSENGER.value, "priority": TrainPriority.MEDIUM.value, "max_speed": 80.0, "current_speed": 55.0, "current_delay_minutes": 12.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[2].section_id, "start_station_id": st_map["SEC02"], "destination_station_id": st_map["SEC05"]},
                {"train_number": "LOC-301", "train_name": "Central Ring Metro", "train_type": TrainType.LOCAL.value, "priority": TrainPriority.LOW.value, "max_speed": 70.0, "current_speed": 40.0, "current_delay_minutes": 2.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[6].section_id, "start_station_id": st_map["SEC01"], "destination_station_id": st_map["SEC03"]},
                {"train_number": "LOC-302", "train_name": "East Suburban Local", "train_type": TrainType.LOCAL.value, "priority": TrainPriority.LOW.value, "max_speed": 70.0, "current_speed": 0.0, "current_delay_minutes": 0.0, "status": TrainStatus.SCHEDULED.value, "current_station_id": st_map["SEC03"], "start_station_id": st_map["SEC03"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "FRT-401", "train_name": "Container Freight Alpha", "train_type": TrainType.FREIGHT.value, "priority": TrainPriority.LOW.value, "max_speed": 75.0, "current_speed": 0.0, "current_delay_minutes": 15.0, "status": TrainStatus.WAITING.value, "current_station_id": st_map["SEC02"], "start_station_id": st_map["SEC02"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "FRT-402", "train_name": "Bulk Coal Carrier", "train_type": TrainType.FREIGHT.value, "priority": TrainPriority.LOW.value, "max_speed": 65.0, "current_speed": 50.0, "current_delay_minutes": 22.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[5].section_id, "start_station_id": st_map["SEC01"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "FRT-403", "train_name": "Iron Ore Hopper", "train_type": TrainType.FREIGHT.value, "priority": TrainPriority.LOW.value, "max_speed": 65.0, "current_speed": 45.0, "current_delay_minutes": 7.0, "status": TrainStatus.RUNNING.value, "current_section_id": sec_list[4].section_id, "start_station_id": st_map["SEC05"], "destination_station_id": st_map["SEC04"]},
                {"train_number": "FRT-404", "train_name": "Automobile Express Freight", "train_type": TrainType.FREIGHT.value, "priority": TrainPriority.LOW.value, "max_speed": 75.0, "current_speed": 0.0, "current_delay_minutes": 0.0, "status": TrainStatus.SCHEDULED.value, "current_station_id": st_map["SEC01"], "start_station_id": st_map["SEC01"], "destination_station_id": st_map["SEC05"]},
            ]
            for tr in trains_data:
                db.add(Train(**tr))
            db.commit()
            print(f"[+] Seeded {len(trains_data)} operating fleet trains.")

        # 5. Schedules
        if db.query(TrainSchedule).count() == 0:
            print("--> Seeding Timetable Schedules...")
            train_objs = {t.train_number: t for t in db.query(Train).all()}
            schedules_data = [
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_departure": "07:30", "platform_number": 1},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC02"], "stop_sequence": 2, "scheduled_arrival": "07:50", "scheduled_departure": "07:53", "platform_number": 2},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 3, "scheduled_arrival": "08:15", "scheduled_departure": "08:18", "platform_number": 1},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 4, "scheduled_arrival": "08:45", "platform_number": 3},
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 1, "scheduled_departure": "08:00", "platform_number": 2},
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 2, "scheduled_arrival": "08:30", "scheduled_departure": "08:33", "platform_number": 2},
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 3, "scheduled_arrival": "09:15", "platform_number": 4},
                {"train_id": train_objs["PAS-201"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_departure": "07:45", "platform_number": 3},
                {"train_id": train_objs["PAS-201"].train_id, "station_id": st_map["SEC02"], "stop_sequence": 2, "scheduled_arrival": "08:35", "platform_number": 1},
                {"train_id": train_objs["FRT-402"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_departure": "08:00", "platform_number": 5},
                {"train_id": train_objs["FRT-402"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 2, "scheduled_arrival": "09:15", "platform_number": 4},
            ]
            for sc in schedules_data:
                db.add(TrainSchedule(**sc))
            db.commit()
            print(f"[+] Seeded timetable schedules.")

        # 6. Scenarios in SQLite
        if db.query(Scenario).count() == 0:
            print("--> Seeding Benchmark Scenarios in DB...")
            scenarios_data = [
                {"scenario_id": "low_traffic", "name": "Low Traffic Density", "traffic_density": "low", "num_trains": 6, "delay_profile": "minimal (0-3 min)", "is_custom": False},
                {"scenario_id": "medium_traffic", "name": "Medium Traffic Density", "traffic_density": "medium", "num_trains": 12, "delay_profile": "moderate (2-8 min)", "is_custom": False},
                {"scenario_id": "heavy_traffic", "name": "Heavy Traffic Density", "traffic_density": "heavy", "num_trains": 24, "delay_profile": "high (5-15 min)", "is_custom": False},
                {"scenario_id": "high_delay", "name": "High Delay Propagation", "traffic_density": "medium-high", "num_trains": 14, "delay_profile": "extreme (0 to 25 min)", "is_custom": False},
                {"scenario_id": "bottleneck_corridor", "name": "Bottleneck Corridor Constrained", "traffic_density": "high", "num_trains": 16, "delay_profile": "bottleneck-induced (4-12 min)", "is_custom": False},
                {"scenario_id": "mixed_priority", "name": "Mixed Priority Heterogeneous", "traffic_density": "medium", "num_trains": 15, "delay_profile": "mixed (1-10 min)", "is_custom": False},
                {"scenario_id": "ai_demo", "name": "AI Throughput Optimization Demo", "traffic_density": "high", "num_trains": 14, "delay_profile": "cascading (3-18 min)", "is_custom": False},
            ]
            for sc in scenarios_data:
                db.add(Scenario(**sc))
            db.commit()
            print(f"[+] Seeded {len(scenarios_data)} benchmark scenarios in DB.")

        print("[+] Deterministic seeding complete!")

    except Exception as exc:
        db.rollback()
        print(f"[!] Seeding failed: {exc}")
        raise exc
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Deterministic Railway Data Seeder")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation (default: 42)")
    parser.add_argument("--reset", action="store_true", help="Reset database and drop existing tables before seeding")
    args = parser.parse_args()

    seed_database(random_seed=args.seed, reset=args.reset)


if __name__ == "__main__":
    main()
