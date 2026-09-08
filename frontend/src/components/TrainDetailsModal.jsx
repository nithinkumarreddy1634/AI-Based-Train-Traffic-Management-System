import React from 'react';
import {
  Train,
  X,
  MapPin,
  GitBranch,
  Gauge,
  Clock,
  Navigation,
  Compass,
  CheckCircle2,
  AlertCircle,
  Radio,
  ArrowRight,
  Route,
} from 'lucide-react';

export default function TrainDetailsModal({ train, onClose }) {
  if (!train) return null;

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
        return <span className="status-chip chip-muted">SCHEDULED</span>;
      case 'STOPPED':
        return <span className="status-chip chip-blocked">STOPPED</span>;
      case 'ARRIVED':
        return <span className="status-chip chip-available"><CheckCircle2 size={11} /> ARRIVED</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  const isDelayed = (train.current_delay_minutes || 0) > 0;
  const routeStations = train.route_stations || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content train-details-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-train-avatar">
              <Train size={24} />
            </div>
            <div>
              <h3>
                {train.train_number} — {train.train_name}
              </h3>
              <div className="modal-subtitle-badges">
                <span className="type-tag">{train.train_type}</span>
                {getPriorityBadge(train.priority)}
                {getStatusBadge(train.status)}
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Key Metrics Row */}
          <div className="modal-telemetry-grid">
            <div className="m-card">
              <span className="m-label"><Gauge size={13} /> Current Speed</span>
              <span className="m-value font-mono text-sky-400">
                {Number(train.speed_kmph || 0).toFixed(1)} <small>km/h</small>
              </span>
            </div>

            <div className="m-card">
              <span className="m-label"><Gauge size={13} /> Speed Limit</span>
              <span className="m-value font-mono text-slate-300">
                {train.max_speed_kmph || 100} <small>km/h</small>
              </span>
            </div>

            <div className="m-card">
              <span className="m-label"><Clock size={13} /> Delay Status</span>
              <span className={`m-value ${isDelayed ? 'text-amber-400' : 'text-emerald-400'}`}>
                {isDelayed ? `+${train.current_delay_minutes} min` : 'On Schedule'}
              </span>
            </div>

            <div className="m-card">
              <span className="m-label"><Navigation size={13} /> Direction</span>
              <span className="m-value font-mono text-sky-300">
                {train.direction || 'UP'}
              </span>
            </div>

            <div className="m-card">
              <span className="m-label"><Route size={13} /> Remaining Distance</span>
              <span className="m-value font-mono text-purple-400">
                {train.remaining_distance_km !== undefined ? `${train.remaining_distance_km} km` : '—'}
              </span>
            </div>

            <div className="m-card">
              <span className="m-label"><MapPin size={13} /> Next Station</span>
              <span className="m-value text-slate-200">
                {train.next_station_name || 'Terminal'}
              </span>
            </div>
          </div>

          {/* Current Block Location */}
          <div className="modal-location-banner">
            <div className="loc-banner-item">
              <span className="loc-title">Current Section:</span>
              <strong>{train.current_section_name || 'Station Platform'}</strong>
              {train.current_position_km !== undefined && train.current_section_name && (
                <span className="loc-milepost font-mono">
                  Milepost {Number(train.current_position_km).toFixed(1)} / {train.section_length_km || 20} km ({Math.round(train.section_progress_pct || 0)}%)
                </span>
              )}
            </div>

            <div className="loc-banner-item">
              <span className="loc-title">Station / Dwell:</span>
              <strong>{train.current_station_name || 'In Transit'}</strong>
            </div>
          </div>

          {/* Phase 6: ML Delay Prediction Section */}
          <div className="modal-ml-forecast-banner">
            <div className="ml-forecast-header">
              <span className="ml-forecast-tag">🤖 ML ARRIVAL DELAY FORECAST (PHASE 6)</span>
              <span className="ml-model-pill">HistGradientBoosting</span>
            </div>
            <div className="ml-forecast-grid">
              <div className="ml-forecast-item">
                <span className="ml-sub">Current Delay</span>
                <span className="ml-val font-mono">{Number(train.current_delay_minutes || 0).toFixed(1)} min</span>
              </div>
              <div className="ml-forecast-item">
                <span className="ml-sub">Predicted Total Delay</span>
                <span className="ml-val font-mono text-purple-400">
                  {Number(train.predicted_delay_minutes !== undefined ? train.predicted_delay_minutes : train.current_delay_minutes || 0).toFixed(1)} min
                </span>
              </div>
              <div className="ml-forecast-item">
                <span className="ml-sub">Expected Additional Delay</span>
                <span className="ml-val font-mono text-amber-400">
                  +{Number(train.expected_additional_delay || 0).toFixed(1)} min
                </span>
              </div>
              <div className="ml-forecast-item">
                <span className="ml-sub">Last Forecast</span>
                <span className="ml-val font-mono text-slate-300">
                  {train.last_prediction_time || 'Live Telemetry'}
                </span>
              </div>
            </div>
          </div>

          {/* Step-by-Step Route Schematic with Highlighted Location */}
          <div className="modal-route-schematic">
            <div className="route-schematic-header">
              <Route size={15} className="text-sky-400" />
              <h5>Scheduled Corridor Route & Traversal Progress</h5>
            </div>

            <div className="route-steps-container">
              {routeStations.length > 0 ? (
                routeStations.map((st, idx) => {
                  const isCur = st.is_current;
                  const isVis = st.is_visited;
                  const isLast = idx === routeStations.length - 1;

                  return (
                    <React.Fragment key={st.station_id || idx}>
                      <div className={`route-step-node ${isCur ? 'step-current' : isVis ? 'step-visited' : 'step-upcoming'}`}>
                        <div className="step-circle">
                          {isVis ? <CheckCircle2 size={13} /> : isCur ? <Train size={13} /> : <MapPin size={12} />}
                        </div>
                        <span className="step-code">{st.station_code}</span>
                        <span className="step-name">{st.station_name}</span>
                        {isCur && <span className="step-current-pill">HERE</span>}
                      </div>

                      {!isLast && (
                        <div className={`route-step-connector ${isVis ? 'conn-visited' : ''}`}>
                          <div className="connector-line" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <div className="route-endpoints-simple">
                  <span className="simple-st-tag">{train.source_station_name || 'Origin'}</span>
                  <ArrowRight size={16} className="text-sky-400" />
                  <span className="simple-st-tag">{train.destination_station_name || 'Destination'}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <span className="text-xs text-slate-500 font-mono">Train ID: #{train.train_id}</span>
          <button className="primary-btn" onClick={onClose}>
            Close Telemetry
          </button>
        </div>
      </div>
    </div>
  );
}

