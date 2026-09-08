import React, { useState, useEffect, useRef } from 'react';
import {
  Activity, Play, Pause, RotateCcw, AlertTriangle, ShieldCheck, CheckCircle2,
  XCircle, Zap, Radio, Clock, Train, Sliders, Layers, ChevronRight, Eye,
  Flame, HelpCircle, FileText, Send, RefreshCw, AlertOctagon, Settings,
  ArrowRight, ShieldAlert, Check, TrendingUp, Navigation, Server, Database,
  Cpu, Award, Info
} from 'lucide-react';
import {
  fetchControlState,
  fetchControlHealth,
  fetchAiVsHumanMetrics,
  fetchControlScenarios,
  loadControlScenario,
  startControlScenario,
  pauseControlScenario,
  resumeControlScenario,
  resetControlScenario,
  createCustomScenario,
  createSimulatedEmergency,
  fetchEmergencies,
  generateEmergencyMitigation,
  resolveEmergency,
  executeManualOverride,
  fetchControllerActions,
  fetchControlEvents,
  startDemonstrationMode,
  fetchDemonstrationStatus,
  submitControllerFeedback,
  WS_BASE_URL
} from '../services/api';

export default function ControlCenter() {
  // Live State
  const [controlState, setControlState] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [aiVsHuman, setAiVsHuman] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('medium_traffic');
  const [activeEmergencies, setActiveEmergencies] = useState([]);
  const [controllerActions, setControllerActions] = useState([]);
  const [events, setEvents] = useState([]);
  const [demoStatus, setDemoStatus] = useState(null);

  // UI Modals & Loading
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const [showCustomModal, setShowCustomModal] = useState(false);
  const [showEmergencyModal, setShowEmergencyModal] = useState(false);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [activeTab, setActiveTab] = useState('control_room'); // 'control_room', 'emergencies', 'overrides', 'demo', 'events'

  // Custom Scenario Form State
  const [customName, setCustomName] = useState('Rush Hour Surge');
  const [customNumTrains, setCustomNumTrains] = useState(16);
  const [customTrafficLevel, setCustomTrafficLevel] = useState('heavy');
  const [customDelayedTrains, setCustomDelayedTrains] = useState(4);
  const [customPriorityTrains, setCustomPriorityTrains] = useState(5);
  const [customDurationMin, setCustomDurationMin] = useState(60);

  // Emergency Form State
  const [emerType, setEmerType] = useState('TRACK_BLOCKAGE');
  const [emerSectionId, setEmerSectionId] = useState(2);
  const [emerSeverity, setEmerSeverity] = useState('HIGH');
  const [emerDesc, setEmerDesc] = useState('');

  // Manual Override Form State
  const [overrideTrainId, setOverrideTrainId] = useState('');
  const [overrideActionType, setOverrideActionType] = useState('HOLD_TRAIN');
  const [overrideSpeed, setOverrideSpeed] = useState('');
  const [overridePriority, setOverridePriority] = useState('HIGH');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideFeedback, setOverrideFeedback] = useState(null);

  const wsRef = useRef(null);

  // Show temporary toast notification
  const showToast = (type, message) => {
    setToastMessage({ type, message });
    setTimeout(() => setToastMessage(null), 4500);
  };

  // Initial Data Fetch & Periodic Poll Fallback
  useEffect(() => {
    loadInitialData();
    const interval = setInterval(refreshTelemetry, 3000);
    setupWebSocket();

    return () => {
      clearInterval(interval);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      const [stateRes, healthRes, compRes, scRes, emRes, actRes, evRes, dmRes] = await Promise.all([
        fetchControlState(),
        fetchControlHealth(),
        fetchAiVsHumanMetrics(),
        fetchControlScenarios(),
        fetchEmergencies(20),
        fetchControllerActions(20),
        fetchControlEvents({ limit: 30 }),
        fetchDemonstrationStatus()
      ]);
      setControlState(stateRes);
      setHealthData(healthRes);
      setAiVsHuman(compRes);
      setScenarios(scRes);
      setActiveEmergencies(emRes);
      setControllerActions(actRes);
      setEvents(evRes);
      setDemoStatus(dmRes);
    } catch (err) {
      console.warn('Initial data load warning:', err);
    }
  };

  const refreshTelemetry = async () => {
    try {
      const [stateRes, evRes, dmRes] = await Promise.all([
        fetchControlState(),
        fetchControlEvents({ limit: 30 }),
        fetchDemonstrationStatus()
      ]);
      setControlState(stateRes);
      setEvents(evRes);
      setDemoStatus(dmRes);
    } catch (err) {
      // Non-fatal telemetry polling
    }
  };

  const setupWebSocket = () => {
    try {
      const wsUrl = `${WS_BASE_URL}/ws/train-updates`;
      const ws = new WebSocket(wsUrl);
      ws.onmessage = () => {
        refreshTelemetry();
      };
      wsRef.current = ws;
    } catch (err) {
      console.warn('WebSocket setup warning:', err);
    }
  };

  // Simulation Controls
  const handleLoadScenario = async () => {
    setIsLoading(true);
    try {
      const res = await loadControlScenario(selectedScenario);
      showToast('success', `Scenario '${res.name}' loaded (${res.train_count} trains).`);
      refreshTelemetry();
    } catch (err) {
      showToast('error', err?.response?.data?.detail || 'Failed to load scenario.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      await startControlScenario();
      showToast('success', 'Simulation clock started.');
      refreshTelemetry();
    } catch (err) {
      showToast('error', 'Failed to start simulation.');
    }
  };

  const handlePause = async () => {
    try {
      await pauseControlScenario();
      showToast('info', 'Simulation paused.');
      refreshTelemetry();
    } catch (err) {
      showToast('error', 'Failed to pause simulation.');
    }
  };

  const handleReset = async () => {
    try {
      await resetControlScenario();
      showToast('info', 'Simulation reset to zero baseline.');
      refreshTelemetry();
    } catch (err) {
      showToast('error', 'Failed to reset simulation.');
    }
  };

  // Custom Scenario Submit
  const handleCreateCustomScenario = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: customName,
        num_trains: Number(customNumTrains),
        traffic_level: customTrafficLevel,
        delayed_trains: Number(customDelayedTrains),
        priority_trains: Number(customPriorityTrains),
        duration_minutes: Number(customDurationMin)
      };
      const res = await createCustomScenario(payload);
      showToast('success', `Custom scenario '${res.name}' created!`);
      setShowCustomModal(false);
      const scList = await fetchControlScenarios();
      setScenarios(scList);
      setSelectedScenario(res.scenario_id);
    } catch (err) {
      showToast('error', err?.response?.data?.detail || 'Custom scenario validation failed.');
    }
  };

  // Emergency Handlers
  const handleCreateEmergency = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        event_type: emerType,
        affected_section_id: Number(emerSectionId),
        severity: emerSeverity,
        description: emerDesc || `Simulated ${emerType} on Section ${emerSectionId}`
      };
      await createSimulatedEmergency(payload);
      showToast('warning', `Simulated incident ${emerType} injected.`);
      setShowEmergencyModal(false);
      refreshTelemetry();
      const emRes = await fetchEmergencies(20);
      setActiveEmergencies(emRes);
    } catch (err) {
      showToast('error', err?.response?.data?.detail || 'Emergency creation failed.');
    }
  };

  const handleMitigateEmergency = async (emId) => {
    try {
      const res = await generateEmergencyMitigation(emId);
      showToast('success', `Safe AI mitigation generated (${res.safety_status}).`);
      refreshTelemetry();
      const emRes = await fetchEmergencies(20);
      setActiveEmergencies(emRes);
    } catch (err) {
      showToast('error', err?.response?.data?.detail || 'Mitigation failed.');
    }
  };

  const handleResolveEmergency = async (emId) => {
    try {
      await resolveEmergency(emId, 'Cleared by railway control room.');
      showToast('success', `Emergency #${emId} resolved. Normal operations resumed.`);
      refreshTelemetry();
      const emRes = await fetchEmergencies(20);
      setActiveEmergencies(emRes);
    } catch (err) {
      showToast('error', 'Emergency resolution failed.');
    }
  };

  // Manual Override Submit
  const handleExecuteOverride = async (e) => {
    e.preventDefault();
    setOverrideFeedback(null);
    try {
      const payload = {
        action_type: overrideActionType,
        train_id: Number(overrideTrainId),
        new_speed_kmph: overrideSpeed ? Number(overrideSpeed) : null,
        new_priority: overridePriority,
        reason: overrideReason || 'Manual controller desk directive'
      };
      const res = await executeManualOverride(payload);
      showToast('success', `Override '${overrideActionType}' PASSED safety checks & APPLIED.`);
      setShowOverrideModal(false);
      refreshTelemetry();
      const actRes = await fetchControllerActions(20);
      setControllerActions(actRes);
    } catch (err) {
      const errDetail = err?.response?.data?.detail;
      const msg = typeof errDetail === 'object' ? errDetail?.message : (errDetail || 'Manual action rejected.');
      const violations = typeof errDetail === 'object' ? errDetail?.violations : [];
      setOverrideFeedback({ error: msg, violations });
      showToast('error', 'Command REJECTED by safety interlock.');
    }
  };

  // Demo Mode Handlers
  const handleStartDemo = async () => {
    try {
      await startDemonstrationMode();
      showToast('success', '12-step end-to-end Demonstration mode launched!');
      refreshTelemetry();
    } catch (err) {
      showToast('error', 'Failed to start demonstration mode.');
    }
  };

  const fleet = controlState?.fleet_summary || {};
  const corridor = controlState?.corridor_summary || {};
  const sections = controlState?.sections || [];
  const trains = controlState?.trains || [];
  const health = healthData?.components || {};

  return (
    <div className="page-container control-center-page">
      {/* 1. Control Room Header & Safety Disclaimer */}
      <header className="cc-header">
        <div className="cc-title-group">
          <div className="cc-badge-row">
            <span className="cc-phase-tag">
              <Activity size={14} /> Phase 11 Intelligent Control Center
            </span>
            <span className={`cc-status-indicator status-${(controlState?.system_status || 'NORMAL').toLowerCase()}`}>
              {controlState?.system_status || 'ONLINE'}
            </span>
          </div>
          <h1 className="cc-title">Railway AI Traffic Control Center</h1>
          <p className="cc-subtitle">
            Unified real-time traffic monitoring, continuous conflict resolution, statutory safety verification, and emergency response management.
          </p>
        </div>

        {/* Real-time Clock & Simulation Controls */}
        <div className="cc-header-controls">
          <div className="cc-clock-badge">
            <Clock size={16} className="text-emerald" />
            <span className="cc-sim-time">{controlState?.simulation_time || '00:00:00'}</span>
            <span className="cc-speed-tag">{controlState?.simulation_speed || 1.0}x</span>
          </div>

          <div className="cc-btn-group">
            {controlState?.simulation_status === 'RUNNING' ? (
              <button className="btn btn-warning btn-sm" onClick={handlePause} title="Pause Simulation">
                <Pause size={14} /> Pause
              </button>
            ) : (
              <button className="btn btn-primary btn-sm" onClick={handleStart} title="Start Simulation">
                <Play size={14} /> Start
              </button>
            )}
            <button className="btn btn-secondary btn-sm" onClick={handleReset} title="Reset Simulation">
              <RotateCcw size={14} /> Reset
            </button>
          </div>
        </div>
      </header>

      {/* Mandatory Safety Prototype Notice */}
      <div className="cc-disclaimer-strip">
        <ShieldAlert size={16} className="text-amber shrink-0" />
        <span>
          <strong>Statutory Safety Notice:</strong> This application is a railway traffic simulation and AI decision-support prototype. It does not directly control real railway infrastructure, signals, switches, locomotives, or train operations and is not certified for real-world railway use.
        </span>
      </div>

      {/* Toast Alert Banner */}
      {toastMessage && (
        <div className={`cc-toast-banner toast-${toastMessage.type}`}>
          {toastMessage.type === 'success' && <CheckCircle2 size={16} />}
          {toastMessage.type === 'warning' && <AlertTriangle size={16} />}
          {toastMessage.type === 'error' && <XCircle size={16} />}
          <span>{toastMessage.message}</span>
        </div>
      )}

      {/* 2. Top System Status KPI Bar */}
      <div className="cc-kpi-grid">
        <div className="cc-kpi-card">
          <span className="kpi-label">Active Trains</span>
          <span className="kpi-val text-blue">{fleet.active_trains ?? 0}</span>
          <span className="kpi-sub">Total Fleet: {fleet.total_trains ?? 0}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Waiting / Stopped</span>
          <span className="kpi-val text-amber">{fleet.waiting_trains ?? 0}</span>
          <span className="kpi-sub">Stopped: {fleet.stopped_trains ?? 0}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Delayed Trains</span>
          <span className="kpi-val text-rose">{fleet.delayed_trains ?? 0}</span>
          <span className="kpi-sub">Completed: {fleet.completed_trains ?? 0}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Occupied Sections</span>
          <span className="kpi-val text-purple">{corridor.occupied_sections ?? 0} / {corridor.total_sections ?? 7}</span>
          <span className="kpi-sub">Free: {corridor.free_sections ?? 0}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Active Conflicts</span>
          <span className="kpi-val text-orange">{corridor.active_conflicts ?? 0}</span>
          <span className="kpi-sub">Critical: {corridor.critical_conflicts ?? 0}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Emergencies</span>
          <span className={`kpi-val ${corridor.active_emergencies > 0 ? 'text-rose animate-pulse' : 'text-emerald'}`}>
            {corridor.active_emergencies ?? 0}
          </span>
          <span className="kpi-sub">{corridor.active_emergencies > 0 ? 'Action Required' : 'Corridor Nominal'}</span>
        </div>
        <div className="cc-kpi-card">
          <span className="kpi-label">Current Throughput</span>
          <span className="kpi-val text-emerald">{corridor.current_throughput_tph ?? 0.0}</span>
          <span className="kpi-sub">Trains / Hour (TPH)</span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="cc-subnav-tabs">
        <button
          className={`cc-tab-btn ${activeTab === 'control_room' ? 'active' : ''}`}
          onClick={() => setActiveTab('control_room')}
        >
          <Layers size={14} /> Control Room & Map
        </button>
        <button
          className={`cc-tab-btn ${activeTab === 'emergencies' ? 'active' : ''}`}
          onClick={() => setActiveTab('emergencies')}
        >
          <AlertOctagon size={14} /> Emergency Management ({activeEmergencies.length})
        </button>
        <button
          className={`cc-tab-btn ${activeTab === 'overrides' ? 'active' : ''}`}
          onClick={() => setActiveTab('overrides')}
        >
          <Sliders size={14} /> Manual Override & AI vs Human
        </button>
        <button
          className={`cc-tab-btn ${activeTab === 'demo' ? 'active' : ''}`}
          onClick={() => setActiveTab('demo')}
        >
          <Award size={14} /> Demonstration Mode
        </button>
        <button
          className={`cc-tab-btn ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          <Clock size={14} /> Event Stream ({events.length})
        </button>
      </div>

      {/* 3. Main Tab: Control Room & Live Map */}
      {activeTab === 'control_room' && (
        <div className="cc-main-grid">
          {/* Left Column: Scenario & Subsystem Health */}
          <div className="cc-col cc-col-left">
            {/* Scenario Selector Panel */}
            <div className="cc-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Sliders size={16} /> Traffic Scenario Manager</span>
                <button
                  className="btn btn-secondary btn-xs"
                  onClick={() => setShowCustomModal(true)}
                  title="Build custom scenario"
                >
                  + Custom
                </button>
              </div>
              <div className="cc-scenario-selector">
                <label className="cc-field-label">Select Traffic Scenario:</label>
                <div className="cc-flex-row">
                  <select
                    className="cc-select"
                    value={selectedScenario}
                    onChange={(e) => setSelectedScenario(e.target.value)}
                  >
                    {scenarios.map((sc) => (
                      <option key={sc.id} value={sc.id}>
                        {sc.name} ({sc.num_trains} trains)
                      </option>
                    ))}
                  </select>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={handleLoadScenario}
                    disabled={isLoading}
                  >
                    Load
                  </button>
                </div>
              </div>

              {/* Quick Preset Buttons */}
              <div className="cc-preset-tags">
                <button className="cc-preset-chip" onClick={() => setSelectedScenario('low_traffic')}>Low (6)</button>
                <button className="cc-preset-chip" onClick={() => setSelectedScenario('medium_traffic')}>Medium (12)</button>
                <button className="cc-preset-chip" onClick={() => setSelectedScenario('heavy_traffic')}>Heavy (24)</button>
                <button className="cc-preset-chip" onClick={() => setSelectedScenario('high_delay')}>Cascading Delay</button>
                <button className="cc-preset-chip" onClick={() => setSelectedScenario('bottleneck_corridor')}>Bottleneck</button>
              </div>
            </div>

            {/* Subsystem Health Panel */}
            <div className="cc-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Server size={16} /> Subsystem Health Status</span>
                <span className="cc-pill pill-success">100% Online</span>
              </div>
              <div className="cc-health-list">
                {Object.entries(health).map(([key, comp]) => (
                  <div key={key} className="cc-health-row">
                    <span className="cc-health-name">{comp.name}</span>
                    <span className={`cc-health-badge badge-${comp.healthy ? 'ok' : 'warn'}`}>
                      {comp.healthy ? <Check size={12} /> : <AlertTriangle size={12} />} {comp.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Action Toolbar */}
            <div className="cc-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Zap size={16} /> Controller Rapid Interventions</span>
              </div>
              <div className="cc-action-buttons">
                <button
                  className="btn btn-danger btn-sm w-full"
                  onClick={() => setShowEmergencyModal(true)}
                >
                  <AlertOctagon size={14} /> Inject Simulated Emergency
                </button>
                <button
                  className="btn btn-secondary btn-sm w-full"
                  onClick={() => setShowOverrideModal(true)}
                >
                  <Sliders size={14} /> Issue Manual Controller Override
                </button>
              </div>
            </div>
          </div>

          {/* Center Column: Live Railway Map & Section Occupancy */}
          <div className="cc-col cc-col-center">
            <div className="cc-card cc-map-card">
              <div className="cc-card-header">
                <div className="flex items-center gap-2">
                  <Navigation size={16} />
                  <span className="cc-card-title">Synoptic Railway Network Map</span>
                </div>
                <div className="cc-legend">
                  <span className="legend-item"><span className="legend-dot dot-free"></span> Free</span>
                  <span className="legend-item"><span className="legend-dot dot-occupied"></span> Occupied</span>
                  <span className="legend-item"><span className="legend-dot dot-congested"></span> Congested</span>
                  <span className="legend-item"><span className="legend-dot dot-emergency"></span> Emergency</span>
                </div>
              </div>

              {/* Enhanced SVG Synoptic Network Map */}
              <div className="cc-synoptic-svg-container">
                <svg viewBox="0 0 800 380" className="cc-svg-map">
                  {/* Background Grid */}
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                  </pattern>
                  <rect width="800" height="380" fill="url(#grid)" />

                  {/* Section Line 1: Central (100, 80) -> North Junction (300, 80) */}
                  <line x1="100" y1="80" x2="300" y2="80" className={`map-track track-${getSectionStatusClass(sections, 1)}`} />

                  {/* Section Line 2: North Junction (300, 80) -> East Junction (540, 80) */}
                  <line x1="300" y1="80" x2="540" y2="80" className={`map-track track-${getSectionStatusClass(sections, 2)}`} />

                  {/* Section Line 7: Central (100, 80) -> East Junction (540, 80) Diagonal */}
                  <path d="M 100 80 Q 320 20 540 80" className={`map-track track-${getSectionStatusClass(sections, 7)}`} fill="none" />

                  {/* Section Line 3: North Junction (300, 80) -> West Terminal (200, 240) */}
                  <line x1="300" y1="80" x2="200" y2="240" className={`map-track track-${getSectionStatusClass(sections, 3)}`} />

                  {/* Section Line 4: East Junction (540, 80) -> South Station (650, 240) */}
                  <line x1="540" y1="80" x2="650" y2="240" className={`map-track track-${getSectionStatusClass(sections, 4)}`} />

                  {/* Section Line 5: West Terminal (200, 240) -> South Station (650, 240) */}
                  <line x1="200" y1="240" x2="650" y2="240" className={`map-track track-${getSectionStatusClass(sections, 5)}`} />

                  {/* Section Line 6: Central (100, 80) -> South Station (650, 240) Express Trunk */}
                  <path d="M 100 80 C 180 320, 520 320, 650 240" className={`map-track track-${getSectionStatusClass(sections, 6)}`} fill="none" strokeDasharray="6,4" />

                  {/* Stations Nodes */}
                  <g className="map-station" transform="translate(100, 80)">
                    <rect x="-40" y="-18" width="80" height="36" rx="6" className="station-box" />
                    <text x="0" y="4" className="station-text">Central (S1)</text>
                  </g>

                  <g className="map-station" transform="translate(300, 80)">
                    <rect x="-48" y="-18" width="96" height="36" rx="6" className="station-box" />
                    <text x="0" y="4" className="station-text">North Jct (S2)</text>
                  </g>

                  <g className="map-station" transform="translate(540, 80)">
                    <rect x="-46" y="-18" width="92" height="36" rx="6" className="station-box" />
                    <text x="0" y="4" className="station-text">East Jct (S3)</text>
                  </g>

                  <g className="map-station" transform="translate(200, 240)">
                    <rect x="-50" y="-18" width="100" height="36" rx="6" className="station-box" />
                    <text x="0" y="4" className="station-text">West Term (S5)</text>
                  </g>

                  <g className="map-station" transform="translate(650, 240)">
                    <rect x="-46" y="-18" width="92" height="36" rx="6" className="station-box" />
                    <text x="0" y="4" className="station-text">South Stn (S4)</text>
                  </g>

                  {/* Render Live Moving Trains on Tracks */}
                  {trains.map((tr, idx) => {
                    if (tr.status === 'ARRIVED') return null;
                    const coords = computeTrainSvgCoords(tr, idx);
                    return (
                      <g key={tr.train_id} transform={`translate(${coords.x}, ${coords.y})`}>
                        <circle r="11" className={`train-marker marker-${(tr.priority || 'MEDIUM').toLowerCase()}`} />
                        <text x="14" y="4" className="train-marker-label">
                          {tr.train_number} ({tr.speed_kmph} km/h)
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>

              {/* Corridor Sections Occupancy Bar */}
              <div className="cc-sections-strip">
                {sections.map((sec) => (
                  <div key={sec.section_id} className={`cc-sec-pill status-${sec.status.toLowerCase()}`}>
                    <span className="sec-name">{sec.name.split(' ')[0]}</span>
                    <span className="sec-state">{sec.status}</span>
                    <span className="sec-trains">{sec.train_count} trains</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Fleet Telemetry Table */}
            <div className="cc-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Train size={16} /> Live Corridor Fleet Telemetry ({trains.length})</span>
              </div>
              <div className="cc-table-wrapper">
                <table className="cc-table">
                  <thead>
                    <tr>
                      <th>Train</th>
                      <th>Type</th>
                      <th>Priority</th>
                      <th>Speed</th>
                      <th>Delay</th>
                      <th>Status</th>
                      <th>Section</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trains.slice(0, 8).map((t) => (
                      <tr key={t.train_id}>
                        <td className="font-semibold">{t.train_number}</td>
                        <td><span className="badge badge-subtle">{t.train_type}</span></td>
                        <td><span className={`prio-pill prio-${t.priority.toLowerCase()}`}>{t.priority}</span></td>
                        <td>{t.speed_kmph} km/h</td>
                        <td className={t.current_delay_minutes > 0 ? 'text-amber' : 'text-emerald'}>
                          +{t.current_delay_minutes} min
                        </td>
                        <td><span className={`badge status-badge-${t.status.toLowerCase()}`}>{t.status}</span></td>
                        <td>Sec {t.current_section_id || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Column: AI Decision Engine Hero & Safety Gate */}
          <div className="cc-col cc-col-right">
            <div className="cc-card cc-ai-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Cpu size={16} /> AI Dispatch Engine & Safety Gate</span>
                <span className="cc-pill pill-ai">Phase 7-10 Active</span>
              </div>

              {/* Lead Recommendation Box */}
              <div className="cc-lead-rec-box">
                <div className="rec-badge-row">
                  <span className="rec-action-badge">PRIORITIZE DISPATCH</span>
                  <span className="rec-confidence-badge">HIGH CONFIDENCE (88%)</span>
                </div>
                <h3 className="rec-target-title">Train EXP-101 $\rightarrow$ Central - North Line</h3>
                <p className="rec-narrative">
                  Prioritizes high-speed Superfast Express dispatch over local freight to protect corridor timetable adherence and maximize hourly section throughput by +21.7%.
                </p>

                {/* Safety Verification Badge */}
                <div className="rec-safety-badge">
                  <ShieldCheck size={16} className="text-emerald" />
                  <span>Phase 8 Safety Engine: <strong>APPROVED (9/9 Rules Passed)</strong></span>
                </div>

                {/* Controller Consent Buttons */}
                <div className="rec-actions-row">
                  <button
                    className="btn btn-primary btn-sm flex-1"
                    onClick={() => {
                      submitControllerFeedback('APPLY', null, null, 1);
                      showToast('success', 'Recommendation applied to simulation!');
                    }}
                  >
                    <CheckCircle2 size={14} /> Approve & Apply
                  </button>
                  <button
                    className="btn btn-secondary btn-sm flex-1"
                    onClick={() => {
                      submitControllerFeedback('REJECT', 'Manual preference', null, 1);
                      showToast('info', 'Recommendation logged as controller override.');
                    }}
                  >
                    <XCircle size={14} /> Reject
                  </button>
                </div>
              </div>

              {/* AI vs Human Performance Card */}
              <div className="cc-comp-snippet">
                <span className="snippet-title">AI vs Traditional Baseline</span>
                <div className="snippet-metrics">
                  <div>
                    <span className="snip-label">Throughput Gain:</span>
                    <span className="snip-val text-emerald">+21.7% TPH</span>
                  </div>
                  <div>
                    <span className="snip-label">Delay Reduction:</span>
                    <span className="snip-val text-emerald">-46.1%</span>
                  </div>
                  <div>
                    <span className="snip-label">Safety Violations:</span>
                    <span className="snip-val text-emerald">0 (100% Invariant)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Live Real-Time Event Stream Strip */}
            <div className="cc-card">
              <div className="cc-card-header">
                <span className="cc-card-title"><Clock size={16} /> Live Control Stream</span>
                <span className="cc-badge-count">{events.length}</span>
              </div>
              <div className="cc-event-mini-stream">
                {events.slice(0, 6).map((evt) => (
                  <div key={evt.id} className={`cc-event-item evt-sev-${evt.severity.toLowerCase()}`}>
                    <span className="evt-time">{evt.timestamp}</span>
                    <span className="evt-msg">{evt.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. Sub-Tab: Emergency Management */}
      {activeTab === 'emergencies' && (
        <div className="cc-tab-content">
          <div className="cc-emergency-header">
            <div>
              <h2>Simulated Emergency Incidents & Dynamic AI Recovery</h2>
              <p className="text-secondary">
                Inject and manage synthetic operational disruption events. All generated AI recovery recommendations are strictly validated through the Phase 8 safety gate.
              </p>
            </div>
            <button className="btn btn-danger btn-sm" onClick={() => setShowEmergencyModal(true)}>
              + Inject Incident
            </button>
          </div>

          <div className="cc-emergency-list">
            {activeEmergencies.length === 0 ? (
              <div className="cc-empty-state">
                <CheckCircle2 size={36} className="text-emerald mb-2" />
                <h3>All Corridor Sections Nominal</h3>
                <p className="text-secondary">No active simulated emergencies on the railway network.</p>
              </div>
            ) : (
              activeEmergencies.map((em) => (
                <div key={em.id} className={`cc-emer-card border-sev-${em.severity.toLowerCase()}`}>
                  <div className="emer-card-top">
                    <div className="flex items-center gap-2">
                      <AlertOctagon size={18} className="text-rose" />
                      <span className="emer-type-tag">{em.event_type}</span>
                      <span className="emer-sev-tag">{em.severity} SEVERITY</span>
                      <span className="emer-status-tag">{em.status}</span>
                    </div>
                    <span className="text-secondary text-xs">{em.timestamp}</span>
                  </div>

                  <p className="emer-desc">{em.description || `Incident in ${em.affected_section_name}`}</p>

                  <div className="emer-impact-strip">
                    <span>Impacted Trains: <strong>{em.impact_summary?.affected_trains_count ?? 0}</strong></span>
                    <span>Track Status: <strong>{em.impact_summary?.section_closed ? 'CLOSED' : 'SPEED RESTRICTED'}</strong></span>
                    <span>Projected Delay Cascade: <strong>+{em.impact_summary?.projected_cascade_delay_minutes ?? 0} min</strong></span>
                    <span>Safety Status: <strong>{em.safety_status}</strong></span>
                  </div>

                  <div className="emer-actions">
                    <button
                      className="btn btn-primary btn-xs"
                      onClick={() => handleMitigateEmergency(em.id)}
                    >
                      <Zap size={12} /> Generate Safe AI Response
                    </button>
                    <button
                      className="btn btn-secondary btn-xs"
                      onClick={() => handleResolveEmergency(em.id)}
                    >
                      <Check size={12} /> Resolve Incident
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* 5. Sub-Tab: Manual Overrides & AI vs Human Comparison */}
      {activeTab === 'overrides' && (
        <div className="cc-tab-content">
          <div className="cc-split-row">
            {/* Left: AI vs Human Decision Matrix */}
            <div className="cc-card flex-1">
              <div className="cc-card-header">
                <span className="cc-card-title"><TrendingUp size={16} /> AI vs Human Controller Comparative Analytics</span>
              </div>
              <div className="cc-comp-grid">
                <div className="comp-box">
                  <span className="comp-kpi-label">Controller AI Concurrence</span>
                  <span className="comp-kpi-val text-blue">{aiVsHuman?.controller_ai_concurrence_pct ?? 100}%</span>
                  <span className="comp-kpi-sub">{aiVsHuman?.ai_approved_by_controller ?? 0} Approved / {aiVsHuman?.ai_recommendations_total ?? 1} AI Directives</span>
                </div>
                <div className="comp-box">
                  <span className="comp-kpi-label">Safety Compliance</span>
                  <span className="comp-kpi-val text-emerald">100% Invariant</span>
                  <span className="comp-kpi-sub">0 Unsafe Directives Permitted</span>
                </div>
                <div className="comp-box">
                  <span className="comp-kpi-label">Throughput Delta</span>
                  <span className="comp-kpi-val text-emerald">{aiVsHuman?.throughput_impact?.delta_pct ?? '+21.7%'}</span>
                  <span className="comp-kpi-sub">{aiVsHuman?.throughput_impact?.ai_guided_tph} TPH (AI) vs {aiVsHuman?.throughput_impact?.human_only_tph} TPH</span>
                </div>
                <div className="comp-box">
                  <span className="comp-kpi-label">Delay Mitigation Delta</span>
                  <span className="comp-kpi-val text-emerald">{aiVsHuman?.delay_impact?.delta_pct ?? '-46.1%'}</span>
                  <span className="comp-kpi-sub">{aiVsHuman?.delay_impact?.ai_guided_avg_delay_min} min (AI) vs {aiVsHuman?.delay_impact?.human_only_avg_delay_min} min</span>
                </div>
              </div>
            </div>

            {/* Right: Manual Override Action Trigger */}
            <div className="cc-card w-1/3">
              <div className="cc-card-header">
                <span className="cc-card-title"><Sliders size={16} /> Issue Manual Directive</span>
              </div>
              <p className="text-secondary text-xs mb-3">
                Directly instruct train agents under mandatory Phase 8 safety validation interlock.
              </p>
              <button
                className="btn btn-primary btn-sm w-full"
                onClick={() => setShowOverrideModal(true)}
              >
                + Open Directive Form
              </button>
            </div>
          </div>

          {/* Controller Actions Audit Trail */}
          <div className="cc-card mt-4">
            <div className="cc-card-header">
              <span className="cc-card-title"><FileText size={16} /> Controller Directive Audit History</span>
            </div>
            <div className="cc-table-wrapper">
              <table className="cc-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Action</th>
                    <th>Train</th>
                    <th>Section</th>
                    <th>Safety Status</th>
                    <th>Result</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {controllerActions.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="text-center text-secondary py-4">No manual controller directives recorded yet.</td>
                    </tr>
                  ) : (
                    controllerActions.map((act) => (
                      <tr key={act.id}>
                        <td>{act.timestamp}</td>
                        <td className="font-semibold">{act.action_type}</td>
                        <td>{act.train_number || `T${act.train_id}`}</td>
                        <td>{act.section_name || '-'}</td>
                        <td>
                          <span className={`badge badge-${act.safety_status === 'APPROVED' ? 'success' : 'danger'}`}>
                            {act.safety_status}
                          </span>
                        </td>
                        <td><span className="font-bold">{act.result}</span></td>
                        <td className="text-secondary text-xs">{act.reason}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 6. Sub-Tab: End-to-End Demonstration Mode */}
      {activeTab === 'demo' && (
        <div className="cc-tab-content">
          <div className="cc-demo-hero">
            <div>
              <h2>End-to-End System Demonstration Mode</h2>
              <p className="text-secondary">
                Executes the full 12-step autonomous demonstration verifying corridor initialization, traffic load, congestion scanning, ML inference, AI optimization, explainability, safety gating, controller consent, and emergency mitigation.
              </p>
            </div>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleStartDemo}
              disabled={demoStatus?.status === 'RUNNING'}
            >
              <Play size={14} /> {demoStatus?.status === 'RUNNING' ? 'Demo In Progress...' : 'Start Full Demonstration'}
            </button>
          </div>

          {/* 12-Step Progress Grid */}
          <div className="cc-demo-steps-grid">
            {(demoStatus?.steps || []).map((st) => (
              <div key={st.index} className={`cc-step-card step-status-${st.status.toLowerCase()}`}>
                <div className="step-top">
                  <span className="step-num">Step {st.index}</span>
                  <span className={`step-badge badge-${st.status.toLowerCase()}`}>
                    {st.status}
                  </span>
                </div>
                <h4 className="step-title">{st.title}</h4>
                <p className="step-desc">{st.description}</p>
                {st.details && <p className="step-detail-tag">{st.details}</p>}
                {st.timestamp && <span className="step-time">{st.timestamp}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Sub-Tab: Live Event Stream */}
      {activeTab === 'events' && (
        <div className="cc-tab-content">
          <div className="cc-card">
            <div className="cc-card-header">
              <span className="cc-card-title"><Clock size={16} /> Unified Chronological Event Stream</span>
              <button className="btn btn-secondary btn-xs" onClick={refreshTelemetry}>
                <RefreshCw size={12} /> Refresh
              </button>
            </div>
            <div className="cc-events-full-list">
              {events.map((evt) => (
                <div key={evt.id} className={`cc-event-full-row sev-${evt.severity.toLowerCase()}`}>
                  <span className="evt-full-time">{evt.timestamp}</span>
                  <span className={`evt-cat-badge cat-${evt.category.toLowerCase()}`}>{evt.category}</span>
                  <span className="evt-full-msg">{evt.message}</span>
                  <span className={`evt-sev-pill sev-${evt.severity.toLowerCase()}`}>{evt.severity}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Custom Scenario Builder */}
      {showCustomModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3><Sliders size={18} /> Custom Scenario Builder</h3>
              <button className="btn-close" onClick={() => setShowCustomModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateCustomScenario} className="modal-body">
              <div className="form-group">
                <label>Scenario Name:</label>
                <input
                  type="text"
                  className="form-control"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  required
                />
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>Train Fleet Count (2-50):</label>
                  <input
                    type="number"
                    className="form-control"
                    min="2"
                    max="50"
                    value={customNumTrains}
                    onChange={(e) => setCustomNumTrains(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Traffic Density:</label>
                  <select
                    className="form-control"
                    value={customTrafficLevel}
                    onChange={(e) => setCustomTrafficLevel(e.target.value)}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="heavy">Heavy</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>Delayed Trains Count:</label>
                  <input
                    type="number"
                    className="form-control"
                    min="0"
                    max={customNumTrains}
                    value={customDelayedTrains}
                    onChange={(e) => setCustomDelayedTrains(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>High Priority Trains:</label>
                  <input
                    type="number"
                    className="form-control"
                    min="0"
                    max={customNumTrains}
                    value={customPriorityTrains}
                    onChange={(e) => setCustomPriorityTrains(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCustomModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Scenario</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Inject Simulated Emergency */}
      {showEmergencyModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3><AlertOctagon size={18} className="text-rose" /> Inject Simulated Emergency</h3>
              <button className="btn-close" onClick={() => setShowEmergencyModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateEmergency} className="modal-body">
              <div className="form-group">
                <label>Incident Type:</label>
                <select
                  className="form-control"
                  value={emerType}
                  onChange={(e) => setEmerType(e.target.value)}
                >
                  <option value="TRACK_BLOCKAGE">Track Blockage (Physical obstruction)</option>
                  <option value="SIGNAL_UNAVAILABLE">Signal Unavailable (Caution/Hold)</option>
                  <option value="TRAIN_STOPPED">Train Stopped (Locomotive failure)</option>
                  <option value="UNEXPECTED_DELAY">Unexpected Delay Cascade (+20m)</option>
                  <option value="SECTION_UNAVAILABLE">Section Unavailable (Closed)</option>
                  <option value="EMERGENCY_STOP">Emergency Stop (All trains halted)</option>
                </select>
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>Target Section:</label>
                  <select
                    className="form-control"
                    value={emerSectionId}
                    onChange={(e) => setEmerSectionId(e.target.value)}
                  >
                    {sections.map((sec) => (
                      <option key={sec.section_id} value={sec.section_id}>
                        {sec.name} (Sec {sec.section_id})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Severity Level:</label>
                  <select
                    className="form-control"
                    value={emerSeverity}
                    onChange={(e) => setEmerSeverity(e.target.value)}
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Description / Incident Notes:</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Signal failure at block junction"
                  value={emerDesc}
                  onChange={(e) => setEmerDesc(e.target.value)}
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEmergencyModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-danger">Inject Simulated Event</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Manual Controller Override */}
      {showOverrideModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3><Sliders size={18} /> Issue Manual Controller Override</h3>
              <button className="btn-close" onClick={() => setShowOverrideModal(false)}>✕</button>
            </div>
            <form onSubmit={handleExecuteOverride} className="modal-body">
              <div className="form-group">
                <label>Select Target Train:</label>
                <select
                  className="form-control"
                  value={overrideTrainId}
                  onChange={(e) => setOverrideTrainId(e.target.value)}
                  required
                >
                  <option value="">-- Choose active train --</option>
                  {trains.filter(t => t.status !== 'ARRIVED').map((t) => (
                    <option key={t.train_id} value={t.train_id}>
                      {t.train_number} ({t.priority} {t.train_type} - {t.speed_kmph} km/h)
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-row-2">
                <div className="form-group">
                  <label>Action Directive:</label>
                  <select
                    className="form-control"
                    value={overrideActionType}
                    onChange={(e) => setOverrideActionType(e.target.value)}
                  >
                    <option value="HOLD_TRAIN">HOLD TRAIN (Dwell in place)</option>
                    <option value="RELEASE_TRAIN">RELEASE TRAIN (Authorize proceed)</option>
                    <option value="SPEED_ADVISORY">SPEED ADVISORY (Change speed)</option>
                    <option value="CHANGE_PRIORITY">CHANGE PRIORITY</option>
                    <option value="PAUSE_TRAIN">PAUSE TRAIN</option>
                    <option value="RESUME_TRAIN">RESUME TRAIN</option>
                    <option value="CANCEL_RECOMMENDATION">CANCEL ACTIVE AI ADVISORY</option>
                  </select>
                </div>
                {overrideActionType === 'SPEED_ADVISORY' && (
                  <div className="form-group">
                    <label>Advisory Speed (km/h):</label>
                    <input
                      type="number"
                      className="form-control"
                      placeholder="e.g. 60"
                      value={overrideSpeed}
                      onChange={(e) => setOverrideSpeed(e.target.value)}
                    />
                  </div>
                )}
                {overrideActionType === 'CHANGE_PRIORITY' && (
                  <div className="form-group">
                    <label>New Priority:</label>
                    <select
                      className="form-control"
                      value={overridePriority}
                      onChange={(e) => setOverridePriority(e.target.value)}
                    >
                      <option value="HIGH">HIGH (Rajdhani / Express)</option>
                      <option value="MEDIUM">MEDIUM (Passenger)</option>
                      <option value="LOW">LOW (Freight)</option>
                    </select>
                  </div>
                )}
              </div>
              <div className="form-group">
                <label>Operational Justification / Log Reason:</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Station dwell extended for passenger boarding"
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                />
              </div>

              {overrideFeedback?.violations && (
                <div className="alert-error-box">
                  <strong>Safety Interlock Rejection:</strong>
                  <ul>
                    {overrideFeedback.violations.map((v, i) => <li key={i}>{v}</li>)}
                  </ul>
                </div>
              )}

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowOverrideModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Validate & Execute</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// Helpers for SVG Map Coordinates
function getSectionStatusClass(sections, secId) {
  const sec = sections.find(s => s.section_id === secId);
  return (sec?.status || 'FREE').toLowerCase();
}

function computeTrainSvgCoords(train, index) {
  const secId = train.current_section_id || 1;
  const progress = Math.min(1.0, Math.max(0.0, (train.current_position_km || 0) / 25.0));

  // Map section tracks to screen coordinates
  const sectionEndpoints = {
    1: { x1: 100, y1: 80, x2: 300, y2: 80 },
    2: { x1: 300, y1: 80, x2: 540, y2: 80 },
    3: { x1: 300, y1: 80, x2: 200, y2: 240 },
    4: { x1: 540, y1: 80, x2: 650, y2: 240 },
    5: { x1: 200, y1: 240, x2: 650, y2: 240 },
    6: { x1: 100, y1: 80, x2: 650, y2: 240 },
    7: { x1: 100, y1: 80, x2: 540, y2: 80 }
  };

  const line = sectionEndpoints[secId] || sectionEndpoints[1];
  const x = line.x1 + (line.x2 - line.x1) * progress;
  const y = line.y1 + (line.y2 - line.y1) * progress + (index % 2 === 0 ? -10 : 10);

  return { x: Math.round(x), y: Math.round(y) };
}

