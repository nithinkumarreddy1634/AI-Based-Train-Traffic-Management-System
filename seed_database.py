"""
Database seeding script for Phase 2: Railway Infrastructure and Train Network.
Run via: python seed_database.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal, init_db
from app.models.railway import (
    Station,
    RailwaySection,
    Track,
    Train,
    TrainSchedule,
    StationStatus,
    SectionStatus,
    TrackDirection,
    TrackStatus,
    TrainType,
    TrainPriority,
    TrainStatus,
)


def seed():
    print("--> Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Check if stations already exist
        existing_stations = db.query(Station).count()
        if existing_stations > 0:
            print(f"[*] Database already contains {existing_stations} stations. Checking complete data...")
        else:
            print("--> Seeding 5 Stations...")
            stations_data = [
                {
                    "station_code": "SEC01",
                    "station_name": "Central Station",
                    "latitude": 28.6139,
                    "longitude": 77.2090,
                    "number_of_platforms": 6,
                    "status": StationStatus.ACTIVE.value,
                },
                {
                    "station_code": "SEC02",
                    "station_name": "North Junction",
                    "latitude": 28.7041,
                    "longitude": 77.1025,
                    "number_of_platforms": 4,
                    "status": StationStatus.ACTIVE.value,
                },
                {
                    "station_code": "SEC03",
                    "station_name": "East Junction",
                    "latitude": 28.6280,
                    "longitude": 77.3000,
                    "number_of_platforms": 4,
                    "status": StationStatus.ACTIVE.value,
                },
                {
                    "station_code": "SEC04",
                    "station_name": "South Station",
                    "latitude": 28.5000,
                    "longitude": 77.2000,
                    "number_of_platforms": 4,
                    "status": StationStatus.ACTIVE.value,
                },
                {
                    "station_code": "SEC05",
                    "station_name": "West Terminal",
                    "latitude": 28.6500,
                    "longitude": 77.0500,
                    "number_of_platforms": 3,
                    "status": StationStatus.ACTIVE.value,
                },
            ]

            for s in stations_data:
                st = Station(**s)
                db.add(st)
            db.commit()
            print(f"[+] Added 5 stations.")

        # Reload stations dict by station_code
        st_map = {s.station_code: s.station_id for s in db.query(Station).all()}

        # 2. Check Sections
        existing_sections = db.query(RailwaySection).count()
        if existing_sections == 0:
            print("--> Seeding 7 Railway Sections...")
            sections_data = [
                {
                    "section_name": "Central - North Junction Line",
                    "start_station_id": st_map["SEC01"],
                    "end_station_id": st_map["SEC02"],
                    "length_km": 18.5,
                    "maximum_speed_kmph": 130.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
                {
                    "section_name": "North Junction - East Junction Line",
                    "start_station_id": st_map["SEC02"],
                    "end_station_id": st_map["SEC03"],
                    "length_km": 24.0,
                    "maximum_speed_kmph": 110.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.AVAILABLE.value,
                },
                {
                    "section_name": "North Junction - West Terminal Line",
                    "start_station_id": st_map["SEC02"],
                    "end_station_id": st_map["SEC05"],
                    "length_km": 14.2,
                    "maximum_speed_kmph": 100.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
                {
                    "section_name": "East Junction - South Station Line",
                    "start_station_id": st_map["SEC03"],
                    "end_station_id": st_map["SEC04"],
                    "length_km": 22.8,
                    "maximum_speed_kmph": 120.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
                {
                    "section_name": "West Terminal - South Station Arc",
                    "start_station_id": st_map["SEC05"],
                    "end_station_id": st_map["SEC04"],
                    "length_km": 28.5,
                    "maximum_speed_kmph": 100.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
                {
                    "section_name": "Central - South Express Trunk",
                    "start_station_id": st_map["SEC01"],
                    "end_station_id": st_map["SEC04"],
                    "length_km": 16.0,
                    "maximum_speed_kmph": 140.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
                {
                    "section_name": "Central - East Junction Connector",
                    "start_station_id": st_map["SEC01"],
                    "end_station_id": st_map["SEC03"],
                    "length_km": 12.5,
                    "maximum_speed_kmph": 110.0,
                    "number_of_tracks": 2,
                    "status": SectionStatus.OCCUPIED.value,
                },
            ]

            for s_data in sections_data:
                sec = RailwaySection(**s_data)
                db.add(sec)
            db.commit()
            print(f"[+] Added 7 railway sections.")

        # Reload sections
        sec_list = db.query(RailwaySection).order_by(RailwaySection.section_id).all()

        # 3. Check Tracks
        existing_tracks = db.query(Track).count()
        if existing_tracks == 0:
            print("--> Seeding 14 Tracks across sections...")
            for sec in sec_list:
                t1 = Track(
                    section_id=sec.section_id,
                    track_number=1,
                    direction=TrackDirection.UP.value,
                    maximum_speed=sec.maximum_speed_kmph,
                    status=TrackStatus.AVAILABLE.value,
                )
                t2 = Track(
                    section_id=sec.section_id,
                    track_number=2,
                    direction=TrackDirection.DOWN.value,
                    maximum_speed=sec.maximum_speed_kmph,
                    status=TrackStatus.AVAILABLE.value,
                )
                db.add(t1)
                db.add(t2)
            db.commit()
            print(f"[+] Added 14 tracks.")

        # 4. Check Trains
        existing_trains = db.query(Train).count()
        if existing_trains == 0:
            print("--> Seeding 12 Sample Trains...")
            trains_data = [
                {
                    "train_number": "EXP-101",
                    "train_name": "Rajdhani Superfast",
                    "train_type": TrainType.EXPRESS.value,
                    "priority": TrainPriority.HIGH.value,
                    "source_station_id": st_map["SEC01"],
                    "destination_station_id": st_map["SEC04"],
                    "current_station_id": None,
                    "current_section_id": sec_list[0].section_id,  # Central-North
                    "current_position_km": 11.2,
                    "speed_kmph": 115.0,
                    "direction": "UP",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "07:30",
                    "scheduled_arrival": "08:45",
                    "actual_departure": "07:30",
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "EXP-102",
                    "train_name": "Vande Bharat Express",
                    "train_type": TrainType.EXPRESS.value,
                    "priority": TrainPriority.HIGH.value,
                    "source_station_id": st_map["SEC04"],
                    "destination_station_id": st_map["SEC01"],
                    "current_station_id": None,
                    "current_section_id": sec_list[3].section_id,  # East-South
                    "current_position_km": 8.5,
                    "speed_kmph": 125.0,
                    "direction": "DOWN",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "08:00",
                    "scheduled_arrival": "09:15",
                    "actual_departure": "08:02",
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "EXP-103",
                    "train_name": "Shatabdi Express",
                    "train_type": TrainType.EXPRESS.value,
                    "priority": TrainPriority.HIGH.value,
                    "source_station_id": st_map["SEC05"],
                    "destination_station_id": st_map["SEC03"],
                    "current_station_id": st_map["SEC02"],
                    "current_section_id": None,
                    "current_position_km": 0.0,
                    "speed_kmph": 0.0,
                    "direction": "UP",
                    "status": TrainStatus.WAITING.value,
                    "scheduled_departure": "08:15",
                    "scheduled_arrival": "09:40",
                    "actual_departure": "08:18",
                    "actual_arrival": None,
                    "current_delay_minutes": 3.0,
                },
                {
                    "train_number": "EXP-104",
                    "train_name": "Duronto Intercity",
                    "train_type": TrainType.EXPRESS.value,
                    "priority": TrainPriority.HIGH.value,
                    "source_station_id": st_map["SEC01"],
                    "destination_station_id": st_map["SEC05"],
                    "current_station_id": st_map["SEC01"],
                    "current_section_id": None,
                    "current_position_km": 0.0,
                    "speed_kmph": 0.0,
                    "direction": "UP",
                    "status": TrainStatus.SCHEDULED.value,
                    "scheduled_departure": "10:00",
                    "scheduled_arrival": "11:15",
                    "actual_departure": None,
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "PAS-201",
                    "train_name": "Capital Corridor Passenger",
                    "train_type": TrainType.PASSENGER.value,
                    "priority": TrainPriority.MEDIUM.value,
                    "source_station_id": st_map["SEC01"],
                    "destination_station_id": st_map["SEC02"],
                    "current_station_id": None,
                    "current_section_id": sec_list[0].section_id,
                    "current_position_km": 4.5,
                    "speed_kmph": 65.0,
                    "direction": "DOWN",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "07:45",
                    "scheduled_arrival": "08:35",
                    "actual_departure": "07:50",
                    "actual_arrival": None,
                    "current_delay_minutes": 5.0,
                },
                {
                    "train_number": "PAS-202",
                    "train_name": "Eastern Junction Passenger",
                    "train_type": TrainType.PASSENGER.value,
                    "priority": TrainPriority.MEDIUM.value,
                    "source_station_id": st_map["SEC03"],
                    "destination_station_id": st_map["SEC04"],
                    "current_station_id": None,
                    "current_section_id": sec_list[3].section_id,
                    "current_position_km": 15.0,
                    "speed_kmph": 45.0,
                    "direction": "UP",
                    "status": TrainStatus.DELAYED.value,
                    "scheduled_departure": "07:15",
                    "scheduled_arrival": "08:20",
                    "actual_departure": "07:33",
                    "actual_arrival": None,
                    "current_delay_minutes": 18.0,
                },
                {
                    "train_number": "PAS-203",
                    "train_name": "North-West Regional",
                    "train_type": TrainType.PASSENGER.value,
                    "priority": TrainPriority.MEDIUM.value,
                    "source_station_id": st_map["SEC02"],
                    "destination_station_id": st_map["SEC05"],
                    "current_station_id": None,
                    "current_section_id": sec_list[2].section_id,
                    "current_position_km": 7.1,
                    "speed_kmph": 70.0,
                    "direction": "UP",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "08:30",
                    "scheduled_arrival": "09:10",
                    "actual_departure": "08:32",
                    "actual_arrival": None,
                    "current_delay_minutes": 2.0,
                },
                {
                    "train_number": "LOC-301",
                    "train_name": "Central Suburban Metro",
                    "train_type": TrainType.LOCAL.value,
                    "priority": TrainPriority.LOW.value,
                    "source_station_id": st_map["SEC01"],
                    "destination_station_id": st_map["SEC03"],
                    "current_station_id": None,
                    "current_section_id": sec_list[6].section_id,
                    "current_position_km": 6.0,
                    "speed_kmph": 50.0,
                    "direction": "UP",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "08:20",
                    "scheduled_arrival": "09:05",
                    "actual_departure": "08:20",
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "LOC-302",
                    "train_name": "South Circular Shuttle",
                    "train_type": TrainType.LOCAL.value,
                    "priority": TrainPriority.LOW.value,
                    "source_station_id": st_map["SEC04"],
                    "destination_station_id": st_map["SEC01"],
                    "current_station_id": st_map["SEC04"],
                    "current_section_id": None,
                    "current_position_km": 0.0,
                    "speed_kmph": 0.0,
                    "direction": "UP",
                    "status": TrainStatus.SCHEDULED.value,
                    "scheduled_departure": "09:30",
                    "scheduled_arrival": "10:20",
                    "actual_departure": None,
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "FRT-401",
                    "train_name": "Steel & Coal Freight",
                    "train_type": TrainType.FREIGHT.value,
                    "priority": TrainPriority.LOW.value,
                    "source_station_id": st_map["SEC03"],
                    "destination_station_id": st_map["SEC05"],
                    "current_station_id": st_map["SEC03"],
                    "current_section_id": None,
                    "current_position_km": 0.0,
                    "speed_kmph": 0.0,
                    "direction": "UP",
                    "status": TrainStatus.WAITING.value,
                    "scheduled_departure": "06:00",
                    "scheduled_arrival": "08:45",
                    "actual_departure": "06:12",
                    "actual_arrival": None,
                    "current_delay_minutes": 12.0,
                },
                {
                    "train_number": "FRT-402",
                    "train_name": "Container Cargo Express",
                    "train_type": TrainType.FREIGHT.value,
                    "priority": TrainPriority.LOW.value,
                    "source_station_id": st_map["SEC01"],
                    "destination_station_id": st_map["SEC04"],
                    "current_station_id": None,
                    "current_section_id": sec_list[5].section_id,
                    "current_position_km": 9.5,
                    "speed_kmph": 62.0,
                    "direction": "UP",
                    "status": TrainStatus.RUNNING.value,
                    "scheduled_departure": "08:00",
                    "scheduled_arrival": "09:15",
                    "actual_departure": "08:00",
                    "actual_arrival": None,
                    "current_delay_minutes": 0.0,
                },
                {
                    "train_number": "FRT-403",
                    "train_name": "Petroleum Tanker Rake",
                    "train_type": TrainType.FREIGHT.value,
                    "priority": TrainPriority.LOW.value,
                    "source_station_id": st_map["SEC05"],
                    "destination_station_id": st_map["SEC04"],
                    "current_station_id": None,
                    "current_section_id": sec_list[4].section_id,
                    "current_position_km": 14.0,
                    "speed_kmph": 0.0,
                    "direction": "DOWN",
                    "status": TrainStatus.STOPPED.value,
                    "scheduled_departure": "06:30",
                    "scheduled_arrival": "08:30",
                    "actual_departure": "06:55",
                    "actual_arrival": None,
                    "current_delay_minutes": 25.0,
                },
            ]

            for tr in trains_data:
                train_obj = Train(**tr)
                db.add(train_obj)
            db.commit()
            print(f"[+] Added 12 trains.")

            # Assign occupied tracks
            all_trains = {t.train_number: t.train_id for t in db.query(Train).all()}
            tracks = db.query(Track).all()

            # Assign tracks for running trains
            # EXP-101 occupies Section 0 (Central-North), Track 1
            t_exp101 = next((t for t in tracks if t.section_id == sec_list[0].section_id and t.track_number == 1), None)
            if t_exp101:
                t_exp101.occupied_by_train = all_trains["EXP-101"]
                t_exp101.status = TrackStatus.OCCUPIED.value

            # PAS-201 occupies Section 0 (Central-North), Track 2
            t_pas201 = next((t for t in tracks if t.section_id == sec_list[0].section_id and t.track_number == 2), None)
            if t_pas201:
                t_pas201.occupied_by_train = all_trains["PAS-201"]
                t_pas201.status = TrackStatus.OCCUPIED.value

            # PAS-203 occupies Section 2 (North-West), Track 1
            t_pas203 = next((t for t in tracks if t.section_id == sec_list[2].section_id and t.track_number == 1), None)
            if t_pas203:
                t_pas203.occupied_by_train = all_trains["PAS-203"]
                t_pas203.status = TrackStatus.OCCUPIED.value

            # EXP-102 occupies Section 3 (East-South), Track 2
            t_exp102 = next((t for t in tracks if t.section_id == sec_list[3].section_id and t.track_number == 2), None)
            if t_exp102:
                t_exp102.occupied_by_train = all_trains["EXP-102"]
                t_exp102.status = TrackStatus.OCCUPIED.value

            # PAS-202 occupies Section 3 (East-South), Track 1
            t_pas202 = next((t for t in tracks if t.section_id == sec_list[3].section_id and t.track_number == 1), None)
            if t_pas202:
                t_pas202.occupied_by_train = all_trains["PAS-202"]
                t_pas202.status = TrackStatus.OCCUPIED.value

            # FRT-403 occupies Section 4 (West-South), Track 2
            t_frt403 = next((t for t in tracks if t.section_id == sec_list[4].section_id and t.track_number == 2), None)
            if t_frt403:
                t_frt403.occupied_by_train = all_trains["FRT-403"]
                t_frt403.status = TrackStatus.OCCUPIED.value

            # FRT-402 occupies Section 5 (Central-South), Track 1
            t_frt402 = next((t for t in tracks if t.section_id == sec_list[5].section_id and t.track_number == 1), None)
            if t_frt402:
                t_frt402.occupied_by_train = all_trains["FRT-402"]
                t_frt402.status = TrackStatus.OCCUPIED.value

            # LOC-301 occupies Section 6 (Central-East), Track 1
            t_loc301 = next((t for t in tracks if t.section_id == sec_list[6].section_id and t.track_number == 1), None)
            if t_loc301:
                t_loc301.occupied_by_train = all_trains["LOC-301"]
                t_loc301.status = TrackStatus.OCCUPIED.value

            db.commit()
            print("[+] Configured track occupancy for running trains.")

        # 5. Check Schedules
        existing_schedules = db.query(TrainSchedule).count()
        if existing_schedules == 0:
            print("--> Seeding Train Timetables & Schedules...")
            train_objs = {t.train_number: t for t in db.query(Train).all()}
            schedules_data = [
                # EXP-101: Central -> North -> East -> South
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "07:30", "platform_number": 1},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC02"], "stop_sequence": 2, "scheduled_arrival": "07:50", "scheduled_departure": "07:53", "platform_number": 2},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 3, "scheduled_arrival": "08:15", "scheduled_departure": "08:18", "platform_number": 1},
                {"train_id": train_objs["EXP-101"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 4, "scheduled_arrival": "08:45", "scheduled_departure": None, "platform_number": 3},

                # EXP-102: South -> East -> Central
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "08:00", "platform_number": 2},
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 2, "scheduled_arrival": "08:30", "scheduled_departure": "08:33", "platform_number": 2},
                {"train_id": train_objs["EXP-102"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 3, "scheduled_arrival": "09:15", "scheduled_departure": None, "platform_number": 4},

                # EXP-103: West -> North -> East
                {"train_id": train_objs["EXP-103"].train_id, "station_id": st_map["SEC05"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "08:15", "platform_number": 1},
                {"train_id": train_objs["EXP-103"].train_id, "station_id": st_map["SEC02"], "stop_sequence": 2, "scheduled_arrival": "08:45", "scheduled_departure": "08:48", "platform_number": 3},
                {"train_id": train_objs["EXP-103"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 3, "scheduled_arrival": "09:40", "scheduled_departure": None, "platform_number": 2},

                # PAS-201: Central -> North
                {"train_id": train_objs["PAS-201"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "07:45", "platform_number": 3},
                {"train_id": train_objs["PAS-201"].train_id, "station_id": st_map["SEC02"], "stop_sequence": 2, "scheduled_arrival": "08:35", "scheduled_departure": None, "platform_number": 1},

                # PAS-202: East -> South
                {"train_id": train_objs["PAS-202"].train_id, "station_id": st_map["SEC03"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "07:15", "platform_number": 3},
                {"train_id": train_objs["PAS-202"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 2, "scheduled_arrival": "08:20", "scheduled_departure": None, "platform_number": 1},

                # FRT-402: Central -> South
                {"train_id": train_objs["FRT-402"].train_id, "station_id": st_map["SEC01"], "stop_sequence": 1, "scheduled_arrival": None, "scheduled_departure": "08:00", "platform_number": 5},
                {"train_id": train_objs["FRT-402"].train_id, "station_id": st_map["SEC04"], "stop_sequence": 2, "scheduled_arrival": "09:15", "scheduled_departure": None, "platform_number": 4},
            ]

            for sc in schedules_data:
                db.add(TrainSchedule(**sc))
            db.commit()
            print(f"[+] Added train schedules.")

        print("--> Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"[!] Seeding error: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
