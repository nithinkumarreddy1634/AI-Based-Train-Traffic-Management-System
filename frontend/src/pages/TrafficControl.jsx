import React, { useState, useEffect, useMemo } from 'react';
import {
  Sliders,
  Train,
  Radio,
  ClockAlert,
  CheckCircle2,
  GitBranch,
  Search,
  Filter,
  RefreshCw,
  Clock,
  Layers,
  Activity,
  AlertTriangle,
  Terminal,
  MapPin,
  Maximize2,
  Trash2,
} from 'lucide-react';
import TrafficDensityCard from '../components/TrafficDensityCard';
import SectionMonitoringPanel from '../components/SectionMonitoringPanel';
import TrackOccupancyPanel from '../components/TrackOccupancyPanel';
import AlertsPanel from '../components/AlertsPanel';
import TrainDetailsModal from '../components/TrainDetailsModal';

export default function TrafficControl({ simulation }) {
  const [selectedTrain, setSelectedTrain] = useState(null);
  const [selectedSectionId, setSelectedSectionId] = useState(null);

  // Table filtering & search state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [sectionFilter, setSectionFilter] = useState('ALL');

  // Network station coordinate map for SVG Synoptic Diagram
  const stationCoords = {
    SEC01: { x: 400, y: 70, label: 'Central Station' },
    SEC02: { x: 260, y: 190, label: 'North Junction' },
    SEC03: { x: 540, y: 190, label: 'East Junction' },
    SEC05: { x: 120, y: 290, label: 'West Terminal' },
    SEC04: { x: 400, y: 390, label: 'South Station' },
  };

  const summary = simulation?.summary || {
    total_trains: 12,
    running_trains: 0,
    waiting_trains: 0,
    delayed_trains: 0,
    arrived_trains: 0,
    occupied_sections: 0,
    throughput_trains_per_hour: 0.0,
  };

  const liveTrains = simulation?.trains || [];
  const liveSections = simulation?.sections || [];
  const liveTracks = simulation?.tracks || [];
  const alerts = simulation?.alerts || [];
  const density = simulation?.density || { network_density: 'LOW', average_trains_per_section: 0, sections: [] };
  const events = simulation?.events || [];

  // Filter trains for table
  const filteredTrains = useMemo(() => {
    return liveTrains.filter((t) => {
      const matchesSearch =
        !searchQuery ||
        String(t.train_id).includes(searchQuery) ||
        t.train_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.train_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (t.source_station_name && t.source_station_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (t.destination_station_name && t.destination_station_name.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
      const matchesType = typeFilter === 'ALL' || t.train_type === typeFilter;
      const matchesPriority = priorityFilter === 'ALL' || t.priority === priorityFilter;
      const matchesSection = sectionFilter === 'ALL' || String(t.current_section_id) === String(sectionFilter);

      return matchesSearch && matchesStatus && matchesType && matchesPriority && matchesSection;
    });
  }, [liveTrains, searchQuery, statusFilter, typeFilter, priorityFilter, sectionFilter]);

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
        return <span className="status-chip chip-maintenance"><AlertTriangle size={11} /> DELAYED</span>;
      case 'SCHEDULED':
        return <span className="status-chip chip-muted">SCHEDULED</span>;
      case 'STOPPED':
        return <span className="status-chip chip-blocked">STOPPED</span>;
      case 'ARRIVED':
        return <span className="status-chip chip-available"><CheckCircle2 size={11} /> ARRIVED</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  const getSectionStrokeColor = (sec) => {
    switch ((sec.status || '').toUpperCase()) {
      case 'OCCUPIED':
        return '#38bdf8'; // Sky blue
      case 'BLOCKED':
        return '#f59e0b'; // Amber
      case 'MAINTENANCE':
        return '#ef4444'; // Red
      default:
        return '#10b981'; // Emerald green
    }
  };

  return (
    <div className="page-container traffic-control-page">
      {/* Control Room Header */}
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Railway Traffic Control Operations Center</h2>
          <p className="page-subheading">
            Live telemetry, dynamic block section occupancy, headway monitoring, and dispatcher alerts.
          </p>
        </div>
        <div className="header-actions-group">
          <div className="phase-indicator-tag phase-tag-live">
            <span className="state-pulse-dot" />
            <span>Phase 4 Control Room Online</span>
          </div>
          {simulation?.refresh && (
            <button onClick={simulation.refresh} className="secondary-btn" title="Refresh Live State">
              <RefreshCw size={13} className={simulation.actionLoading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          )}
        </div>
      </div>

      {/* 1. TOP 6 STATISTICS CARDS */}
      <div className="control-stats-grid">
        <div className="ctrl-stat-card stat-total">
          <div className="stat-top">
            <span className="stat-title">Total Trains</span>
            <Train size={18} className="text-sky-400" />
          </div>
          <div className="stat-val">{summary.total_trains}</div>
          <span className="stat-sub">Active fleet monitored</span>
        </div>

        <div className="ctrl-stat-card stat-running">
          <div className="stat-top">
            <span className="stat-title">Running Trains</span>
            <Radio size={18} className="text-emerald-400" />
          </div>
          <div className="stat-val text-emerald-400">{summary.running_trains}</div>
          <span className="stat-sub">Cruising in section</span>
        </div>

        <div className="ctrl-stat-card stat-waiting">
          <div className="stat-top">
            <span className="stat-title">Waiting Trains</span>
            <Clock size={18} className="text-amber-400" />
          </div>
          <div className="stat-val text-amber-400">{summary.waiting_trains}</div>
          <span className="stat-sub">Holding for clearance</span>
        </div>

        <div className="ctrl-stat-card stat-delayed">
          <div className="stat-top">
            <span className="stat-title">Delayed Trains</span>
            <ClockAlert size={18} className="text-rose-400" />
          </div>
          <div className="stat-val text-rose-400">{summary.delayed_trains}</div>
          <span className="stat-sub">Delay &gt; 0 min</span>
        </div>

        <div className="ctrl-stat-card stat-arrived">
          <div className="stat-top">
            <span className="stat-title">Arrived Trains</span>
            <CheckCircle2 size={18} className="text-purple-400" />
          </div>
          <div className="stat-val text-purple-400">{summary.arrived_trains}</div>
          <span className="stat-sub">Completed journey</span>
        </div>

        <div className="ctrl-stat-card stat-sections">
          <div className="stat-top">
            <span className="stat-title">Occupied Sections</span>
            <GitBranch size={18} className="text-sky-400" />
          </div>
          <div className="stat-val text-sky-400">
            {summary.occupied_sections} <small className="text-slate-400 text-sm">/ {summary.total_sections || 7}</small>
          </div>
          <span className="stat-sub">Section density active</span>
        </div>
      </div>

      {/* 2. INTERACTIVE SYNOPTIC NETWORK MAP */}
      <div className="network-visualizer-container control-room-map">
        <div className="visualizer-header">
          <div>
            <h3>Live Synoptic Corridor Diagram</h3>
            <p>Real-time physical block sections, track occupancy, and train vectors.</p>
          </div>
          <div className="legend-row">
            <div className="legend-item"><span className="legend-color color-available"></span> Available</div>
            <div className="legend-item"><span className="legend-color color-occupied"></span> Occupied</div>
            <div className="legend-item"><span className="legend-color color-blocked"></span> Blocked</div>
            <div className="legend-item"><span className="legend-color color-maintenance"></span> Maintenance</div>
          </div>
        </div>

        <div className="synoptic-svg-wrapper">
          <svg viewBox="0 0 800 460" className="synoptic-svg">
            <defs>
              <filter id="glow-ctrl" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Section Track Lines */}
            {liveSections.map((sec) => {
              const s1 = stationCoords[sec.start_station_code] || { x: 100, y: 100 };
              const s2 = stationCoords[sec.end_station_code] || { x: 300, y: 300 };
              const isSelected = selectedSectionId === sec.section_id;
              const sectionConflicts = (simulation?.conflicts || []).filter((c) => c.section_id === sec.section_id);
              const hasConflict = sectionConflicts.length > 0;
              const strokeColor = hasConflict ? '#ef4444' : getSectionStrokeColor(sec);
              const midX = (s1.x + s2.x) / 2;
              const midY = (s1.y + s2.y) / 2;

              return (
                <g
                  key={sec.section_id}
                  className="section-group"
                  onClick={() => setSelectedSectionId(sec.section_id)}
                  style={{ cursor: 'pointer' }}
                >
                  <line
                    x1={s1.x}
                    y1={s1.y}
                    x2={s2.x}
                    y2={s2.y}
                    stroke={strokeColor}
                    strokeWidth={isSelected ? 6 : (hasConflict ? 5 : 4)}
                    strokeLinecap="round"
                    opacity={0.85}
                  />

                  {/* Dynamic Conflict Warning Badge */}
                  {hasConflict && (
                    <g className="conflict-badge-group">
                      <rect
                        x={midX - 36}
                        y={midY - 30}
                        width={72}
                        height={16}
                        rx={8}
                        fill="#dc2626"
                        stroke="#ffffff"
                        strokeWidth={1}
                      />
                      <text
                        x={midX}
                        y={midY - 18}
                        fill="#ffffff"
                        fontSize="8"
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        ⚠️ {sectionConflicts.length} Conflict{sectionConflicts.length > 1 ? 's' : ''}
                      </text>
                    </g>
                  )}

                  {/* Section Label Badge */}
                  <rect
                    x={midX - 42}
                    y={midY - 11}
                    width={84}
                    height={22}
                    rx={4}
                    fill="#0a0f1d"
                    stroke={strokeColor}
                    strokeWidth={hasConflict ? 2 : 1.5}
                  />
                  <text
                    x={midX}
                    y={midY + 4}
                    fill="#f1f5f9"
                    fontSize="8.5"
                    fontWeight="bold"
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {sec.section_name} ({sec.length_km}k)
                  </text>
                </g>
              );
            })}

            {/* Station Nodes */}
            {Object.entries(stationCoords).map(([stCode, coord]) => (
              <g key={stCode} className="station-node-group">
                <circle cx={coord.x} cy={coord.y} r={22} fill="#1e293b" stroke="#38bdf8" strokeWidth={2} />
                <circle cx={coord.x} cy={coord.y} r={14} fill="#0284c7" />
                <text
                  x={coord.x}
                  y={coord.y + 4}
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="bold"
                  textAnchor="middle"
                  fontFamily="sans-serif"
                >
                  {stCode.replace('SEC', 'S')}
                </text>
                <text
                  x={coord.x}
                  y={coord.y + 36}
                  fill="#f8fafc"
                  fontSize="12"
                  fontWeight="600"
                  textAnchor="middle"
                >
                  {coord.label}
                </text>
              </g>
            ))}

            {/* Animated Live Trains */}
            {liveTrains.filter((t) => t.status !== 'SCHEDULED').map((train) => {
              let tx = 0;
              let ty = 0;

              if (train.current_section_id) {
                const sec = liveSections.find((s) => s.section_id === train.current_section_id);
                if (!sec) return null;
                const s1 = stationCoords[sec.start_station_code];
                const s2 = stationCoords[sec.end_station_code];
                if (!s1 || !s2) return null;

                const len = sec.length_km || 20;
                const rawRatio = Math.min(Math.max((train.current_position_km || 0) / len, 0.08), 0.92);
                const ratio = train.direction === 'DOWN' ? (1 - rawRatio) : rawRatio;

                const dx = s2.x - s1.x;
                const dy = s2.y - s1.y;
                const dNorm = Math.hypot(dx, dy) || 1;
                const perpX = -dy / dNorm;
                const perpY = dx / dNorm;
                const offset = train.direction === 'DOWN' ? -8 : 8;

                tx = s1.x + dx * ratio + perpX * offset;
                ty = s1.y + dy * ratio + perpY * offset;
              } else if (train.current_station_code) {
                const coord = stationCoords[train.current_station_code];
                if (!coord) return null;
                tx = coord.x + 28;
                ty = coord.y - 15;
              } else {
                return null;
              }

              const getTrainColor = (st) => {
                switch ((st || '').toUpperCase()) {
                  case 'RUNNING': return '#10b981';
                  case 'WAITING': return '#f59e0b';
                  case 'DELAYED': return '#ef4444';
                  case 'STOPPED': return '#38bdf8';
                  case 'ARRIVED': return '#a855f7';
                  default: return '#64748b';
                }
              };

              const markerColor = getTrainColor(train.status);
              const speedVal = Math.round(train.speed_kmph || 0);

              return (
                <g
                  key={train.train_id}
                  className="train-marker-group"
                  onClick={() => setSelectedTrain(train)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle cx={tx} cy={ty} r={14} fill={markerColor} opacity={0.25} />
                  <rect
                    x={tx - 32}
                    y={ty - 13}
                    width={64}
                    height={26}
                    rx={5}
                    fill="#0b1329"
                    stroke={markerColor}
                    strokeWidth={1.75}
                    filter="url(#glow-ctrl)"
                  />
                  <text
                    x={tx}
                    y={ty - 1}
                    fill="#ffffff"
                    fontSize="8"
                    fontWeight="bold"
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {train.train_number}
                  </text>
                  <text
                    x={tx}
                    y={ty + 9}
                    fill={markerColor}
                    fontSize="7"
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {train.status === 'STOPPED'
                      ? 'DWELL'
                      : train.status === 'WAITING'
                      ? 'HOLD'
                      : train.status === 'ARRIVED'
                      ? 'TERM'
                      : `${speedVal} km/h`}
                  </text>
                  <circle cx={tx + 25} cy={ty - 6} r={2.5} fill={markerColor} />
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* 3. OPERATIONS SPLIT VIEW: Sections / Tracks / Density (Left) + Alerts / Events (Right) */}
      <div className="control-split-grid">
        {/* Left Column: Infrastructure & Density */}
        <div className="control-col-left">
          <TrafficDensityCard density={density} />
          <SectionMonitoringPanel
            sections={liveSections}
            onSelectSection={(sec) => {
              setSelectedSectionId(sec.section_id);
              setSectionFilter(String(sec.section_id));
            }}
            selectedSectionId={selectedSectionId}
          />
          <TrackOccupancyPanel tracks={liveTracks} />
        </div>

        {/* Right Column: Alerts & Events */}
        <div className="control-col-right">
          <AlertsPanel
            alerts={alerts}
            onClearAlerts={simulation?.clearAlerts}
          />

          {/* Simulation Event Log */}
          <div className="sim-event-terminal">
            <div className="event-terminal-header">
              <div className="event-terminal-title">
                <Terminal size={14} className="text-sky-400" />
                <span>Simulation Dispatcher Event Log</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="event-terminal-badge">{events.length} Events</span>
                {simulation?.clearEvents && (
                  <button onClick={simulation.clearEvents} className="clear-alerts-btn" title="Clear Event Log">
                    <Trash2 size={12} />
                    <span>Clear</span>
                  </button>
                )}
              </div>
            </div>

            <div className="event-terminal-body">
              {events.length === 0 ? (
                <div className="text-center py-6 text-slate-500 font-mono text-xs">
                  Event buffer empty. Run simulation to log dispatching milestones.
                </div>
              ) : (
                events.map((ev, idx) => (
                  <div key={idx} className={`event-log-row event-${ev.event_type}`}>
                    <span className="event-time">{ev.timestamp}</span>
                    <span className={`event-type-badge event-badge-${ev.event_type}`}>
                      {ev.event_type}
                    </span>
                    <span className="event-desc">{ev.message}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 4. LIVE TRAIN MONITORING TABLE (13 COLUMNS) */}
      <div className="train-monitor-section">
        <div className="section-title-row">
          <div className="title-left">
            <Train size={18} className="text-sky-400" />
            <h3>Live Train Fleet Monitoring Table</h3>
            <span className="count-pill">
              Showing {filteredTrains.length} of {liveTrains.length} Trains
            </span>
          </div>

          {(statusFilter !== 'ALL' || typeFilter !== 'ALL' || priorityFilter !== 'ALL' || sectionFilter !== 'ALL' || searchQuery) && (
            <button
              onClick={() => {
                setStatusFilter('ALL');
                setTypeFilter('ALL');
                setPriorityFilter('ALL');
                setSectionFilter('ALL');
                setSearchQuery('');
                setSelectedSectionId(null);
              }}
              className="reset-filters-btn"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Filter Controls Bar */}
        <div className="filter-controls-panel">
          <div className="search-input-box filter-search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search train ID, number, name, origin, destination..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">All Statuses</option>
              <option value="RUNNING">Running</option>
              <option value="WAITING">Waiting</option>
              <option value="DELAYED">Delayed</option>
              <option value="SCHEDULED">Scheduled</option>
              <option value="STOPPED">Stopped</option>
              <option value="ARRIVED">Arrived</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Type:</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">All Types</option>
              <option value="EXPRESS">Express</option>
              <option value="PASSENGER">Passenger</option>
              <option value="LOCAL">Local</option>
              <option value="FREIGHT">Freight</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Priority:</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Section:</label>
            <select
              value={sectionFilter}
              onChange={(e) => {
                setSectionFilter(e.target.value);
                setSelectedSectionId(e.target.value === 'ALL' ? null : Number(e.target.value));
              }}
              className="filter-select"
            >
              <option value="ALL">All Sections</option>
              {liveSections.map((sec) => (
                <option key={sec.section_id} value={sec.section_id}>
                  {sec.section_name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 13-Column Table */}
        <div className="table-wrapper-panel">
          <table className="data-table">
            <thead>
              <tr>
                <th>Train ID</th>
                <th>Train Number</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Current Station</th>
                <th>Current Section & Progress</th>
                <th>Position</th>
                <th>Speed</th>
                <th>Direction</th>
                <th>Status</th>
                <th>Delay</th>
                <th>Next Station</th>
                <th>Destination</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrains.length === 0 ? (
                <tr>
                  <td colSpan={14} className="text-center py-6 text-slate-500">
                    No trains match the selected criteria.
                  </td>
                </tr>
              ) : (
                filteredTrains.map((t) => {
                  const isDelayed = (t.current_delay_minutes || 0) > 0;
                  return (
                    <tr
                      key={t.train_id}
                      className="clickable-tr"
                      onClick={() => setSelectedTrain(t)}
                    >
                      <td className="font-mono text-slate-400">#{t.train_id}</td>
                      <td>
                        <span className="train-no-badge">{t.train_number}</span>
                      </td>
                      <td>
                        <span className="type-tag">{t.train_type}</span>
                      </td>
                      <td>{getPriorityBadge(t.priority)}</td>
                      <td>
                        {t.current_station_name ? (
                          <span className="loc-badge-station">
                            <MapPin size={11} /> {t.current_station_name}
                          </span>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td>
                        {t.current_section_name ? (
                          <div className="progress-cell">
                            <span className="loc-badge">
                              <GitBranch size={11} /> {t.current_section_name}
                            </span>
                            <div className="progress-track" title={`${Math.round(t.section_progress_pct || 0)}% completed`}>
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
                          </div>
                        ) : (
                          <span className="text-slate-500">Station Platform</span>
                        )}
                      </td>
                      <td className="font-mono text-slate-300">
                        {Number(t.current_position_km || 0).toFixed(1)} km
                      </td>
                      <td>
                        <span className="font-mono font-bold text-sky-400">
                          {Number(t.speed_kmph || 0).toFixed(1)} <small className="text-slate-500">km/h</small>
                        </span>
                      </td>
                      <td className="font-mono text-sky-300">{t.direction || 'UP'}</td>
                      <td>{getStatusBadge(t.status)}</td>
                      <td>
                        {isDelayed ? (
                          <span className="delay-badge">+{t.current_delay_minutes} min</span>
                        ) : (
                          <span className="on-time-badge">On Time</span>
                        )}
                      </td>
                      <td className="text-slate-300">{t.next_station_name || 'Terminal'}</td>
                      <td className="font-semibold text-slate-200">{t.destination_station_name}</td>
                      <td>
                        <button
                          className="details-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTrain(t);
                          }}
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. TRAIN DETAILS MODAL / DRAWER */}
      {selectedTrain && (
        <TrainDetailsModal
          train={selectedTrain}
          onClose={() => setSelectedTrain(null)}
        />
      )}
    </div>
  );
}
