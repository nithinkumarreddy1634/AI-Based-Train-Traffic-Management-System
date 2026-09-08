"""
State Manager & Track Reservation System.
Handles dynamic track occupancy, basic safety clearance, and section availability.
"""

from typing import Dict, List, Optional, Any


class StateManager:
    """Maintains in-memory track occupancy and enforces basic safety interlocks."""

    def __init__(self):
        # track_id -> dict with details: {track_id, section_id, track_number, direction, status, occupied_by_train}
        self.tracks: Dict[int, Dict[str, Any]] = {}
        # section_id -> list of track_ids
        self.section_tracks: Dict[int, List[int]] = {}
        # train_id -> currently occupied track_id
        self.train_occupied_track: Dict[int, int] = {}

    def initialize_tracks(self, tracks_data: List[Any]):
        """Populates in-memory tracks from database models."""
        self.tracks.clear()
        self.section_tracks.clear()
        self.train_occupied_track.clear()

        for t in tracks_data:
            t_id = t.track_id if hasattr(t, "track_id") else t["track_id"]
            sec_id = t.section_id if hasattr(t, "section_id") else t["section_id"]
            t_num = t.track_number if hasattr(t, "track_number") else t["track_number"]
            direction = t.direction if hasattr(t, "direction") else t["direction"]
            status = t.status if hasattr(t, "status") else t["status"]
            occ = t.occupied_by_train if hasattr(t, "occupied_by_train") else t.get("occupied_by_train")

            self.tracks[t_id] = {
                "track_id": t_id,
                "section_id": sec_id,
                "track_number": t_num,
                "direction": direction,
                "status": status,
                "occupied_by_train": occ,
            }
            self.section_tracks.setdefault(sec_id, []).append(t_id)
            if occ:
                self.train_occupied_track[occ] = t_id

    def find_available_track_in_section(self, section_id: int, train_direction: str) -> Optional[int]:
        """
        Finds an available track inside a section matching direction (UP, DOWN, or BOTH).
        Basic safety rule: rejects occupied, blocked, or maintenance tracks.
        """
        track_ids = self.section_tracks.get(section_id, [])
        for t_id in track_ids:
            track = self.tracks[t_id]
            if track["status"] == "AVAILABLE" and track["occupied_by_train"] is None:
                if track["direction"] in (train_direction.upper(), "BOTH"):
                    return t_id
        return None

    def reserve_track(self, track_id: int, train_id: int) -> bool:
        """
        Atomically allocates a track to a train.
        Returns True if reservation succeeded, False if occupied/blocked.
        """
        track = self.tracks.get(track_id)
        if not track:
            return False

        if track["status"] != "AVAILABLE" or track["occupied_by_train"] is not None:
            return False

        track["status"] = "OCCUPIED"
        track["occupied_by_train"] = train_id
        self.train_occupied_track[train_id] = track_id
        return True

    def release_track(self, train_id: int) -> Optional[int]:
        """
        Frees whichever track the train was occupying.
        Returns the released track_id or None.
        """
        track_id = self.train_occupied_track.pop(train_id, None)
        if track_id and track_id in self.tracks:
            track = self.tracks[track_id]
            track["status"] = "AVAILABLE"
            track["occupied_by_train"] = None
            return track_id
        return None

    def is_section_occupied(self, section_id: int) -> bool:
        """Checks if any track in the section is occupied."""
        track_ids = self.section_tracks.get(section_id, [])
        for t_id in track_ids:
            if self.tracks[t_id]["occupied_by_train"] is not None:
                return True
        return False

    def get_track_status(self, track_id: int) -> Dict[str, Any]:
        return self.tracks.get(track_id, {})

    def get_occupied_track_for_train(self, train_id: int) -> Optional[int]:
        return self.train_occupied_track.get(train_id)


state_manager = StateManager()

