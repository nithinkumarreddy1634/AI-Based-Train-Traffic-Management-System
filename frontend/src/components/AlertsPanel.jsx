import React, { useState } from 'react';
import { Bell, AlertTriangle, AlertCircle, Info, Trash2, Filter } from 'lucide-react';

export default function AlertsPanel({ alerts, onClearAlerts }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const filteredAlerts = (alerts || []).filter((a) => {
    if (filterSeverity === 'ALL') return true;
    return a.severity === filterSeverity;
  });

  const getSeverityBadge = (sev) => {
    switch ((sev || '').toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="alert-sev-badge sev-critical">
            <AlertCircle size={12} /> CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="alert-sev-badge sev-warning">
            <AlertTriangle size={12} /> WARNING
          </span>
        );
      default:
        return (
          <span className="alert-sev-badge sev-info">
            <Info size={12} /> INFO
          </span>
        );
    }
  };

  return (
    <div className="alerts-panel">
      <div className="alerts-panel-header">
        <div className="panel-title-row">
          <Bell size={17} className="text-amber-400" />
          <h3>Real-Time Dispatcher Alerts</h3>
          <span className="alert-count-pill">{filteredAlerts.length}</span>
        </div>

        <div className="alert-header-actions">
          {/* Severity Filter Tabs */}
          <div className="alert-filter-group">
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((lvl) => (
              <button
                key={lvl}
                className={`alert-filter-btn ${filterSeverity === lvl ? 'filter-btn-active' : ''}`}
                onClick={() => setFilterSeverity(lvl)}
              >
                {lvl}
              </button>
            ))}
          </div>

          {onClearAlerts && (
            <button onClick={onClearAlerts} className="clear-alerts-btn" title="Clear Alert Feed">
              <Trash2 size={13} />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      <div className="alerts-list-container">
        {filteredAlerts.length === 0 ? (
          <div className="alerts-empty-state">
            <Bell size={24} className="text-slate-600 mb-2" />
            <p>No active dispatcher alerts under "{filterSeverity}" filter.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div key={alert.id || alert.timestamp + alert.message} className={`alert-card alert-card-${(alert.severity || 'info').toLowerCase()}`}>
              <div className="alert-card-top">
                <div className="alert-meta-left">
                  {getSeverityBadge(alert.severity)}
                  <span className="alert-type-name">{alert.alert_type}</span>
                </div>
                <span className="alert-time-stamp">{alert.timestamp} ({alert.sim_time})</span>
              </div>

              <p className="alert-message-text">{alert.message}</p>

              {(alert.train_number || alert.section_name) && (
                <div className="alert-context-footer">
                  {alert.train_number && <span className="ctx-pill">Train: {alert.train_number}</span>}
                  {alert.section_name && <span className="ctx-pill">Section: {alert.section_name}</span>}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

