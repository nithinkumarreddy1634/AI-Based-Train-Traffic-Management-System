import React from 'react';
import { Activity, AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react';

export default function StatusBadge({ status, latency, error, onRefresh }) {
  const isConnected = status === 'connected';
  const isChecking = status === 'checking';

  return (
    <div className="status-badge-container">
      <div className={`status-badge status-${status}`}>
        <span className="status-indicator-dot">
          <span className="dot-ping"></span>
          <span className="dot-core"></span>
        </span>
        <span className="status-label">
          {isConnected && 'Backend Status: Connected'}
          {status === 'disconnected' && 'Backend Status: Disconnected'}
          {isChecking && 'Backend Status: Connecting...'}
        </span>
        {latency !== null && isConnected && (
          <span className="status-latency">{latency}ms</span>
        )}
      </div>

      <button
        onClick={onRefresh}
        className="refresh-btn"
        title="Check Backend Health Now"
        aria-label="Refresh Backend Health"
      >
        <RefreshCw size={14} className={isChecking ? 'spin' : ''} />
      </button>

      {status === 'disconnected' && error && (
        <div className="status-error-hint">
          <AlertTriangle size={13} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

