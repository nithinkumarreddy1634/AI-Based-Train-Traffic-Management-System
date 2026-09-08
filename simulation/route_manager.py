"""
Route Manager for Train Simulation.
Discovers and manages train path sequences across stations and sections dynamically from the network graph.
"""

from typing import List, Dict, Optional, Tuple, Any
from collections import deque


class RouteManager:
    """Manages railway network graph connectivity and determines train section routes."""

    def __init__(self):
        self.stations: Dict[int, Dict[str, Any]] = {}
        self.sections: Dict[int, Dict[str, Any]] = {}
        self.station_connections: Dict[int, List[Tuple[int, int]]] = {}  # station_id -> [(neighbor_station_id, section_id)]
        self.train_routes: Dict[int, List[int]] = {}  # train_id -> list of section_ids in order
        self.train_station_sequences: Dict[int, List[int]] = {}  # train_id -> list of station_ids in order

    def build_network_graph(self, stations: List[Any], sections: List[Any], schedules: List[Any]):
        """Initializes graph nodes and edges from database models."""
        self.stations.clear()
        self.sections.clear()
        self.station_connections.clear()
        self.train_routes.clear()
        self.train_station_sequences.clear()

        for st in stations:
            s_id = st.station_id if hasattr(st, "station_id") else st["station_id"]
            code = st.station_code if hasattr(st, "station_code") else st["station_code"]
            name = st.station_name if hasattr(st, "station_name") else st["station_name"]
            self.stations[s_id] = {"id": s_id, "code": code, "name": name}
            self.station_connections[s_id] = []

        for sec in sections:
            sec_id = sec.section_id if hasattr(sec, "section_id") else sec["section_id"]
            start_id = sec.start_station_id if hasattr(sec, "start_station_id") else sec["start_station_id"]
            end_id = sec.end_station_id if hasattr(sec, "end_station_id") else sec["end_station_id"]
            length = sec.length_km if hasattr(sec, "length_km") else (sec.get("length_km", 20.0) if isinstance(sec, dict) else getattr(sec, "length_km", 20.0))
            if hasattr(sec, "maximum_speed_kmph"):
                speed = sec.maximum_speed_kmph
            elif isinstance(sec, dict):
                speed = sec.get("maximum_speed_kmph") or sec.get("speed_limit", 110.0)
            else:
                speed = getattr(sec, "speed_limit", 110.0)
            name = sec.section_name if hasattr(sec, "section_name") else (sec.get("section_name", f"Section {sec_id}") if isinstance(sec, dict) else getattr(sec, "section_name", f"Section {sec_id}"))

            self.sections[sec_id] = {
                "id": sec_id,
                "name": name,
                "start_station_id": start_id,
                "end_station_id": end_id,
                "length_km": length,
                "max_speed": speed,
            }

            if start_id in self.station_connections:
                self.station_connections[start_id].append((end_id, sec_id))
            if end_id in self.station_connections:
                self.station_connections[end_id].append((start_id, sec_id))

        # Index schedules by train_id
        train_schedules_map: Dict[int, List[Any]] = {}
        for sc in schedules:
            t_id = sc.train_id if hasattr(sc, "train_id") else sc["train_id"]
            train_schedules_map.setdefault(t_id, []).append(sc)

        for t_id, sc_list in train_schedules_map.items():
            sorted_stops = sorted(
                sc_list,
                key=lambda x: x.stop_sequence if hasattr(x, "stop_sequence") else (x.get("stop_sequence") or x.get("stop_order", 0) if isinstance(x, dict) else getattr(x, "stop_order", 0)),
            )
            st_ids = [s.station_id if hasattr(s, "station_id") else s["station_id"] for s in sorted_stops]
            self.train_station_sequences[t_id] = st_ids

    def find_path_between_stations(self, source_id: int, dest_id: int) -> List[int]:
        """BFS pathfinding between two stations returning list of section IDs."""
        if source_id == dest_id:
            return []

        queue = deque([(source_id, [])])
        visited = {source_id}

        while queue:
            curr_station, path = queue.popleft()
            if curr_station == dest_id:
                return path

            for neighbor_id, sec_id in self.station_connections.get(curr_station, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [sec_id]))

        return []

    def get_route_for_train(self, train: Any) -> List[int]:
        """Returns the ordered list of section_ids a train must traverse."""
        train_id = train.train_id if hasattr(train, "train_id") else train["train_id"]
        source_id = train.source_station_id if hasattr(train, "source_station_id") else train["source_station_id"]
        dest_id = train.destination_station_id if hasattr(train, "destination_station_id") else train["destination_station_id"]

        if train_id in self.train_routes:
            return self.train_routes[train_id]

        # If train has scheduled intermediate stops, build path via those stops
        if train_id in self.train_station_sequences and len(self.train_station_sequences[train_id]) > 1:
            full_route: List[int] = []
            stops = self.train_station_sequences[train_id]
            for i in range(len(stops) - 1):
                leg_sections = self.find_path_between_stations(stops[i], stops[i + 1])
                full_route.extend(leg_sections)
            self.train_routes[train_id] = full_route
            return full_route

        # Fallback: direct path from source to destination
        path = self.find_path_between_stations(source_id, dest_id)
        self.train_routes[train_id] = path
        return path

    def get_next_section(self, train: Any, current_section_id: Optional[int]) -> Optional[int]:
        """Determines the next section along the train's route after the current section."""
        route = self.get_route_for_train(train)
        if not route:
            return None

        if current_section_id is None:
            return route[0]

        if current_section_id in route:
            idx = route.index(current_section_id)
            if idx + 1 < len(route):
                return route[idx + 1]

        return None

    def get_ordered_stations_for_train(self, train: Any) -> List[Dict[str, Any]]:
        """Returns the ordered list of station dicts along the train's journey."""
        train_id = train.train_id if hasattr(train, "train_id") else train["train_id"]
        source_id = train.source_station_id if hasattr(train, "source_station_id") else train["source_station_id"]
        dest_id = train.destination_station_id if hasattr(train, "destination_station_id") else train["destination_station_id"]

        st_ids: List[int] = []
        if train_id in self.train_station_sequences and len(self.train_station_sequences[train_id]) > 1:
            st_ids = self.train_station_sequences[train_id]
        else:
            # Reconstruct from route sections
            route = self.get_route_for_train(train)
            curr = source_id
            st_ids = [curr]
            for s_id in route:
                nxt = self.get_destination_station_for_section(s_id, curr)
                st_ids.append(nxt)
                curr = nxt

        result = []
        for sid in st_ids:
            st = self.stations.get(sid)
            if st:
                result.append({
                    "station_id": sid,
                    "station_code": st["code"],
                    "station_name": st["name"],
                })
        return result

    def get_destination_station_for_section(self, section_id: int, origin_station_id: int) -> int:
        """Given a section and the station entering from, returns the exit station."""
        sec = self.sections.get(section_id)
        if not sec:
            return origin_station_id
        if sec["start_station_id"] == origin_station_id:
            return sec["end_station_id"]
        return sec["start_station_id"]


route_manager = RouteManager()



