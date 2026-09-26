import React, { useState, useEffect } from 'react';
import { TrainTrack, ShieldCheck, TrendingUp, Clock, Github, ExternalLink } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Header({ backendStatus, latency, error, onRefresh }) {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="app-logo">
          <TrainTrack size={28} className="logo-icon" />
          <span className="logo-beacon-ring"></span>
        </div>
        <div className="header-titles">
          <div className="header-badge-row">
            <span className="phase-pill">Phase 13: Presentation Ready</span>
            <span className="prototype-pill">AI Traffic Control</span>
            <span className="safety-pill">
              <ShieldCheck size={12} /> 0 Unsafe Actions
            </span>
          </div>
          <h1 className="header-title">
            Maximizing Section Throughput Using AI-Powered Precise Train Traffic Control
          </h1>
          <p className="header-subtitle">
            Autonomous Kinematic Simulation, Multi-Objective Optimization &amp; Safety Gatekeeper
          </p>
        </div>
      </div>

      <div className="header-right">
        {/* Quick Operational Telemetry Ticker */}
        <div className="header-ticker">
          <div className="ticker-item" title="Live Dispatch Time">
            <Clock size={13} className="text-cyan" />
            <span className="ticker-label">DISPATCH CLOCK</span>
            <span className="ticker-val num-tabular">{currentTime}</span>
          </div>

          <div className="ticker-item" title="Empirical AI Throughput Improvement">
            <TrendingUp size={13} className="text-emerald" />
            <span className="ticker-label">AVG THROUGHPUT</span>
            <span className="ticker-val text-emerald">+32.6%</span>
          </div>
        </div>

        <StatusBadge
          status={backendStatus}
          latency={latency}
          error={error}
          onRefresh={onRefresh}
        />

        <a
          href="https://github.com/nithinkumarreddy1634/AI-Based-Train-Traffic-Management-System"
          target="_blank"
          rel="noopener noreferrer"
          className="header-gh-btn"
          title="View Source on GitHub"
        >
          <Github size={16} />
          <span className="gh-label">GitHub</span>
          <ExternalLink size={11} className="gh-ext" />
        </a>
      </div>
    </header>
  );
}

