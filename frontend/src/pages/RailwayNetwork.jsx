import React, { useState, useEffect } from 'react';
import {
  Network,
  GitBranch,
  Train,
  CheckCircle2,
  AlertTriangle,
  Wrench,
  Ban,
  Radio,
  Search,
  RefreshCw,
  Layers,
  MapPin,
  Compass,
} from 'lucide-react';
import { fetchNetwork } from '../services/api';

export default function RailwayNetwork({ simulation }) {
  const [network, setNetwork] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('topology'); // 'topology' | 'stations' | 'sections' | 'tracks'
  const [selectedSection, setSelectedSection] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadNetworkData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchNetwork();
      setNetwork(data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch railway network.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadNetworkData();
  }, []);

  // Derived live simulation data (falling back to database snapshot)
  const liveTrains = (simulation?.trains && simulation.trains.length > 0)
    ? simulation.trains
    : (network?.trains || []);

  const liveTracks = (simulation?.tracks && simulation.tracks.length > 0)
    ? simulation.tracks
    : (network?.tracks || []);

  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'AVAILABLE':
        return <span className="status-chip chip-available"><CheckCircle2 size={12} /> Available</span>;
      case 'OCCUPIED':
        return <span className="status-chip chip-occupied"><Radio size={12} /> Occupied</span>;
      case 'BLOCKED':
        return <span className="status-chip chip-blocked"><Ban size={12} /> Blocked</span>;
      case 'MAINTENANCE':
        return <span className="status-chip chip-maintenance"><Wrench size={12} /> Maintenance</span>;
      case 'ACTIVE':
        return <span className="status-chip chip-available"><CheckCircle2 size={12} /> Active</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  // Coordinates for the 5 stations in our SVG Synoptic Diagram
  // Central Station (top center-left), North Junction (middle-left),
  // East Junction (middle-right), West Terminal (far left), South Station (bottom center)
  const stationCoords = {
    SEC01: { x: 400, y: 70, label: 'Central Station' },
    SEC02: { x: 260, y: 190, label: 'North Junction' },
    SEC03: { x: 540, y: 190, label: 'East Junction' },
    SEC05: { x: 120, y: 290, label: 'West Terminal' },
    SEC04: { x: 400, y: 390, label: 'South Station' },
  };

  const getDynamicSectionColor = (sec) => {
    const tracksForSec = liveTracks.filter(t => t.section_id === sec.section_id);
    if (tracksForSec.some(t => (t.status || '').toUpperCase() === 'OCCUPIED')) {
      return '#38bdf8'; // sky blue (active train in section)
    }
    if (tracksForSec.some(t => (t.status || '').toUpperCase() === 'BLOCKED')) {
      return '#f59e0b'; // amber
    }
    if (tracksForSec.some(t => (t.status || '').toUpperCase() === 'MAINTENANCE')) {
      return '#ef4444'; // red
    }
    return '#10b981'; // emerald green (available)
  };

  const getTrackColor = (secStatus) => {
    switch ((secStatus || '').toUpperCase()) {
      case 'OCCUPIED':
        return '#38bdf8'; // sky blue
      case 'AVAILABLE':
        return '#10b981'; // emerald green
      case 'BLOCKED':
        return '#f59e0b'; // amber
      case 'MAINTENANCE':
        return '#ef4444'; // red
      default:
        return '#64748b'; // slate
    }
  };

  const filteredStations = (network?.stations || []).filter(
    (s) =>
      s.station_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.station_code.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredSections = (network?.sections || []).filter(
    (sec) =>
      sec.section_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sec.start_station_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sec.end_station_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredTracks = liveTracks.filter(
    (t) =>
      String(t.track_id).includes(searchQuery) ||
      (t.occupied_train_number && t.occupied_train_number.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Railway Network Topology & Infrastructure</h2>
          <p className="page-subheading">
            Physical block sections, double tracks, signaling status, and station platforms.
          </p>
        </div>
        <div className="header-actions-group">
          <button
            onClick={loadNetworkData}
            className="secondary-btn"
            disabled={isLoading}
            title="Refresh Network Data"
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
            <span>Refresh Network</span>
          </button>
        </div>
      </div>

      {/* Network Overview Mini Badges */}
      <div className="network-quick-stats">
        <div className="quick-stat-pill">
          <MapPin size={14} className="text-info" />
          <span><strong>{network?.stations?.length ?? 5}</strong> Stations</span>
        </div>
        <div className="quick-stat-pill">
          <GitBranch size={14} className="text-info" />
          <span><strong>{network?.sections?.length ?? 7}</strong> Railway Sections</span>
        </div>
        <div className="quick-stat-pill">
          <Layers size={14} className="text-info" />
          <span><strong>{network?.tracks?.length ?? 14}</strong> Directional Tracks</span>
        </div>
        <div className="quick-stat-pill">
          <Train size={14} className="text-info" />
          <span><strong>{network?.trains?.length ?? 12}</strong> Deployed Trains</span>
        </div>
      </div>

      {/* Main Tabs */}
      <div className="subnav-tabs">
        <button
          className={`subnav-btn ${activeTab === 'topology' ? 'subnav-btn-active' : ''}`}
          onClick={() => setActiveTab('topology')}
        >
          <Network size={15} />
          <span>Synoptic Network Diagram</span>
        </button>
        <button
          className={`subnav-btn ${activeTab === 'stations' ? 'subnav-btn-active' : ''}`}
          onClick={() => setActiveTab('stations')}
        >
          <MapPin size={15} />
          <span>Stations ({network?.stations?.length ?? 0})</span>
        </button>
        <button
          className={`subnav-btn ${activeTab === 'sections' ? 'subnav-btn-active' : ''}`}
          onClick={() => setActiveTab('sections')}
        >
          <GitBranch size={15} />
          <span>Sections ({network?.sections?.length ?? 0})</span>
        </button>
        <button
          className={`subnav-btn ${activeTab === 'tracks' ? 'subnav-btn-active' : ''}`}
          onClick={() => setActiveTab('tracks')}
        >
          <Layers size={15} />
          <span>Tracks & Occupancy ({network?.tracks?.length ?? 0})</span>
        </button>
      </div>

      {/* TOPOLOGY SYNOPTIC MAP VIEW */}
      {activeTab === 'topology' && (
        <div className="network-visualizer-container">
          <div className="visualizer-header">
            <div>
              <h3>Interactive Network Synoptic Diagram</h3>
              <p>Topological graph representation of stations and dual-track block sections.</p>
            </div>
            <div className="legend-row">
              <div className="legend-item"><span className="legend-color color-available"></span> Available</div>
              <div className="legend-item"><span className="legend-color color-occupied"></span> Occupied (Active Train)</div>
              <div className="legend-item"><span className="legend-color color-blocked"></span> Blocked</div>
              <div className="legend-item"><span className="legend-color color-maintenance"></span> Maintenance</div>
            </div>
          </div>

          <div className="synoptic-svg-wrapper">
            <svg viewBox="0 0 800 460" className="synoptic-svg">
              <defs>
                <filter id="glow-sky" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Draw Sections / Track Lines */}
              {network?.sections?.map((sec) => {
                const s1 = stationCoords[sec.start_station_code] || { x: 100, y: 100 };
                const s2 = stationCoords[sec.end_station_code] || { x: 300, y: 300 };
                const isSelected = selectedSection?.section_id === sec.section_id;
                const strokeColor = getDynamicSectionColor(sec);
                const midX = (s1.x + s2.x) / 2;
                const midY = (s1.y + s2.y) / 2;

                return (
                  <g
                    key={sec.section_id}
                    className="section-group"
                    onClick={() => setSelectedSection(sec)}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* Underlying Glow Track */}
                    <line
                      x1={s1.x}
                      y1={s1.y}
                      x2={s2.x}
                      y2={s2.y}
                      stroke={strokeColor}
                      strokeWidth={isSelected ? 6 : 4}
                      strokeLinecap="round"
                      opacity={0.85}
                    />

                    {/* Section Label Badge */}
                    <rect
                      x={midX - 36}
                      y={midY - 11}
                      width={72}
                      height={22}
                      rx={4}
                      fill="#0f172a"
                      stroke={strokeColor}
                      strokeWidth={1.5}
                    />
                    <text
                      x={midX}
                      y={midY + 4}
                      fill="#f1f5f9"
                      fontSize="9"
                      fontWeight="bold"
                      textAnchor="middle"
                      fontFamily="monospace"
                    >
                      {sec.length_km}km
                    </text>
                  </g>
                );
              })}

              {/* Draw Station Nodes */}
              {network?.stations?.map((st) => {
                const coord = stationCoords[st.station_code] || { x: 200, y: 200, label: st.station_name };
                return (
                  <g key={st.station_id} className="station-node-group">
                    {/* Outer halo */}
                    <circle cx={coord.x} cy={coord.y} r={22} fill="#1e293b" stroke="#38bdf8" strokeWidth={2} />
                    <circle cx={coord.x} cy={coord.y} r={14} fill="#0284c7" />

                    {/* Station code inside */}
                    <text
                      x={coord.x}
                      y={coord.y + 4}
                      fill="#ffffff"
                      fontSize="10"
                      fontWeight="bold"
                      textAnchor="middle"
                      fontFamily="sans-serif"
                    >
                      {st.station_code.replace('SEC', 'S')}
                    </text>

                    {/* Station Name & Platform Badge Below/Above */}
                    <text
                      x={coord.x}
                      y={coord.y + 36}
                      fill="#f8fafc"
                      fontSize="12"
                      fontWeight="600"
                      textAnchor="middle"
                    >
                      {st.station_name}
                    </text>
                    <text
                      x={coord.x}
                      y={coord.y + 50}
                      fill="#94a3b8"
                      fontSize="9"
                      textAnchor="middle"
                    >
                      {st.number_of_platforms} Platforms · {st.station_code}
                    </text>
                  </g>
                );
              })}

              {/* Render Live Trains Moving in Real-Time */}
              {liveTrains.filter(t => t.status !== 'SCHEDULED').map((train) => {
                let tx = 0;
                let ty = 0;

                if (train.current_section_id) {
                  const sec = network?.sections?.find(s => s.section_id === train.current_section_id);
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
                  // Perpendicular offset for double track separation (UP vs DOWN)
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
                    case 'RUNNING': return '#10b981'; // Green
                    case 'WAITING': return '#f59e0b'; // Amber
                    case 'DELAYED': return '#ef4444'; // Red
                    case 'STOPPED': return '#38bdf8'; // Sky blue
                    case 'ARRIVED': return '#a855f7'; // Purple
                    default: return '#64748b';
                  }
                };

                const markerColor = getTrainColor(train.status);
                const speedVal = Math.round(train.speed_kmph || 0);

                return (
                  <g key={train.train_id} className="train-marker-group" style={{ cursor: 'pointer' }}>
                    {/* Pulsing indicator halo */}
                    <circle cx={tx} cy={ty} r={14} fill={markerColor} opacity={0.25} />

                    {/* Train Marker Box */}
                    <rect
                      x={tx - 32}
                      y={ty - 13}
                      width={64}
                      height={26}
                      rx={5}
                      fill="#0b1329"
                      stroke={markerColor}
                      strokeWidth={1.75}
                      filter="url(#glow-sky)"
                    />

                    {/* Train Number */}
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

                    {/* Live Speed / State */}
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
                        ? 'WAIT'
                        : train.status === 'ARRIVED'
                        ? 'ARRIVED'
                        : `${speedVal} km/h`}
                    </text>

                    {/* Status Dot */}
                    <circle cx={tx + 25} cy={ty - 6} r={2.5} fill={markerColor} />
                  </g>
                );
              })}
            </svg>
          </div>

          {/* Selected Section Telemetry Box */}
          {selectedSection && (
            <div className="section-telemetry-card">
              <div className="sec-card-header">
                <div>
                  <span className="sec-pill">Section Telemetry</span>
                  <h4>{selectedSection.section_name}</h4>
                </div>
                {getStatusBadge(selectedSection.status)}
              </div>
              <div className="sec-card-stats">
                <div className="sec-stat">
                  <span>Start Station:</span>
                  <strong>{selectedSection.start_station_name} ({selectedSection.start_station_code})</strong>
                </div>
                <div className="sec-stat">
                  <span>End Station:</span>
                  <strong>{selectedSection.end_station_name} ({selectedSection.end_station_code})</strong>
                </div>
                <div className="sec-stat">
                  <span>Section Length:</span>
                  <strong>{selectedSection.length_km} km</strong>
                </div>
                <div className="sec-stat">
                  <span>Speed Limit:</span>
                  <strong>{selectedSection.maximum_speed_kmph} km/h</strong>
                </div>
                <div className="sec-stat">
                  <span>Total Tracks:</span>
                  <strong>{selectedSection.number_of_tracks} tracks</strong>
                </div>
              </div>

              {/* Tracks in this section */}
              <div className="sec-tracks-list">
                <h5>Tracks in this Section</h5>
                <div className="tracks-chips-grid">
                  {selectedSection.tracks?.map((t) => (
                    <div key={t.track_id} className="track-chip-item">
                      <div>
                        <strong>Track {t.track_number} ({t.direction})</strong>
                        <span className="text-muted">Max: {t.maximum_speed} km/h</span>
                      </div>
                      <div className="track-right">
                        {getStatusBadge(t.status)}
                        {t.occupied_train_number && (
                          <span className="occupied-train-tag">
                            <Train size={11} /> {t.occupied_train_number}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STATIONS TABLE TAB */}
      {activeTab === 'stations' && (
        <div className="table-wrapper-panel">
          <div className="table-controls-row">
            <div className="search-input-box">
              <Search size={15} />
              <input
                type="text"
                placeholder="Search station name or code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="count-pill">Showing {filteredStations.length} stations</div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Station Code</th>
                <th>Station Name</th>
                <th>Platforms</th>
                <th>Coordinates (Lat, Long)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredStations.map((st) => (
                <tr key={st.station_id}>
                  <td>
                    <span className="code-badge">{st.station_code}</span>
                  </td>
                  <td className="font-semibold text-white">{st.station_name}</td>
                  <td>{st.number_of_platforms} Platforms</td>
                  <td className="text-muted font-mono text-xs">{st.latitude.toFixed(4)}, {st.longitude.toFixed(4)}</td>
                  <td>{getStatusBadge(st.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* SECTIONS TABLE TAB */}
      {activeTab === 'sections' && (
        <div className="table-wrapper-panel">
          <div className="table-controls-row">
            <div className="search-input-box">
              <Search size={15} />
              <input
                type="text"
                placeholder="Search railway section..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="count-pill">Showing {filteredSections.length} sections</div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Section ID</th>
                <th>Section Name</th>
                <th>Start Station</th>
                <th>End Station</th>
                <th>Length (km)</th>
                <th>Max Speed</th>
                <th>Tracks</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredSections.map((sec) => (
                <tr key={sec.section_id}>
                  <td className="font-mono">SEC-{sec.section_id}</td>
                  <td className="font-semibold text-white">{sec.section_name}</td>
                  <td>{sec.start_station_name} ({sec.start_station_code})</td>
                  <td>{sec.end_station_name} ({sec.end_station_code})</td>
                  <td className="font-mono">{sec.length_km} km</td>
                  <td className="font-mono">{sec.maximum_speed_kmph} km/h</td>
                  <td>{sec.number_of_tracks} tracks</td>
                  <td>{getStatusBadge(sec.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TRACKS TABLE TAB */}
      {activeTab === 'tracks' && (
        <div className="table-wrapper-panel">
          <div className="table-controls-row">
            <div className="search-input-box">
              <Search size={15} />
              <input
                type="text"
                placeholder="Search track ID or train..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="count-pill">Showing {filteredTracks.length} tracks</div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Track ID</th>
                <th>Section ID</th>
                <th>Track Number</th>
                <th>Direction</th>
                <th>Maximum Speed</th>
                <th>Status</th>
                <th>Occupied Train</th>
              </tr>
            </thead>
            <tbody>
              {filteredTracks.map((t) => (
                <tr key={t.track_id}>
                  <td className="font-mono">TRK-{t.track_id}</td>
                  <td className="font-mono">Section {t.section_id}</td>
                  <td>Track #{t.track_number}</td>
                  <td>
                    <span className="direction-badge">{t.direction}</span>
                  </td>
                  <td className="font-mono">{t.maximum_speed} km/h</td>
                  <td>{getStatusBadge(t.status)}</td>
                  <td>
                    {t.occupied_train_number ? (
                      <span className="occupied-train-tag">
                        <Train size={12} /> {t.occupied_train_number} ({t.occupied_train_name})
                      </span>
                    ) : (
                      <span className="text-muted">Unoccupied</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
