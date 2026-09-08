import React from 'react';
import { Play, Pause, RotateCcw, Zap, Clock, Activity, Radio } from 'lucide-react';

export default function SimulationControls({ simulation }) {
  const { status, isWsConnected, actionLoading, start, pause, resume, reset, setSpeed } = simulation;

  const isRunning = status?.running && !status?.paused;
  const isPaused = status?.running && status?.paused;
  const isIdle = !status?.running;
  const speed = status?.speed_multiplier || 1.0;
  const throughput = status?.throughput_trains_per_hour || 0.0;
  const simTime = status?.simulation_time || '00:00:00';

  const multipliers = [1.0, 2.0, 5.0, 10.0];

  return (
    <div className="sim-control-ribbon">
      <div className="sim-ribbon-left">
        {/* Status Indicator */}
        <div className={`sim-state-badge ${isRunning ? 'state-running' : isPaused ? 'state-paused' : 'state-idle'}`}>
          <span className="state-pulse-dot"></span>
          <span>{isRunning ? 'SIMULATION RUNNING' : isPaused ? 'SIMULATION PAUSED' : 'SIMULATION READY'}</span>
        </div>

        {/* Live Simulation Clock */}
        <div className="sim-clock-display" title="Elapsed Simulation Clock Time">
          <Clock size={15} className="clock-icon" />
          <span className="clock-label">Sim Time:</span>
          <span className="clock-digits">{simTime}</span>
        </div>

        {/* Throughput Metric */}
        <div className="sim-metric-pill" title="Trains cleared through corridor per simulation hour">
          <Activity size={14} className="text-emerald-400" />
          <span>Throughput: <strong>{throughput}</strong> trains/h</span>
        </div>
      </div>

      <div className="sim-ribbon-center">
        {/* Main Action Buttons */}
        {isIdle && (
          <button
            onClick={start}
            disabled={actionLoading}
            className="sim-btn sim-btn-start"
            title="Start Simulation Engine"
          >
            <Play size={16} />
            <span>Start</span>
          </button>
        )}

        {isRunning && (
          <button
            onClick={pause}
            disabled={actionLoading}
            className="sim-btn sim-btn-pause"
            title="Pause Train Movement"
          >
            <Pause size={16} />
            <span>Pause</span>
          </button>
        )}

        {isPaused && (
          <button
            onClick={resume}
            disabled={actionLoading}
            className="sim-btn sim-btn-resume"
            title="Resume Train Movement"
          >
            <Play size={16} />
            <span>Resume</span>
          </button>
        )}

        <button
          onClick={reset}
          disabled={actionLoading}
          className="sim-btn sim-btn-reset"
          title="Reset Simulation to Initial Scenario"
        >
          <RotateCcw size={15} />
          <span>Reset</span>
        </button>
      </div>

      <div className="sim-ribbon-right">
        {/* Speed Multipliers */}
        <div className="speed-selector-group">
          <div className="speed-group-label">
            <Zap size={13} />
            <span>Speed:</span>
          </div>
          <div className="speed-buttons">
            {multipliers.map((m) => (
              <button
                key={m}
                onClick={() => setSpeed(m)}
                className={`speed-pill-btn ${speed === m ? 'speed-pill-active' : ''}`}
                title={`Run at ${m}x speed`}
              >
                {m}x
              </button>
            ))}
          </div>
        </div>

        {/* WebSocket Telemetry Status */}
        <div
          className={`ws-indicator-pill ${isWsConnected ? 'ws-connected' : 'ws-polling'}`}
          title={isWsConnected ? 'Real-Time WebSocket Stream Connected' : 'Falling back to HTTP Polling'}
        >
          <Radio size={12} className={isWsConnected ? 'spin-slow' : ''} />
          <span>{isWsConnected ? 'Live WS' : 'Polling'}</span>
        </div>
      </div>
    </div>
  );
}

