/**
 * Mock Data Repository for Standalone & Netlify Demonstration
 * Ensures 100% interactive responsiveness and visual richness even without active local backend.
 */

export const MOCK_STATIONS = [
  { id: 1, station_code: 'SEC01', station_name: 'Central Station', latitude: 28.6139, longitude: 77.2090, number_of_platforms: 6, status: 'ACTIVE' },
  { id: 2, station_code: 'SEC02', station_name: 'North Junction', latitude: 28.7041, longitude: 77.1025, number_of_platforms: 4, status: 'ACTIVE' },
  { id: 3, station_code: 'SEC03', station_name: 'East Junction', latitude: 28.6280, longitude: 77.3000, number_of_platforms: 4, status: 'ACTIVE' },
  { id: 4, station_code: 'SEC04', station_name: 'South Station', latitude: 28.5355, longitude: 77.2410, number_of_platforms: 4, status: 'ACTIVE' },
  { id: 5, station_code: 'SEC05', station_name: 'West Terminal', latitude: 28.6353, longitude: 77.0850, number_of_platforms: 3, status: 'ACTIVE' }
];

export const MOCK_SECTIONS = [
  { id: 1, section_code: 'SEC-01-02', name: 'Central - North Corridor', start_station_id: 1, end_station_id: 2, length_km: 12.5, max_speed_kmh: 110, total_tracks: 2, status: 'OPTIMAL', capacity: 6 },
  { id: 2, section_code: 'SEC-01-03', name: 'Central - East Bottleneck', start_station_id: 1, end_station_id: 3, length_km: 9.8, max_speed_kmh: 80, total_tracks: 2, status: 'CONGESTED', capacity: 4 },
  { id: 3, section_code: 'SEC-01-04', name: 'Central - South Mainline', start_station_id: 1, end_station_id: 4, length_km: 14.2, max_speed_kmh: 130, total_tracks: 2, status: 'OPTIMAL', capacity: 8 },
  { id: 4, section_code: 'SEC-01-05', name: 'Central - West Link', start_station_id: 1, end_station_id: 5, length_km: 11.0, max_speed_kmh: 90, total_tracks: 2, status: 'OPTIMAL', capacity: 5 },
  { id: 5, section_code: 'SEC-02-05', name: 'North - West Orbital', start_station_id: 2, end_station_id: 5, length_km: 8.5, max_speed_kmh: 75, total_tracks: 2, status: 'OPTIMAL', capacity: 4 },
  { id: 6, section_code: 'SEC-03-04', name: 'East - South Chord', start_station_id: 3, end_station_id: 4, length_km: 10.3, max_speed_kmh: 85, total_tracks: 2, status: 'OPTIMAL', capacity: 5 },
  { id: 7, section_code: 'SEC-02-03', name: 'North - East Crossway', start_station_id: 2, end_station_id: 3, length_km: 15.1, max_speed_kmh: 95, total_tracks: 2, status: 'OPTIMAL', capacity: 5 }
];

export const MOCK_TRACKS = [
  { id: 1, track_number: 'TRK-01-UP', section_id: 1, direction: 'UP', track_type: 'MAIN', max_speed_kmh: 110, length_km: 12.5, status: 'OCCUPIED' },
  { id: 2, track_number: 'TRK-01-DN', section_id: 1, direction: 'DOWN', track_type: 'MAIN', max_speed_kmh: 110, length_km: 12.5, status: 'CLEAR' },
  { id: 3, track_number: 'TRK-02-UP', section_id: 2, direction: 'UP', track_type: 'MAIN', max_speed_kmh: 80, length_km: 9.8, status: 'CONGESTED' },
  { id: 4, track_number: 'TRK-02-DN', section_id: 2, direction: 'DOWN', track_type: 'MAIN', max_speed_kmh: 80, length_km: 9.8, status: 'OCCUPIED' },
  { id: 5, track_number: 'TRK-03-UP', section_id: 3, direction: 'UP', track_type: 'MAIN', max_speed_kmh: 130, length_km: 14.2, status: 'CLEAR' },
  { id: 6, track_number: 'TRK-03-DN', section_id: 3, direction: 'DOWN', track_type: 'MAIN', max_speed_kmh: 130, length_km: 14.2, status: 'CLEAR' },
  { id: 7, track_number: 'TRK-04-UP', section_id: 4, direction: 'UP', track_type: 'MAIN', max_speed_kmh: 90, length_km: 11.0, status: 'CLEAR' },
  { id: 8, track_number: 'TRK-04-DN', section_id: 4, direction: 'DOWN', track_type: 'MAIN', max_speed_kmh: 90, length_km: 11.0, status: 'OCCUPIED' }
];

export const MOCK_TRAINS = [
  { id: 1, train_number: '12951', train_name: 'Rajdhani Express', train_type: 'EXPRESS', priority: 'HIGH', max_speed_kmh: 130, current_speed: 115, status: 'RUNNING', current_section_id: 1, delay_minutes: 2.5, route: 'Central -> North Junction' },
  { id: 2, train_number: '12002', train_name: 'Bhopal Shatabdi', train_type: 'EXPRESS', priority: 'HIGH', max_speed_kmh: 130, current_speed: 122, status: 'RUNNING', current_section_id: 3, delay_minutes: 0.0, route: 'Central -> South Station' },
  { id: 3, train_number: '22436', train_name: 'Vande Bharat Express', train_type: 'EXPRESS', priority: 'HIGH', max_speed_kmh: 140, current_speed: 128, status: 'RUNNING', current_section_id: 1, delay_minutes: 1.0, route: 'Central -> North Junction' },
  { id: 4, train_number: '12260', train_name: 'Duronto Superfast', train_type: 'EXPRESS', priority: 'HIGH', max_speed_kmh: 120, current_speed: 98, status: 'RUNNING', current_section_id: 4, delay_minutes: 4.5, route: 'Central -> West Terminal' },
  { id: 5, train_number: '12414', train_name: 'Intercity Express', train_type: 'PASSENGER', priority: 'MEDIUM', max_speed_kmh: 100, current_speed: 85, status: 'RUNNING', current_section_id: 2, delay_minutes: 8.0, route: 'Central -> East Junction' },
  { id: 6, train_number: '54076', train_name: 'Passenger Special', train_type: 'PASSENGER', priority: 'MEDIUM', max_speed_kmh: 80, current_speed: 65, status: 'WAITING', current_section_id: 2, delay_minutes: 12.0, route: 'East Junction Loop' },
  { id: 7, train_number: '12056', train_name: 'Jan Shatabdi Express', train_type: 'PASSENGER', priority: 'MEDIUM', max_speed_kmh: 110, current_speed: 92, status: 'RUNNING', current_section_id: 3, delay_minutes: 3.5, route: 'South Station -> Central' },
  { id: 8, train_number: '64491', train_name: 'Suburban Commuter 01', train_type: 'LOCAL', priority: 'LOW', max_speed_kmh: 75, current_speed: 55, status: 'RUNNING', current_section_id: 1, delay_minutes: 5.0, route: 'Central -> North Local' },
  { id: 9, train_number: '64492', train_name: 'Suburban Commuter 02', train_type: 'LOCAL', priority: 'LOW', max_speed_kmh: 75, current_speed: 0, status: 'STOPPED', current_section_id: 5, delay_minutes: 6.5, route: 'West Terminal Platform 2' },
  { id: 10, train_number: 'BOXN-88', train_name: 'Container Cargo Express', train_type: 'FREIGHT', priority: 'LOW', max_speed_kmh: 75, current_speed: 60, status: 'RUNNING', current_section_id: 6, delay_minutes: 15.0, route: 'East -> South Freight Line' },
  { id: 11, train_number: 'BTPN-42', train_name: 'Petroleum Bulk Express', train_type: 'FREIGHT', priority: 'LOW', max_speed_kmh: 70, current_speed: 52, status: 'RUNNING', current_section_id: 7, delay_minutes: 18.0, route: 'North -> East Freight Chord' },
  { id: 12, train_number: 'BOBR-19', train_name: 'Coal Rapid Transit', train_type: 'FREIGHT', priority: 'LOW', max_speed_kmh: 70, current_speed: 0, status: 'WAITING', current_section_id: 2, delay_minutes: 22.0, route: 'Central Freight Yard' }
];

export const MOCK_SCHEDULES = MOCK_TRAINS.map(t => ({
  id: t.id,
  train_id: t.id,
  station_id: 1,
  scheduled_arrival: '08:00:00',
  scheduled_departure: '08:15:00',
  actual_arrival: '08:02:00',
  actual_departure: '08:17:30',
  platform_number: 1,
  dwell_time_minutes: 15
}));

export const MOCK_CONTROL_STATE = {
  running: true,
  paused: false,
  simulation_time: '10:45:22',
  speed_multiplier: 1.0,
  active_scenario: 'bottleneck_corridor',
  fleet: {
    total_trains: 12,
    active_trains: 10,
    waiting_trains: 2,
    stopped_trains: 1,
    delayed_trains: 3,
    completed_trains: 4,
    throughput_trains_per_hour: 16.0
  },
  corridor: {
    total_sections: 7,
    occupied_sections: 5,
    free_sections: 2,
    congested_sections: 1,
    active_conflicts: 1
  },
  trains: MOCK_TRAINS,
  conflicts: [
    {
      id: 'CONF-01',
      conflict_type: 'HEADWAY_SPACING',
      severity: 'HIGH',
      section_id: 2,
      section_name: 'Central - East Bottleneck',
      train_1_id: '12414',
      train_2_id: '54076',
      time_to_conflict_sec: 145,
      mitigation_strategy: 'AI Headway Buffer Enforced (Hold Train 54076 by 180s on Passing Loop)',
      safety_validated: true
    }
  ]
};

export const MOCK_HEALTH = {
  status: 'healthy',
  backend: 'healthy',
  database: 'healthy',
  simulation: 'ready',
  ml_model: 'loaded',
  optimizer: 'ready',
  safety: 'active',
  safety_engine: 'active',
  analytics: 'ready',
  explainability: 'ready',
  websocket: 'ready',
  application_version: '1.0.0',
  database_version: 'SQLite 3 (SQLAlchemy 2.0)',
  ml_model_version: 'HistGradientBoosting v1.0.0',
  environment: 'production-ready',
  uptime_seconds: 3600
};

export const MOCK_AI_VS_HUMAN = {
  traditional: {
    throughput_trains_per_hour: 12.0,
    average_delay_minutes: 46.5,
    max_delay_minutes: 85.0,
    safety_violations: 0,
    conflicts_count: 5
  },
  ai_optimized: {
    throughput_trains_per_hour: 16.0,
    average_delay_minutes: 13.6,
    max_delay_minutes: 24.0,
    safety_violations: 0,
    conflicts_count: 0
  },
  improvements: {
    throughput_increase_pct: 33.33,
    delay_reduction_pct: 70.75,
    conflicts_resolved_pct: 100.0,
    overall_performance_score: 52.1
  }
};
