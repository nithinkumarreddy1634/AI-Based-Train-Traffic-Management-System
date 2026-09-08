import React from 'react';
import { GitBranch, Radio, CheckCircle2, Ban, Wrench, Train, Gauge, Activity } from 'lucide-react';

export default function SectionMonitoringPanel({ sections, onSelectSection, selectedSectionId }) {
  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'OCCUPIED':
        return <span className="status-chip chip-occupied"><Radio size={11} /> OCCUPIED</span>;
      case 'AVAILABLE':
        return <span className="status-chip chip-available"><CheckCircle2 size={11} /> AVAILABLE</span>;
      case 'BLOCKED':
        return <span className="status-chip chip-blocked"><Ban size={11} /> BLOCKED</span>;
      case 'MAINTENANCE':
        return <span className="status-chip chip-maintenance"><Wrench size={11} /> MAINT</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  const getDensityChip = (density) => {
    const d = (density || 'LOW').toUpperCase();
    switch (d) {
      case 'CRITICAL':
        return <span className="density-tag tag-critical">CRITICAL</span>;
      case 'HIGH':
        return <span className="density-tag tag-high">HIGH</span>;
      case 'MEDIUM':
        return <span className="density-tag tag-med">MEDIUM</span>;
      default:
        return <span className="density-tag tag-low">LOW</span>;
    }
  };

  return (
    <div className="section-monitor-panel">
      <div className="monitor-panel-header">
        <div className="panel-title-row">
          <GitBranch size={17} className="text-sky-400" />
          <h3>Railway Section Telemetry & Utilization</h3>
        </div>
        <span className="count-pill">{sections?.length || 0} Sections Active</span>
      </div>

      <div className="section-cards-grid">
        {sections?.map((sec) => {
          const isSelected = selectedSectionId === sec.section_id;
          const isOccupied = sec.status === 'OCCUPIED';
          const utilPct = sec.utilization_percent ?? 0.0;

          return (
            <div
              key={sec.section_id}
              className={`section-monitor-card ${isSelected ? 'sec-card-selected' : ''} ${isOccupied ? 'sec-card-occupied' : ''}`}
              onClick={() => onSelectSection && onSelectSection(sec)}
            >
              <div className="sec-card-top">
                <div className="sec-identity">
                  <span className="sec-id-badge">SEC-{sec.section_id}</span>
                  <span className="sec-name-text">{sec.section_name}</span>
                </div>
                {getStatusBadge(sec.status)}
              </div>

              <div className="sec-endpoints-row">
                <span className="endpoint-tag">{sec.start_station_code}</span>
                <span className="endpoint-arrow">─────</span>
                <span className="sec-len-pill">{sec.length_km} km</span>
                <span className="endpoint-arrow">─────</span>
                <span className="endpoint-tag">{sec.end_station_code}</span>
              </div>

              {/* Occupied Trains Badge */}
              <div className="sec-train-row">
                {sec.current_trains && sec.current_trains.length > 0 ? (
                  <div className="occupied-train-chips">
                    <Train size={12} className="text-sky-400" />
                    {sec.current_trains.map((tNum) => (
                      <span key={tNum} className="active-train-chip">
                        {tNum}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="no-train-text">Section Track Clear</span>
                )}
                {getDensityChip(sec.density_level)}
              </div>

              {/* Cumulative Utilization Bar */}
              <div className="sec-utilization-row">
                <div className="util-header">
                  <span>Occupancy Utilization</span>
                  <strong>{utilPct}%</strong>
                </div>
                <div className="util-track">
                  <div
                    className={`util-fill ${utilPct > 70 ? 'util-high' : utilPct > 40 ? 'util-med' : ''}`}
                    style={{ width: `${Math.min(100, Math.max(2, utilPct))}%` }}
                  />
                </div>
              </div>

              <div className="sec-footer-meta">
                <span>Max Speed: <strong>{sec.maximum_speed_kmph} km/h</strong></span>
                <span>Tracks: <strong>{sec.track_count} physical</strong></span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

