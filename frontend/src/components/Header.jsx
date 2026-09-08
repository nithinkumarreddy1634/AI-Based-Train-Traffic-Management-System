import React from 'react';
import { TrainTrack } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Header({ backendStatus, latency, error, onRefresh }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="app-logo">
          <TrainTrack size={28} className="logo-icon" />
        </div>
        <div className="header-titles">
          <div className="header-badge-row">
            <span className="phase-pill">Phase 13: Verified &amp; Presentation Ready</span>
            <span className="prototype-pill">Simulation Prototype</span>
          </div>
          <h1 className="header-title">
            Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control
          </h1>
          <p className="header-subtitle">
            AI-Based Railway Traffic Simulation, Optimization and Decision Support System
          </p>
        </div>
      </div>

      <div className="header-right">
        <StatusBadge
          status={backendStatus}
          latency={latency}
          error={error}
          onRefresh={onRefresh}
        />
      </div>
    </header>
  );
}

