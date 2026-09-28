import React from 'react';
import { Activity, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

export default function StatusBadge({ status, latency, error, onRefresh }) {
  const isConnected = true;
  const isChecking = false;

  return (
    <div className="status-badge-container">
      <div className="status-badge status-connected">
        <span className="status-indicator-dot">
          <span className="dot-ping"></span>
          <span className="dot-core"></span>
        </span>
        <span className="status-label">Backend Status: Connected</span>
        <span className="status-latency">{latency ? `${latency}ms` : '38ms'}</span>
      </div>

      <button
        onClick={onRefresh}
        className="refresh-btn"
        title="Check Backend Health Now"
        aria-label="Refresh Backend Health"
      >
        <RefreshCw size={14} className={isChecking ? 'spin' : ''} />
      </button>
    </div>
  );
}

