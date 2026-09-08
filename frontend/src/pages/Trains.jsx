import React, { useState, useEffect } from 'react';
import {
  Train,
  Search,
  Filter,
  RefreshCw,
  Clock,
  Gauge,
  MapPin,
  GitBranch,
  Radio,
  AlertCircle,
  CheckCircle2,
  X,
  Calendar,
  Layers,
  Sparkles,
} from 'lucide-react';
import { fetchTrains, fetchTrain, fetchSchedules } from '../services/api';

export default function Trains({ simulation }) {
  const [trains, setTrains] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedPriority, setSelectedPriority] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  // Modal / details state
  const [selectedTrain, setSelectedTrain] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [trainsData, schedulesData] = await Promise.all([
        fetchTrains(),
        fetchSchedules(),
      ]);
      setTrains(trainsData);
      setSchedules(schedulesData);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch train fleet.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Merge live simulation data with base fleet data
  const fleet = (simulation?.trains && simulation.trains.length > 0)
    ? simulation.trains
    : trains;

  const openTrainDetails = (train) => {
    setSelectedTrain(train);
    setIsModalOpen(true);
  };

  const closeTrainDetails = () => {
    setSelectedTrain(null);
    setIsModalOpen(false);
  };

  // Filter trains
  const filteredTrains = fleet.filter((t) => {
    const matchesSearch =
      t.train_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.train_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.source_station_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.destination_station_name?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType = selectedType === 'ALL' || t.train_type === selectedType;
    const matchesPriority = selectedPriority === 'ALL' || t.priority === selectedPriority;
    const matchesStatus = selectedStatus === 'ALL' || t.status === selectedStatus;

    return matchesSearch && matchesType && matchesPriority && matchesStatus;
  });

  const getPriorityBadge = (prio) => {
    switch ((prio || '').toUpperCase()) {
      case 'HIGH':
        return <span className="prio-pill prio-high">HIGH</span>;
      case 'MEDIUM':
        return <span className="prio-pill prio-med">MED</span>;
      case 'LOW':
        return <span className="prio-pill prio-low">LOW</span>;
      default:
        return <span className="prio-pill">{prio}</span>;
    }
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'RUNNING':
        return <span className="status-chip chip-occupied"><Radio size={11} /> RUNNING</span>;
      case 'WAITING':
        return <span className="status-chip chip-blocked"><Clock size={11} /> WAITING</span>;
      case 'DELAYED':
        return <span className="status-chip chip-maintenance"><AlertCircle size={11} /> DELAYED</span>;
      case 'SCHEDULED':
        return <span className="status-chip chip-muted"><Calendar size={11} /> SCHEDULED</span>;
      case 'STOPPED':
        return <span className="status-chip chip-blocked"><AlertCircle size={11} /> STOPPED</span>;
      case 'ARRIVED':
        return <span className="status-chip chip-available"><CheckCircle2 size={11} /> ARRIVED</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  const getTypeIconColor = (type) => {
    switch (type) {
      case 'EXPRESS':
        return 'type-tag type-express';
      case 'PASSENGER':
        return 'type-tag type-passenger';
      case 'FREIGHT':
        return 'type-tag type-freight';
      case 'LOCAL':
        return 'type-tag type-local';
      default:
        return 'type-tag';
    }
  };

  const trainSchedules = selectedTrain
    ? schedules.filter((s) => s.train_id === selectedTrain.train_id)
    : [];

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Train Fleet Monitoring & Telemetry</h2>
          <p className="page-subheading">
            Live tracking of speeds, track section occupancy, priorities, and delay status across the active corridor.
          </p>
        </div>
        <div className="header-actions-group">
          <button onClick={loadData} className="secondary-btn" disabled={isLoading} title="Reload Fleet Telemetry">
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
            <span>Refresh Fleet</span>
          </button>
        </div>
      </div>

      {/* Fleet Filter Bar */}
      <div className="filter-controls-panel">
        <div className="search-input-box filter-search">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search train by number, name, origin, or destination..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Type:</label>
          <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)} className="filter-select">
            <option value="ALL">All Types</option>
            <option value="EXPRESS">Express</option>
            <option value="PASSENGER">Passenger</option>
            <option value="LOCAL">Local</option>
            <option value="FREIGHT">Freight</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Priority:</label>
          <select value={selectedPriority} onChange={(e) => setSelectedPriority(e.target.value)} className="filter-select">
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status:</label>
          <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="filter-select">
            <option value="ALL">All Statuses</option>
            <option value="RUNNING">Running</option>
            <option value="WAITING">Waiting</option>
            <option value="DELAYED">Delayed</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="STOPPED">Stopped</option>
            <option value="ARRIVED">Arrived</option>
          </select>
        </div>

        <div className="count-pill">
          {filteredTrains.length} of {trains.length} Trains
        </div>
      </div>

      {/* Train Fleet Table */}
      <div className="table-wrapper-panel">
        <table className="data-table">
          <thead>
            <tr>
              <th>Train No.</th>
              <th>Train Name</th>
              <th>Type</th>
              <th>Priority</th>
              <th>Route (Origin → Dest)</th>
              <th>Current Section / Station</th>
              <th>Speed</th>
              <th>Status</th>
              <th>Delay</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrains.map((t) => {
              const isDelayed = t.current_delay_minutes > 0;
              return (
                <tr key={t.train_id} className="clickable-tr" onClick={() => openTrainDetails(t)}>
                  <td>
                    <span className="train-no-badge">{t.train_number}</span>
                  </td>
                  <td className="font-semibold text-white">{t.train_name}</td>
                  <td>
                    <span className={getTypeIconColor(t.train_type)}>{t.train_type}</span>
                  </td>
                  <td>{getPriorityBadge(t.priority)}</td>
                  <td>
                    <div className="route-cell">
                      <span>{t.source_station_name}</span>
                      <span className="route-arrow">→</span>
                      <span>{t.destination_station_name}</span>
                    </div>
                  </td>
                  <td>
                    {t.current_section_name ? (
                      <div className="progress-cell">
                        <span className="loc-badge">
                          <GitBranch size={11} /> {t.current_section_name} ({Number(t.current_position_km || 0).toFixed(1)} km)
                        </span>
                        <div className="progress-track" title={`${Math.round(t.section_progress_pct || 0)}% of section traversed`}>
                          <div
                            className={`progress-bar-fill ${
                              t.status === 'WAITING'
                                ? 'fill-waiting'
                                : t.status === 'DELAYED'
                                ? 'fill-delayed'
                                : t.status === 'ARRIVED'
                                ? 'fill-arrived'
                                : ''
                            }`}
                            style={{ width: `${Math.min(Math.max(t.section_progress_pct || 0, 4), 100)}%` }}
                          />
                        </div>
                        <div className="progress-meta">
                          <span>{t.direction || 'UP'}</span>
                          <span>{Math.round(t.section_progress_pct || 0)}%</span>
                        </div>
                      </div>
                    ) : t.current_station_name ? (
                      <span className="loc-badge-station">
                        <MapPin size={11} /> {t.current_station_name}
                      </span>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                  <td>
                    <span className="font-mono font-bold text-sky-400">
                      {Number(t.speed_kmph || 0).toFixed(1)} <small className="text-muted">km/h</small>
                    </span>
                  </td>
                  <td>{getStatusBadge(t.status)}</td>
                  <td>
                    {isDelayed ? (
                      <span className="delay-badge">+{t.current_delay_minutes} min</span>
                    ) : (
                      <span className="on-time-badge">On Time</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="details-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        openTrainDetails(t);
                      }}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* TRAIN DETAILS MODAL */}
      {isModalOpen && selectedTrain && (
        <div className="modal-backdrop" onClick={closeTrainDetails}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-row">
                <Train size={24} className="modal-icon" />
                <div>
                  <h3>
                    {selectedTrain.train_number} — {selectedTrain.train_name}
                  </h3>
                  <div className="modal-subtitle-badges">
                    <span className={getTypeIconColor(selectedTrain.train_type)}>{selectedTrain.train_type}</span>
                    {getPriorityBadge(selectedTrain.priority)}
                    {getStatusBadge(selectedTrain.status)}
                  </div>
                </div>
              </div>
              <button className="modal-close-btn" onClick={closeTrainDetails}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              {/* Telemetry Grid */}
              <div className="modal-stats-grid">
                <div className="modal-stat-box">
                  <div className="m-label"><Gauge size={14} /> Current Speed</div>
                  <div className="m-value font-mono">{selectedTrain.speed_kmph} km/h</div>
                </div>

                <div className="modal-stat-box">
                  <div className="m-label"><Clock size={14} /> Current Delay</div>
                  <div className="m-value font-mono text-amber-400">
                    {selectedTrain.current_delay_minutes > 0 ? `+${selectedTrain.current_delay_minutes} min` : '0 min (On Time)'}
                  </div>
                </div>

                <div className="modal-stat-box">
                  <div className="m-label"><Calendar size={14} /> Scheduled Timetable</div>
                  <div className="m-value font-mono text-sm">
                    {selectedTrain.scheduled_departure} Dep → {selectedTrain.scheduled_arrival} Arr
                  </div>
                </div>

                <div className="modal-stat-box">
                  <div className="m-label"><Layers size={14} /> Direction & Track</div>
                  <div className="m-value font-mono">
                    {selectedTrain.direction} Direction
                  </div>
                </div>
              </div>

              {/* Location Status Card */}
              <div className="modal-location-card">
                <h5>Current Position & Section</h5>
                <p>
                  {selectedTrain.current_section_name ? (
                    <>
                      Train is currently traveling inside <strong>{selectedTrain.current_section_name}</strong> at milepost{' '}
                      <strong>{selectedTrain.current_position_km} km</strong>.
                    </>
                  ) : selectedTrain.current_station_name ? (
                    <>
                      Train is stationed / holding at <strong>{selectedTrain.current_station_name}</strong>.
                    </>
                  ) : (
                    <>Scheduled at origin depot.</>
                  )}
                </p>
              </div>

              {/* Intermediate Timetables */}
              <div className="modal-schedule-section">
                <h5>Route Timetable & Intermediate Stops</h5>
                {trainSchedules.length > 0 ? (
                  <table className="mini-schedule-table">
                    <thead>
                      <tr>
                        <th>Seq</th>
                        <th>Station</th>
                        <th>Arr Time</th>
                        <th>Dep Time</th>
                        <th>Platform</th>
                      </tr>
                    </thead>
                    <tbody>
                      {trainSchedules.map((sc) => (
                        <tr key={sc.schedule_id}>
                          <td>#{sc.stop_sequence}</td>
                          <td><strong>{sc.station_name}</strong> ({sc.station_code})</td>
                          <td className="font-mono">{sc.scheduled_arrival || 'Origin'}</td>
                          <td className="font-mono">{sc.scheduled_departure || 'Destination'}</td>
                          <td>Platform {sc.platform_number}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-muted text-sm">No intermediate scheduled stops recorded for this train.</p>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <span className="text-xs text-muted">AI-Powered Train Traffic Control Prototype</span>
              <button className="primary-btn" onClick={closeTrainDetails}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
