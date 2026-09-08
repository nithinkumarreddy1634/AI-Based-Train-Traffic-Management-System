from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from ..models.railway import (
    Station,
    RailwaySection,
    Track,
    Train,
    TrainSchedule,
    SectionStatus,
    TrackStatus,
    TrainStatus,
)
from ..schemas.railway import (
    StationCreate,
    StationUpdate,
    SectionCreate,
    SectionUpdate,
    TrackCreate,
    TrackUpdate,
    TrainCreate,
    TrainUpdate,
)


class RailwayService:
    """Service layer encapsulating business logic for stations, sections, tracks, trains, and networks."""

    # =========================================================================
    # STATIONS
    # =========================================================================
    @staticmethod
    def get_all_stations(db: Session) -> List[Station]:
        return db.query(Station).order_by(Station.station_code).all()

    @staticmethod
    def get_station_by_id(db: Session, station_id: int) -> Station:
        station = db.query(Station).filter(Station.station_id == station_id).first()
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station with ID {station_id} not found.",
            )
        return station

    @staticmethod
    def create_station(db: Session, data: StationCreate) -> Station:
        existing = db.query(Station).filter(Station.station_code == data.station_code.upper()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Station code '{data.station_code.upper()}' already exists.",
            )
        station = Station(
            station_code=data.station_code.upper(),
            station_name=data.station_name,
            latitude=data.latitude,
            longitude=data.longitude,
            number_of_platforms=data.number_of_platforms,
            status=data.status.upper(),
        )
        db.add(station)
        db.commit()
        db.refresh(station)
        return station

    @staticmethod
    def update_station(db: Session, station_id: int, data: StationUpdate) -> Station:
        station = RailwayService.get_station_by_id(db, station_id)
        if data.station_code:
            existing = (
                db.query(Station)
                .filter(Station.station_code == data.station_code.upper(), Station.station_id != station_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Station code '{data.station_code.upper()}' is already in use.",
                )
            station.station_code = data.station_code.upper()

        if data.station_name is not None:
            station.station_name = data.station_name
        if data.latitude is not None:
            station.latitude = data.latitude
        if data.longitude is not None:
            station.longitude = data.longitude
        if data.number_of_platforms is not None:
            station.number_of_platforms = data.number_of_platforms
        if data.status is not None:
            station.status = data.status.upper()

        db.commit()
        db.refresh(station)
        return station

    @staticmethod
    def delete_station(db: Session, station_id: int) -> None:
        station = RailwayService.get_station_by_id(db, station_id)
        db.delete(station)
        db.commit()

    # =========================================================================
    # SECTIONS
    # =========================================================================
    @staticmethod
    def get_all_sections(db: Session) -> List[Dict[str, Any]]:
        sections = (
            db.query(RailwaySection)
            .options(
                joinedload(RailwaySection.start_station),
                joinedload(RailwaySection.end_station),
                joinedload(RailwaySection.tracks),
            )
            .all()
        )
        result = []
        for s in sections:
            result.append(RailwayService._format_section_response(s))
        return result

    @staticmethod
    def get_section_by_id(db: Session, section_id: int) -> Dict[str, Any]:
        section = (
            db.query(RailwaySection)
            .options(
                joinedload(RailwaySection.start_station),
                joinedload(RailwaySection.end_station),
                joinedload(RailwaySection.tracks),
            )
            .filter(RailwaySection.section_id == section_id)
            .first()
        )
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Railway section with ID {section_id} not found.",
            )
        return RailwayService._format_section_response(section)

    @staticmethod
    def create_section(db: Session, data: SectionCreate) -> Dict[str, Any]:
        # Validate that both stations exist
        RailwayService.get_station_by_id(db, data.start_station_id)
        RailwayService.get_station_by_id(db, data.end_station_id)

        section = RailwaySection(
            section_name=data.section_name,
            start_station_id=data.start_station_id,
            end_station_id=data.end_station_id,
            length_km=data.length_km,
            maximum_speed_kmph=data.maximum_speed_kmph,
            number_of_tracks=data.number_of_tracks,
            status=data.status.upper(),
        )
        db.add(section)
        db.commit()
        db.refresh(section)

        # Create tracks for this section automatically
        for i in range(1, data.number_of_tracks + 1):
            direction = "UP" if i == 1 else ("DOWN" if i == 2 else "BOTH")
            track = Track(
                section_id=section.section_id,
                track_number=i,
                direction=direction,
                maximum_speed=data.maximum_speed_kmph,
                status=TrackStatus.AVAILABLE.value,
            )
            db.add(track)
        db.commit()
        db.refresh(section)

        return RailwayService.get_section_by_id(db, section.section_id)

    @staticmethod
    def update_section(db: Session, section_id: int, data: SectionUpdate) -> Dict[str, Any]:
        section = db.query(RailwaySection).filter(RailwaySection.section_id == section_id).first()
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Railway section with ID {section_id} not found.",
            )

        if data.start_station_id is not None:
            RailwayService.get_station_by_id(db, data.start_station_id)
            section.start_station_id = data.start_station_id
        if data.end_station_id is not None:
            RailwayService.get_station_by_id(db, data.end_station_id)
            section.end_station_id = data.end_station_id

        if section.start_station_id == section.end_station_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_station_id and end_station_id cannot be the same.",
            )

        if data.section_name is not None:
            section.section_name = data.section_name
        if data.length_km is not None:
            section.length_km = data.length_km
        if data.maximum_speed_kmph is not None:
            section.maximum_speed_kmph = data.maximum_speed_kmph
        if data.number_of_tracks is not None:
            section.number_of_tracks = data.number_of_tracks
        if data.status is not None:
            section.status = data.status.upper()

        db.commit()
        return RailwayService.get_section_by_id(db, section_id)

    @staticmethod
    def delete_section(db: Session, section_id: int) -> None:
        section = db.query(RailwaySection).filter(RailwaySection.section_id == section_id).first()
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Railway section with ID {section_id} not found.",
            )
        db.delete(section)
        db.commit()

    # =========================================================================
    # TRACKS
    # =========================================================================
    @staticmethod
    def get_all_tracks(db: Session) -> List[Dict[str, Any]]:
        tracks = (
            db.query(Track)
            .options(joinedload(Track.section), joinedload(Track.train))
            .all()
        )
        return [RailwayService._format_track_response(t) for t in tracks]

    @staticmethod
    def get_track_by_id(db: Session, track_id: int) -> Dict[str, Any]:
        track = (
            db.query(Track)
            .options(joinedload(Track.section), joinedload(Track.train))
            .filter(Track.track_id == track_id)
            .first()
        )
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track with ID {track_id} not found.",
            )
        return RailwayService._format_track_response(track)

    @staticmethod
    def create_track(db: Session, data: TrackCreate) -> Dict[str, Any]:
        # Validate section existence
        sec = db.query(RailwaySection).filter(RailwaySection.section_id == data.section_id).first()
        if not sec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {data.section_id} does not exist.",
            )

        if data.occupied_by_train:
            train = db.query(Train).filter(Train.train_id == data.occupied_by_train).first()
            if not train:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Train with ID {data.occupied_by_train} not found.",
                )

        track = Track(
            section_id=data.section_id,
            track_number=data.track_number,
            direction=data.direction.upper(),
            maximum_speed=data.maximum_speed,
            status=data.status.upper(),
            occupied_by_train=data.occupied_by_train,
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        return RailwayService.get_track_by_id(db, track.track_id)

    @staticmethod
    def update_track(db: Session, track_id: int, data: TrackUpdate) -> Dict[str, Any]:
        track = db.query(Track).filter(Track.track_id == track_id).first()
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track with ID {track_id} not found.",
            )

        if data.section_id is not None:
            sec = db.query(RailwaySection).filter(RailwaySection.section_id == data.section_id).first()
            if not sec:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Section with ID {data.section_id} does not exist.",
                )
            track.section_id = data.section_id

        if data.occupied_by_train is not None:
            if data.occupied_by_train != 0:
                train = db.query(Train).filter(Train.train_id == data.occupied_by_train).first()
                if not train:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Train with ID {data.occupied_by_train} not found.",
                    )
                track.occupied_by_train = data.occupied_by_train
                track.status = TrackStatus.OCCUPIED.value
            else:
                track.occupied_by_train = None
                track.status = TrackStatus.AVAILABLE.value

        if data.track_number is not None:
            track.track_number = data.track_number
        if data.direction is not None:
            track.direction = data.direction.upper()
        if data.maximum_speed is not None:
            track.maximum_speed = data.maximum_speed
        if data.status is not None:
            track.status = data.status.upper()

        db.commit()
        return RailwayService.get_track_by_id(db, track_id)

    # =========================================================================
    # TRAINS
    # =========================================================================
    @staticmethod
    def get_all_trains(
        db: Session,
        train_type: Optional[str] = None,
        priority: Optional[str] = None,
        train_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = db.query(Train).options(
            joinedload(Train.source_station),
            joinedload(Train.destination_station),
            joinedload(Train.current_station),
            joinedload(Train.current_section),
            joinedload(Train.occupied_tracks),
        )

        if train_type:
            query = query.filter(Train.train_type == train_type.upper())
        if priority:
            query = query.filter(Train.priority == priority.upper())
        if train_status:
            query = query.filter(Train.status == train_status.upper())
        if search:
            s_pattern = f"%{search}%"
            query = query.filter(
                (Train.train_number.ilike(s_pattern)) | (Train.train_name.ilike(s_pattern))
            )

        trains = query.order_by(Train.train_id).all()
        return [RailwayService._format_train_response(t) for t in trains]

    @staticmethod
    def get_train_by_id(db: Session, train_id: int) -> Dict[str, Any]:
        train = (
            db.query(Train)
            .options(
                joinedload(Train.source_station),
                joinedload(Train.destination_station),
                joinedload(Train.current_station),
                joinedload(Train.current_section),
                joinedload(Train.occupied_tracks),
                joinedload(Train.schedules).joinedload(TrainSchedule.station),
            )
            .filter(Train.train_id == train_id)
            .first()
        )
        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Train with ID {train_id} not found.",
            )
        return RailwayService._format_train_response(train)

    @staticmethod
    def create_train(db: Session, data: TrainCreate) -> Dict[str, Any]:
        # Validate stations
        RailwayService.get_station_by_id(db, data.source_station_id)
        RailwayService.get_station_by_id(db, data.destination_station_id)

        if data.current_station_id:
            RailwayService.get_station_by_id(db, data.current_station_id)
        if data.current_section_id:
            db_sec = db.query(RailwaySection).filter(RailwaySection.section_id == data.current_section_id).first()
            if not db_sec:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Current section ID {data.current_section_id} does not exist.",
                )

        existing = db.query(Train).filter(Train.train_number == data.train_number.upper()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Train number '{data.train_number.upper()}' already exists.",
            )

        train = Train(
            train_number=data.train_number.upper(),
            train_name=data.train_name,
            train_type=data.train_type.upper(),
            priority=data.priority.upper(),
            source_station_id=data.source_station_id,
            destination_station_id=data.destination_station_id,
            current_station_id=data.current_station_id,
            current_section_id=data.current_section_id,
            current_position_km=data.current_position_km,
            speed_kmph=data.speed_kmph,
            direction=data.direction.upper(),
            status=data.status.upper(),
            scheduled_departure=data.scheduled_departure,
            scheduled_arrival=data.scheduled_arrival,
            actual_departure=data.actual_departure,
            actual_arrival=data.actual_arrival,
            current_delay_minutes=data.current_delay_minutes,
        )
        db.add(train)
        db.commit()
        db.refresh(train)

        return RailwayService.get_train_by_id(db, train.train_id)

    @staticmethod
    def update_train(db: Session, train_id: int, data: TrainUpdate) -> Dict[str, Any]:
        train = db.query(Train).filter(Train.train_id == train_id).first()
        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Train with ID {train_id} not found.",
            )

        if data.train_number:
            existing = (
                db.query(Train)
                .filter(Train.train_number == data.train_number.upper(), Train.train_id != train_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Train number '{data.train_number.upper()}' is already in use.",
                )
            train.train_number = data.train_number.upper()

        if data.source_station_id is not None:
            RailwayService.get_station_by_id(db, data.source_station_id)
            train.source_station_id = data.source_station_id

        if data.destination_station_id is not None:
            RailwayService.get_station_by_id(db, data.destination_station_id)
            train.destination_station_id = data.destination_station_id

        if train.source_station_id == train.destination_station_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_station_id and destination_station_id cannot be the same.",
            )

        if data.current_station_id is not None:
            if data.current_station_id != 0:
                RailwayService.get_station_by_id(db, data.current_station_id)
                train.current_station_id = data.current_station_id
            else:
                train.current_station_id = None

        if data.current_section_id is not None:
            if data.current_section_id != 0:
                sec = db.query(RailwaySection).filter(RailwaySection.section_id == data.current_section_id).first()
                if not sec:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
                train.current_section_id = data.current_section_id
            else:
                train.current_section_id = None

        if data.train_name is not None:
            train.train_name = data.train_name
        if data.train_type is not None:
            train.train_type = data.train_type.upper()
        if data.priority is not None:
            train.priority = data.priority.upper()
        if data.current_position_km is not None:
            train.current_position_km = data.current_position_km
        if data.speed_kmph is not None:
            train.speed_kmph = data.speed_kmph
        if data.direction is not None:
            train.direction = data.direction.upper()
        if data.status is not None:
            train.status = data.status.upper()
        if data.scheduled_departure is not None:
            train.scheduled_departure = data.scheduled_departure
        if data.scheduled_arrival is not None:
            train.scheduled_arrival = data.scheduled_arrival
        if data.actual_departure is not None:
            train.actual_departure = data.actual_departure
        if data.actual_arrival is not None:
            train.actual_arrival = data.actual_arrival
        if data.current_delay_minutes is not None:
            train.current_delay_minutes = data.current_delay_minutes

        db.commit()
        return RailwayService.get_train_by_id(db, train_id)

    @staticmethod
    def delete_train(db: Session, train_id: int) -> None:
        train = db.query(Train).filter(Train.train_id == train_id).first()
        if not train:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Train with ID {train_id} not found.",
            )
        # Clear track occupancy first
        tracks = db.query(Track).filter(Track.occupied_by_train == train_id).all()
        for t in tracks:
            t.occupied_by_train = None
            t.status = TrackStatus.AVAILABLE.value
        db.delete(train)
        db.commit()

    # =========================================================================
    # SCHEDULES
    # =========================================================================
    @staticmethod
    def get_all_schedules(db: Session) -> List[Dict[str, Any]]:
        schedules = (
            db.query(TrainSchedule)
            .options(joinedload(TrainSchedule.train), joinedload(TrainSchedule.station))
            .order_by(TrainSchedule.train_id, TrainSchedule.stop_sequence)
            .all()
        )
        result = []
        for sc in schedules:
            result.append({
                "schedule_id": sc.schedule_id,
                "train_id": sc.train_id,
                "train_number": sc.train.train_number if sc.train else "UNKNOWN",
                "train_name": sc.train.train_name if sc.train else "Unknown Train",
                "station_id": sc.station_id,
                "station_code": sc.station.station_code if sc.station else "",
                "station_name": sc.station.station_name if sc.station else "",
                "stop_sequence": sc.stop_sequence,
                "scheduled_arrival": sc.scheduled_arrival,
                "scheduled_departure": sc.scheduled_departure,
                "platform_number": sc.platform_number,
            })
        return result

    # =========================================================================
    # COMPLETE NETWORK GRAPH
    # =========================================================================
    @staticmethod
    def get_complete_network(db: Session) -> Dict[str, Any]:
        stations = db.query(Station).order_by(Station.station_id).all()
        sections = (
            db.query(RailwaySection)
            .options(
                joinedload(RailwaySection.start_station),
                joinedload(RailwaySection.end_station),
                joinedload(RailwaySection.tracks),
            )
            .order_by(RailwaySection.section_id)
            .all()
        )
        tracks = (
            db.query(Track)
            .options(joinedload(Track.section), joinedload(Track.train))
            .order_by(Track.track_id)
            .all()
        )
        trains = (
            db.query(Train)
            .options(
                joinedload(Train.source_station),
                joinedload(Train.destination_station),
                joinedload(Train.current_station),
                joinedload(Train.current_section),
                joinedload(Train.occupied_tracks),
            )
            .order_by(Train.train_id)
            .all()
        )

        connections = []
        for sec in sections:
            connections.append({
                "from_station_id": sec.start_station_id,
                "to_station_id": sec.end_station_id,
                "section_id": sec.section_id,
                "section_name": sec.section_name,
                "length_km": sec.length_km,
                "status": sec.status,
                "tracks_count": sec.number_of_tracks,
            })

        return {
            "stations": [
                {
                    "station_id": s.station_id,
                    "station_code": s.station_code,
                    "station_name": s.station_name,
                    "latitude": s.latitude,
                    "longitude": s.longitude,
                    "number_of_platforms": s.number_of_platforms,
                    "status": s.status,
                }
                for s in stations
            ],
            "sections": [RailwayService._format_section_response(s) for s in sections],
            "tracks": [RailwayService._format_track_response(t) for t in tracks],
            "trains": [RailwayService._format_train_response(tr) for tr in trains],
            "connections": connections,
        }

    # =========================================================================
    # DASHBOARD AGGREGATED STATS
    # =========================================================================
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        total_trains = db.query(Train).count()
        active_trains = db.query(Train).filter(Train.status.in_(["RUNNING", "WAITING", "DELAYED"])).count()
        delayed_trains = db.query(Train).filter((Train.current_delay_minutes > 0) | (Train.status == "DELAYED")).count()
        scheduled_trains = db.query(Train).filter(Train.status == "SCHEDULED").count()

        total_sections = db.query(RailwaySection).count()
        occupied_sections = db.query(RailwaySection).filter(RailwaySection.status == "OCCUPIED").count()
        available_sections = db.query(RailwaySection).filter(RailwaySection.status == "AVAILABLE").count()

        total_tracks = db.query(Track).count()
        occupied_tracks = db.query(Track).filter(Track.occupied_by_train.isnot(None)).count()
        track_utilization = round((occupied_tracks / total_tracks * 100), 1) if total_tracks > 0 else 0.0

        return {
            "total_trains": total_trains,
            "active_trains": active_trains,
            "delayed_trains": delayed_trains,
            "scheduled_trains": scheduled_trains,
            "total_sections": total_sections,
            "occupied_sections": occupied_sections,
            "available_sections": available_sections,
            "total_tracks": total_tracks,
            "occupied_tracks": occupied_tracks,
            "track_utilization_percent": track_utilization,
            "system_status": "NORMAL" if delayed_trains <= 2 else "HEAVY_TRAFFIC",
        }

    # =========================================================================
    # HELPER FORMATTERS
    # =========================================================================
    @staticmethod
    def _format_section_response(sec: RailwaySection) -> Dict[str, Any]:
        return {
            "section_id": sec.section_id,
            "section_name": sec.section_name,
            "start_station_id": sec.start_station_id,
            "start_station_code": sec.start_station.station_code if sec.start_station else None,
            "start_station_name": sec.start_station.station_name if sec.start_station else None,
            "end_station_id": sec.end_station_id,
            "end_station_code": sec.end_station.station_code if sec.end_station else None,
            "end_station_name": sec.end_station.station_name if sec.end_station else None,
            "length_km": sec.length_km,
            "maximum_speed_kmph": sec.maximum_speed_kmph,
            "number_of_tracks": sec.number_of_tracks,
            "status": sec.status,
            "tracks": [RailwayService._format_track_response(t) for t in (sec.tracks or [])],
        }

    @staticmethod
    def _format_track_response(track: Track) -> Dict[str, Any]:
        return {
            "track_id": track.track_id,
            "section_id": track.section_id,
            "track_number": track.track_number,
            "direction": track.direction,
            "maximum_speed": track.maximum_speed,
            "status": track.status,
            "occupied_by_train": track.occupied_by_train,
            "occupied_train_number": track.train.train_number if track.train else None,
            "occupied_train_name": track.train.train_name if track.train else None,
        }

    @staticmethod
    def _format_train_response(train: Train) -> Dict[str, Any]:
        occupied_track_id = train.occupied_tracks[0].track_id if train.occupied_tracks else None
        return {
            "train_id": train.train_id,
            "train_number": train.train_number,
            "train_name": train.train_name,
            "train_type": train.train_type,
            "priority": train.priority,
            "source_station_id": train.source_station_id,
            "source_station_name": train.source_station.station_name if train.source_station else None,
            "destination_station_id": train.destination_station_id,
            "destination_station_name": train.destination_station.station_name if train.destination_station else None,
            "current_station_id": train.current_station_id,
            "current_station_name": train.current_station.station_name if train.current_station else None,
            "current_section_id": train.current_section_id,
            "current_section_name": train.current_section.section_name if train.current_section else None,
            "current_position_km": train.current_position_km,
            "speed_kmph": train.speed_kmph,
            "direction": train.direction,
            "status": train.status,
            "scheduled_departure": train.scheduled_departure,
            "scheduled_arrival": train.scheduled_arrival,
            "actual_departure": train.actual_departure,
            "actual_arrival": train.actual_arrival,
            "current_delay_minutes": train.current_delay_minutes,
            "occupied_track_id": occupied_track_id,
        }
