import React from 'react';

export default function CongestionPanel({ congestion = [] }) {
  const getCongestionBadgeClass = (level) => {
    switch (level) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MODERATE': return 'badge-medium';
      default: return 'badge-low';
    }
  };

  const getUtilBarColor = (pct) => {
    if (pct >= 80) return 'linear-gradient(90deg, #ef4444, #dc2626)';
    if (pct >= 60) return 'linear-gradient(90deg, #f59e0b, #d97706)';
    if (pct >= 30) return 'linear-gradient(90deg, #3b82f6, #2563eb)';
    return 'linear-gradient(90deg, #10b981, #059669)';
  };

  return (
    <div className="card congestion-panel-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">SECTION FLOW & TRAFFIC DENSITY</div>
          <h3 className="card-title">Network Section Congestion Analysis</h3>
        </div>
        <span className="badge badge-info">{congestion.length} Sections Monitored</span>
      </div>

      <div className="card-body">
        {congestion.length === 0 ? (
          <div className="empty-state-card">
            <p>Awaiting simulation telemetry for section flow analysis...</p>
          </div>
        ) : (
          <div className="congestion-grid">
            {congestion.map((sec) => {
              const util = sec.utilization_percent || 0;
              const hasWaiting = sec.waiting_train_count > 0;

              return (
                <div key={sec.section_id} className={`congestion-sec-card level-${sec.congestion_level.toLowerCase()}`}>
                  <div className="congestion-card-header">
                    <div>
                      <div className="congestion-sec-name">{sec.section_name}</div>
                      <div className="congestion-sec-meta">
                        Length: {sec.length_km} km | Max Speed: {sec.max_speed_kmph} km/h
                      </div>
                    </div>
                    <span className={`badge ${getCongestionBadgeClass(sec.congestion_level)}`}>
                      {sec.congestion_level}
                    </span>
                  </div>

                  {/* Flow & Train Numbers */}
                  <div className="congestion-train-counts">
                    <div className="count-item">
                      <span className="count-label">Active Trains:</span>
                      <span className="count-val">{sec.active_train_count}</span>
                    </div>
                    <div className="count-item">
                      <span className="count-label">Waiting / Queued:</span>
                      <span className={`count-val ${hasWaiting ? 'text-danger fw-bold' : ''}`}>
                        {sec.waiting_train_count}
                      </span>
                    </div>
                    <div className="count-item">
                      <span className="count-label">Avg Speed:</span>
                      <span className="count-val">{sec.average_speed_kmph} km/h</span>
                    </div>
                  </div>

                  {/* Speed drop indicator if applicable */}
                  {sec.speed_drop_percent > 10 && (
                    <div className="speed-drop-alert">
                      ⚠️ Speed reduced by {sec.speed_drop_percent}% below limit
                    </div>
                  )}

                  {/* Utilization Progress Bar */}
                  <div className="congestion-util-block">
                    <div className="util-header">
                      <span>Occupancy Utilization</span>
                      <span className="util-pct">{util.toFixed(1)}%</span>
                    </div>
                    <div className="util-bar-track">
                      <div
                        className="util-bar-fill"
                        style={{
                          width: `${Math.min(100, util)}%`,
                          background: getUtilBarColor(util),
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

