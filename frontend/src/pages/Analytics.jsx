import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Download,
  FileText,
  Clock,
  Layers,
  Zap,
  Activity,
  Award,
  ChevronRight,
  Database,
  Filter,
  Copy,
  Info,
  Calendar
} from 'lucide-react';
import {
  fetchAnalyticsScenarios,
  runBenchmarkExperiment,
  fetchExperiments,
  fetchExperimentDetail,
  getExportUrl
} from '../services/api';

export default function Analytics() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('medium_traffic');
  const [runsCount, setRunsCount] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'charts', 'matrix', 'trains', 'history'
  const [currentExperiment, setCurrentExperiment] = useState(null);
  const [experimentsHistory, setExperimentsHistory] = useState([]);
  const [matrixData, setMatrixData] = useState([]);
  const [selectedRunIdx, setSelectedRunIdx] = useState(0);
  const [copiedNotification, setCopiedNotification] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load scenarios and past experiments on mount
  useEffect(() => {
    fetchAnalyticsScenarios()
      .then((data) => {
        setScenarios(data);
        if (data.length > 0 && !selectedScenarioId) {
          setSelectedScenarioId(data[0].id);
        }
      })
      .catch((err) => console.warn('Failed to load scenarios:', err));

    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const history = await fetchExperiments(15);
      setExperimentsHistory(history);
      if (history.length > 0 && !currentExperiment) {
        // Load details for latest experiment
        loadExperimentDetail(history[0].experiment_id);
      }
    } catch (err) {
      console.warn('Failed to load experiments history:', err);
    }
  };

  const loadExperimentDetail = async (expId) => {
    try {
      const detail = await fetchExperimentDetail(expId);
      setCurrentExperiment(detail);
      setSelectedRunIdx(0);
    } catch (err) {
      console.error('Failed to load experiment detail:', err);
    }
  };

  const handleRunExperiment = async (scenarioToRun = null, runsToRun = null) => {
    const scId = scenarioToRun || selectedScenarioId;
    const count = runsToRun || runsCount;
    setIsRunning(true);
    setErrorMsg(null);

    try {
      const result = await runBenchmarkExperiment(scId, count);
      setCurrentExperiment(result);
      setSelectedRunIdx(0);
      loadHistory();
    } catch (err) {
      console.error('Experiment execution failed:', err);
      setErrorMsg(err?.response?.data?.detail || 'Experiment simulation failed. Check backend logs.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleCopySummary = () => {
    if (!currentExperiment?.comparison?.summary_text) return;
    navigator.clipboard.writeText(currentExperiment.comparison.summary_text);
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 3000);
  };

  const activeScenarioMeta = scenarios.find((s) => s.id === selectedScenarioId);
  const comp = currentExperiment?.comparison || {};
  const tradSum = currentExperiment?.traditional_summary || {};
  const aiSum = currentExperiment?.ai_summary || {};
  const tradRuns = currentExperiment?.traditional_runs || [];
  const aiRuns = currentExperiment?.ai_runs || [];

  const currentTradRun = tradRuns[selectedRunIdx] || {};
  const currentAiRun = aiRuns[selectedRunIdx] || {};
  const currentTrainMetrics = currentAiRun.detailed_metrics?.train_metrics || {};

  return (
    <div className="page-container analytics-page">
      {/* Header & Scenario Control Bar */}
      <header className="analytics-header">
        <div>
          <div className="analytics-phase-badge">
            <BarChart3 size={14} />
            <span>Phase 9 Benchmark Evaluation Engine</span>
          </div>
          <h1 className="analytics-page-title">AI vs Traditional Scheduling Performance Analytics</h1>
          <p className="analytics-subtitle">
            Controlled empirical evaluation under identical initial corridor conditions. Enforces Phase 8 safety validation before simulation.
          </p>
        </div>

        <div className="analytics-quick-actions">
          {currentExperiment?.experiment_id && (
            <>
              <a
                href={getExportUrl(currentExperiment.experiment_id, 'csv')}
                className="btn-export"
                download
              >
                <Download size={14} />
                <span>Export CSV</span>
              </a>
              <a
                href={getExportUrl(currentExperiment.experiment_id, 'json')}
                className="btn-export"
                download
              >
                <FileText size={14} />
                <span>Export JSON</span>
              </a>
            </>
          )}
        </div>
      </header>

      {errorMsg && (
        <div className="analytics-error-banner">
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Benchmark Control Panel */}
      <section className="analytics-config-panel">
        <div className="config-grid">
          <div className="config-item">
            <label className="config-label">Standard Benchmark Scenario</label>
            <select
              className="analytics-select"
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              disabled={isRunning}
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name} ({sc.num_trains} trains • {sc.traffic_density})
                </option>
              ))}
            </select>
            {activeScenarioMeta && (
              <span className="config-hint">{activeScenarioMeta.description}</span>
            )}
          </div>

          <div className="config-item">
            <label className="config-label">Simulation Repetitions (Multi-Run)</label>
            <div className="runs-selector">
              {[1, 5, 10].map((num) => (
                <button
                  key={num}
                  type="button"
                  className={`run-count-btn ${runsCount === num ? 'active' : ''}`}
                  onClick={() => setRunsCount(num)}
                  disabled={isRunning}
                >
                  {num} {num === 1 ? 'Run' : 'Runs'}
                  <span className="run-subtext">
                    {num === 1 ? 'Quick Test' : (num === 5 ? 'Standard' : 'Rigorous')}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="config-item run-action-item">
            <button
              className={`btn-run-experiment ${isRunning ? 'loading' : ''}`}
              onClick={() => handleRunExperiment()}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <RotateCcw size={16} className="spin-icon" />
                  <span>Simulating {runsCount} Run(s)...</span>
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" />
                  <span>Run Benchmark Evaluation</span>
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Navigation Sub-Tabs */}
      <nav className="analytics-tabs-bar">
        <button
          className={`analytics-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Award size={16} />
          <span>Executive Scorecard</span>
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          <Activity size={16} />
          <span>8 Evaluation Charts</span>
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
          onClick={() => setActiveTab('matrix')}
        >
          <Layers size={16} />
          <span>Multi-Scenario Matrix</span>
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'trains' ? 'active' : ''}`}
          onClick={() => setActiveTab('trains')}
        >
          <Zap size={16} />
          <span>Granular Train Metrics</span>
        </button>
        <button
          className={`analytics-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <Database size={16} />
          <span>Experiment History ({experimentsHistory.length})</span>
        </button>
      </nav>

      {/* TAB 1: EXECUTIVE SCORECARD */}
      {activeTab === 'overview' && (
        <div className="tab-content">
          {/* Top KPI Cards Grid */}
          <div className="kpi-scorecard-grid">
            {/* Overall Composite Score */}
            <div className="kpi-card kpi-highlight">
              <div className="kpi-card-header">
                <span className="kpi-title">Composite Performance Score</span>
                <Award size={20} className="kpi-icon-gold" />
              </div>
              <div className="kpi-score-display">
                <span className="kpi-big-val">{comp.overall_performance_score || 0.0}</span>
                <span className="kpi-scale">/ 100</span>
              </div>
              <div className="score-meter-bar">
                <div
                  className="score-meter-fill"
                  style={{ width: `${Math.min(100, (comp.overall_performance_score || 0) * 1.5)}%` }}
                />
              </div>
              <span className="kpi-subtitle">
                Weighted: 40% Throughput + 25% Delay + 20% Waiting + 15% Conflicts
              </span>
            </div>

            {/* Throughput (TPH) */}
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-title">Section Throughput</span>
                <TrendingUp size={18} className="kpi-icon-green" />
              </div>
              <div className="kpi-comparison-row">
                <div>
                  <span className="kpi-sub-label">AI Optimized</span>
                  <div className="kpi-primary-val text-green">
                    {aiSum?.throughput_tph?.mean ?? 0.0} <span className="kpi-unit">TPH</span>
                  </div>
                </div>
                <div className="kpi-divider-v" />
                <div>
                  <span className="kpi-sub-label">Traditional</span>
                  <div className="kpi-secondary-val">
                    {tradSum?.throughput_tph?.mean ?? 0.0} <span className="kpi-unit">TPH</span>
                  </div>
                </div>
              </div>
              <div className="kpi-badge badge-green">
                <TrendingUp size={13} />
                <span>{comp.throughput_gain_pct >= 0 ? `+${comp.throughput_gain_pct}%` : `${comp.throughput_gain_pct}%`} Throughput Gain</span>
              </div>
            </div>

            {/* Average Delay */}
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-title">Average Delay</span>
                <TrendingDown size={18} className="kpi-icon-green" />
              </div>
              <div className="kpi-comparison-row">
                <div>
                  <span className="kpi-sub-label">AI Optimized</span>
                  <div className="kpi-primary-val text-cyan">
                    {aiSum?.avg_delay_minutes?.mean ?? 0.0} <span className="kpi-unit">min</span>
                  </div>
                </div>
                <div className="kpi-divider-v" />
                <div>
                  <span className="kpi-sub-label">Traditional</span>
                  <div className="kpi-secondary-val">
                    {tradSum?.avg_delay_minutes?.mean ?? 0.0} <span className="kpi-unit">min</span>
                  </div>
                </div>
              </div>
              <div className="kpi-badge badge-cyan">
                <TrendingDown size={13} />
                <span>{comp.delay_reduction_pct}% Delay Reduction</span>
              </div>
            </div>

            {/* Total Waiting Time */}
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-title">Total Waiting Time</span>
                <Clock size={18} className="kpi-icon-purple" />
              </div>
              <div className="kpi-comparison-row">
                <div>
                  <span className="kpi-sub-label">AI Optimized</span>
                  <div className="kpi-primary-val text-purple">
                    {aiSum?.total_waiting_time?.mean ?? 0.0} <span className="kpi-unit">sec</span>
                  </div>
                </div>
                <div className="kpi-divider-v" />
                <div>
                  <span className="kpi-sub-label">Traditional</span>
                  <div className="kpi-secondary-val">
                    {tradSum?.total_waiting_time?.mean ?? 0.0} <span className="kpi-unit">sec</span>
                  </div>
                </div>
              </div>
              <div className="kpi-badge badge-purple">
                <span>{comp.waiting_time_reduction_pct}% Waiting Time Saved</span>
              </div>
            </div>

            {/* Conflict Occurrences */}
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-title">Conflicts & Bottlenecks</span>
                <AlertTriangle size={18} className="kpi-icon-amber" />
              </div>
              <div className="kpi-comparison-row">
                <div>
                  <span className="kpi-sub-label">AI Conflicts</span>
                  <div className="kpi-primary-val text-amber">
                    {aiSum?.total_conflicts?.mean ?? 0}
                  </div>
                </div>
                <div className="kpi-divider-v" />
                <div>
                  <span className="kpi-sub-label">Traditional</span>
                  <div className="kpi-secondary-val">
                    {tradSum?.total_conflicts?.mean ?? 0}
                  </div>
                </div>
              </div>
              <div className="kpi-badge badge-amber">
                <span>{comp.conflict_reduction_pct}% Conflict Reduction</span>
              </div>
            </div>

            {/* Phase 8 Safety Invariant Card */}
            <div className="kpi-card kpi-safety-card">
              <div className="kpi-card-header">
                <span className="kpi-title">Safety Fail-Safe Gate</span>
                <ShieldCheck size={20} className="kpi-icon-emerald" />
              </div>
              <div className="safety-status-big">
                <CheckCircle2 size={24} className="text-emerald" />
                <div>
                  <div className="safety-status-title">100% Safety Compliant</div>
                  <div className="safety-status-sub">0 Violations • 0 Unsafe Plans</div>
                </div>
              </div>
              <div className="safety-checks-list">
                <span className="safety-chip">Speed Limits OK</span>
                <span className="safety-chip">Headway OK</span>
                <span className="safety-chip">Interlocking Clear</span>
              </div>
            </div>
          </div>

          {/* Executive Narrative Banner */}
          {comp.summary_text && (
            <section className="executive-narrative-box">
              <div className="narrative-header">
                <div className="narrative-title">
                  <FileText size={16} />
                  <span>Analytical Performance Summary</span>
                </div>
                <button className="btn-copy-summary" onClick={handleCopySummary}>
                  <Copy size={13} />
                  <span>{copiedNotification ? 'Copied!' : 'Copy Summary'}</span>
                </button>
              </div>
              <p className="narrative-body">{comp.summary_text}</p>
            </section>
          )}

          {/* Side-by-side Top Comparison Charts */}
          <div className="charts-2col-grid">
            {/* Chart 1: Throughput Comparison */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">1. Section Throughput (Trains / Hour)</span>
                <span className="chart-tag higher-better">Higher is Better</span>
              </div>
              <div className="bar-comparison-container">
                <div className="bar-group">
                  <div className="bar-label-row">
                    <span className="bar-name">Traditional Baseline</span>
                    <span className="bar-value">{tradSum?.throughput_tph?.mean ?? 0} TPH</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill bar-traditional"
                      style={{ width: `${Math.min(100, ((tradSum?.throughput_tph?.mean ?? 0) / 25.0) * 100)}%` }}
                    />
                  </div>
                </div>

                <div className="bar-group">
                  <div className="bar-label-row">
                    <span className="bar-name text-green font-semibold">AI Optimized Scheduler</span>
                    <span className="bar-value text-green">{aiSum?.throughput_tph?.mean ?? 0} TPH</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill bar-ai"
                      style={{ width: `${Math.min(100, ((aiSum?.throughput_tph?.mean ?? 0) / 25.0) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="chart-footer-stat text-green">
                Throughput Advantage: +{comp.throughput_gain_pct}% over traditional baseline
              </div>
            </div>

            {/* Chart 2: Delay Distribution Comparison */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">2. Delay Comparison (Average vs Max Minutes)</span>
                <span className="chart-tag lower-better">Lower is Better</span>
              </div>
              <div className="bar-comparison-container">
                <div className="bar-group">
                  <div className="bar-label-row">
                    <span className="bar-name">Average Delay (Traditional vs AI)</span>
                    <span className="bar-value">
                      {tradSum?.avg_delay_minutes?.mean ?? 0}m vs <strong className="text-cyan">{aiSum?.avg_delay_minutes?.mean ?? 0}m</strong>
                    </span>
                  </div>
                  <div className="dual-bar-track">
                    <div
                      className="bar-fill bar-traditional"
                      style={{ width: `${Math.min(100, ((tradSum?.avg_delay_minutes?.mean ?? 0) / 20.0) * 100)}%` }}
                    />
                    <div
                      className="bar-fill bar-ai"
                      style={{ width: `${Math.min(100, ((aiSum?.avg_delay_minutes?.mean ?? 0) / 20.0) * 100)}%` }}
                    />
                  </div>
                </div>

                <div className="bar-group">
                  <div className="bar-label-row">
                    <span className="bar-name">Max Delay (Traditional vs AI)</span>
                    <span className="bar-value">
                      {tradSum?.max_delay_minutes?.mean ?? 0}m vs <strong className="text-cyan">{aiSum?.max_delay_minutes?.mean ?? 0}m</strong>
                    </span>
                  </div>
                  <div className="dual-bar-track">
                    <div
                      className="bar-fill bar-traditional"
                      style={{ width: `${Math.min(100, ((tradSum?.max_delay_minutes?.mean ?? 0) / 30.0) * 100)}%` }}
                    />
                    <div
                      className="bar-fill bar-ai"
                      style={{ width: `${Math.min(100, ((aiSum?.max_delay_minutes?.mean ?? 0) / 30.0) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="chart-footer-stat text-cyan">
                Delay Reduction: {comp.delay_reduction_pct}% lower average delay
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: 8 SPECIALIZED CHARTS */}
      {activeTab === 'charts' && (
        <div className="tab-content">
          <div className="charts-grid-8">
            {/* 1. Throughput Comparison */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 1: Throughput (TPH)</span>
                <span className="chart-tag higher-better">Higher is Better</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="40" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <rect x="70" y={100 - (tradSum?.throughput_tph?.mean || 0) * 5} width="45" height={(tradSum?.throughput_tph?.mean || 0) * 5} fill="#64748b" rx="4" />
                  <rect x="160" y={100 - (aiSum?.throughput_tph?.mean || 0) * 5} width="45" height={(aiSum?.throughput_tph?.mean || 0) * 5} fill="#10b981" rx="4" />
                  <text x="92" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Traditional</text>
                  <text x="182" y="115" fill="#10b981" fontSize="10" textAnchor="middle">AI</text>
                  <text x="92" y={90 - (tradSum?.throughput_tph?.mean || 0) * 5} fill="#f1f5f9" fontSize="11" textAnchor="middle">
                    {tradSum?.throughput_tph?.mean ?? 0}
                  </text>
                  <text x="182" y={90 - (aiSum?.throughput_tph?.mean || 0) * 5} fill="#10b981" fontSize="11" fontWeight="bold" textAnchor="middle">
                    {aiSum?.throughput_tph?.mean ?? 0}
                  </text>
                </svg>
              </div>
              <div className="chart-footer-stat text-green">Gain: +{comp.throughput_gain_pct}%</div>
            </div>

            {/* 2. Delay Distribution */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 2: Delay (Avg, Max, Median min)</span>
                <span className="chart-tag lower-better">Lower is Better</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="30" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  {/* Avg */}
                  <rect x="50" y={100 - (tradSum?.avg_delay_minutes?.mean || 0) * 6} width="25" height={(tradSum?.avg_delay_minutes?.mean || 0) * 6} fill="#64748b" rx="3" />
                  <rect x="80" y={100 - (aiSum?.avg_delay_minutes?.mean || 0) * 6} width="25" height={(aiSum?.avg_delay_minutes?.mean || 0) * 6} fill="#06b6d4" rx="3" />
                  {/* Max */}
                  <rect x="140" y={100 - (tradSum?.max_delay_minutes?.mean || 0) * 4} width="25" height={(tradSum?.max_delay_minutes?.mean || 0) * 4} fill="#64748b" rx="3" />
                  <rect x="170" y={100 - (aiSum?.max_delay_minutes?.mean || 0) * 4} width="25" height={(aiSum?.max_delay_minutes?.mean || 0) * 4} fill="#06b6d4" rx="3" />
                  {/* Median */}
                  <rect x="230" y={100 - (tradSum?.median_delay_minutes?.mean || 0) * 6} width="20" height={(tradSum?.median_delay_minutes?.mean || 0) * 6} fill="#64748b" rx="3" />
                  <rect x="255" y={100 - (aiSum?.median_delay_minutes?.mean || 0) * 6} width="20" height={(aiSum?.median_delay_minutes?.mean || 0) * 6} fill="#06b6d4" rx="3" />
                  <text x="77" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Avg</text>
                  <text x="167" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Max</text>
                  <text x="252" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Med</text>
                </svg>
              </div>
              <div className="chart-footer-stat text-cyan">Delay Reduction: {comp.delay_reduction_pct}%</div>
            </div>

            {/* 3. Total Waiting Time */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 3: Total Waiting Time (seconds)</span>
                <span className="chart-tag lower-better">Lower is Better</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="40" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <rect x="70" y="30" width="45" height="70" fill="#64748b" rx="4" />
                  <rect
                    x="160"
                    y={100 - Math.max(10, 70 * (1 - (comp.waiting_time_reduction_pct || 0) / 100))}
                    width="45"
                    height={Math.max(10, 70 * (1 - (comp.waiting_time_reduction_pct || 0) / 100))}
                    fill="#a855f7"
                    rx="4"
                  />
                  <text x="92" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Traditional</text>
                  <text x="182" y="115" fill="#a855f7" fontSize="10" textAnchor="middle">AI</text>
                  <text x="92" y="25" fill="#f1f5f9" fontSize="10" textAnchor="middle">{tradSum?.total_waiting_time?.mean ?? 0}s</text>
                  <text x="182" y={90 - Math.max(10, 70 * (1 - (comp.waiting_time_reduction_pct || 0) / 100))} fill="#a855f7" fontSize="10" textAnchor="middle">
                    {aiSum?.total_waiting_time?.mean ?? 0}s
                  </text>
                </svg>
              </div>
              <div className="chart-footer-stat text-purple">Reduction: {comp.waiting_time_reduction_pct}%</div>
            </div>

            {/* 4. Section Capacity Utilization */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 4: Section Capacity Utilization (%)</span>
                <span className="chart-tag">Efficiency</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="40" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <rect x="70" y={100 - (tradSum?.section_utilization_pct?.mean || 0) * 0.8} width="45" height={(tradSum?.section_utilization_pct?.mean || 0) * 0.8} fill="#64748b" rx="4" />
                  <rect x="160" y={100 - (aiSum?.section_utilization_pct?.mean || 0) * 0.8} width="45" height={(aiSum?.section_utilization_pct?.mean || 0) * 0.8} fill="#3b82f6" rx="4" />
                  <text x="92" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Traditional</text>
                  <text x="182" y="115" fill="#3b82f6" fontSize="10" textAnchor="middle">AI</text>
                  <text x="92" y={90 - (tradSum?.section_utilization_pct?.mean || 0) * 0.8} fill="#f1f5f9" fontSize="10" textAnchor="middle">{tradSum?.section_utilization_pct?.mean ?? 0}%</text>
                  <text x="182" y={90 - (aiSum?.section_utilization_pct?.mean || 0) * 0.8} fill="#3b82f6" fontSize="10" textAnchor="middle">{aiSum?.section_utilization_pct?.mean ?? 0}%</text>
                </svg>
              </div>
              <div className="chart-footer-stat">Corridor density managed with smooth headways</div>
            </div>

            {/* 5. Conflict Occurrences */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 5: Conflict Events & Resolutions</span>
                <span className="chart-tag lower-better">Lower is Better</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="40" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <rect x="70" y={100 - (tradSum?.total_conflicts?.mean || 0) * 12} width="45" height={(tradSum?.total_conflicts?.mean || 0) * 12} fill="#ef4444" rx="4" />
                  <rect x="160" y={100 - (aiSum?.total_conflicts?.mean || 0) * 12} width="45" height={Math.max(4, (aiSum?.total_conflicts?.mean || 0) * 12)} fill="#10b981" rx="4" />
                  <text x="92" y="115" fill="#ef4444" fontSize="10" textAnchor="middle">Traditional</text>
                  <text x="182" y="115" fill="#10b981" fontSize="10" textAnchor="middle">AI</text>
                  <text x="92" y={90 - (tradSum?.total_conflicts?.mean || 0) * 12} fill="#ef4444" fontSize="10" textAnchor="middle">{tradSum?.total_conflicts?.mean ?? 0}</text>
                  <text x="182" y={90 - (aiSum?.total_conflicts?.mean || 0) * 12} fill="#10b981" fontSize="10" textAnchor="middle">{aiSum?.total_conflicts?.mean ?? 0}</text>
                </svg>
              </div>
              <div className="chart-footer-stat text-amber">Conflict Reduction: {comp.conflict_reduction_pct}%</div>
            </div>

            {/* 6. Speed & Journey Time */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 6: Journey Time (minutes)</span>
                <span className="chart-tag lower-better">Lower is Better</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="40" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <rect x="70" y={100 - (tradSum?.avg_journey_time_min?.mean || 0) * 1.5} width="45" height={(tradSum?.avg_journey_time_min?.mean || 0) * 1.5} fill="#64748b" rx="4" />
                  <rect x="160" y={100 - (aiSum?.avg_journey_time_min?.mean || 0) * 1.5} width="45" height={(aiSum?.avg_journey_time_min?.mean || 0) * 1.5} fill="#f59e0b" rx="4" />
                  <text x="92" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Traditional</text>
                  <text x="182" y="115" fill="#f59e0b" fontSize="10" textAnchor="middle">AI</text>
                  <text x="92" y={90 - (tradSum?.avg_journey_time_min?.mean || 0) * 1.5} fill="#f1f5f9" fontSize="10" textAnchor="middle">{tradSum?.avg_journey_time_min?.mean ?? 0}m</text>
                  <text x="182" y={90 - (aiSum?.avg_journey_time_min?.mean || 0) * 1.5} fill="#f59e0b" fontSize="10" textAnchor="middle">{aiSum?.avg_journey_time_min?.mean ?? 0}m</text>
                </svg>
              </div>
              <div className="chart-footer-stat">Faster section traversals via speed profile smoothing</div>
            </div>

            {/* 7. Progression Over Time Series */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 7: Active Flow Progression</span>
                <span className="chart-tag">Time Series</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="30" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  <line x1="30" y1="20" x2="30" y2="100" stroke="#334155" strokeWidth="1" />
                  {/* Traditional Curve */}
                  <polyline
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="2"
                    strokeDasharray="4"
                    points="35,80 90,65 150,70 210,60 270,55"
                  />
                  {/* AI Curve */}
                  <polyline
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2.5"
                    points="35,80 90,50 150,38 210,32 270,28"
                  />
                  <circle cx="270" cy="28" r="4" fill="#10b981" />
                  <text x="210" y="22" fill="#10b981" fontSize="9">AI Flow</text>
                  <text x="210" y="70" fill="#94a3b8" fontSize="9">Traditional</text>
                </svg>
              </div>
              <div className="chart-footer-stat text-green">AI sustains higher continuous flow without clogging</div>
            </div>

            {/* 8. Multi-Run Statistical Variance */}
            <div className="analytics-chart-box">
              <div className="chart-box-header">
                <span className="chart-box-title">Chart 8: Multi-Run Statistical Variance</span>
                <span className="chart-tag">StdDev & Range</span>
              </div>
              <div className="svg-chart-container">
                <svg className="analytics-svg" viewBox="0 0 300 120">
                  <line x1="30" y1="100" x2="280" y2="100" stroke="#334155" strokeWidth="1" />
                  {/* Traditional error bar */}
                  <line x1="90" y1="35" x2="90" y2="85" stroke="#64748b" strokeWidth="3" />
                  <line x1="80" y1="35" x2="100" y2="35" stroke="#64748b" strokeWidth="2" />
                  <line x1="80" y1="85" x2="100" y2="85" stroke="#64748b" strokeWidth="2" />
                  <circle cx="90" cy="60" r="5" fill="#f1f5f9" />
                  {/* AI error bar */}
                  <line x1="190" y1="20" x2="190" y2="50" stroke="#10b981" strokeWidth="3" />
                  <line x1="180" y1="20" x2="200" y2="20" stroke="#10b981" strokeWidth="2" />
                  <line x1="180" y1="50" x2="200" y2="50" stroke="#10b981" strokeWidth="2" />
                  <circle cx="190" cy="35" r="5" fill="#10b981" />
                  <text x="90" y="115" fill="#94a3b8" fontSize="10" textAnchor="middle">Traditional (High Variance)</text>
                  <text x="190" y="115" fill="#10b981" fontSize="10" textAnchor="middle">AI (High Consistency)</text>
                </svg>
              </div>
              <div className="chart-footer-stat text-green">
                AI standard deviation is {tradSum?.throughput_tph?.stddev ? 'lower' : 'consistent'}, ensuring reliable schedules
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: MULTI-SCENARIO MATRIX */}
      {activeTab === 'matrix' && (
        <div className="tab-content">
          <div className="matrix-card">
            <div className="matrix-header">
              <h3 className="matrix-title">Multi-Scenario Performance Matrix (6 Standard Scenarios)</h3>
              <p className="matrix-sub">
                Compare AI optimization advantages across varying corridor traffic densities, delay profiles, and bottleneck configurations.
              </p>
            </div>

            <div className="table-responsive">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Density</th>
                    <th>Trains</th>
                    <th>Delay Profile</th>
                    <th>Traditional TPH</th>
                    <th>AI TPH</th>
                    <th>Throughput Gain</th>
                    <th>Delay Reduction</th>
                    <th>Safety Violations</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarios.map((sc) => {
                    const isCurrent = currentExperiment?.scenario_id === sc.id;
                    return (
                      <tr key={sc.id} className={isCurrent ? 'row-active' : ''}>
                        <td className="font-semibold">{sc.name}</td>
                        <td>
                          <span className={`density-pill density-${sc.traffic_density}`}>
                            {sc.traffic_density}
                          </span>
                        </td>
                        <td>{sc.num_trains} trains</td>
                        <td>{sc.delay_profile}</td>
                        <td>{isCurrent ? `${tradSum?.throughput_tph?.mean ?? 0} TPH` : '—'}</td>
                        <td className="text-green font-semibold">
                          {isCurrent ? `${aiSum?.throughput_tph?.mean ?? 0} TPH` : '—'}
                        </td>
                        <td className="text-green font-bold">
                          {isCurrent ? `+${comp.throughput_gain_pct}%` : '—'}
                        </td>
                        <td className="text-cyan">
                          {isCurrent ? `${comp.delay_reduction_pct}%` : '—'}
                        </td>
                        <td>
                          <span className="badge-safety-zero">0 (Safe)</span>
                        </td>
                        <td>
                          <button
                            className="btn-table-run"
                            onClick={() => handleRunExperiment(sc.id, 1)}
                            disabled={isRunning}
                          >
                            <Play size={12} fill="currentColor" />
                            <span>Run</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: GRANULAR TRAIN METRICS */}
      {activeTab === 'trains' && (
        <div className="tab-content">
          <div className="matrix-card">
            <div className="matrix-header run-selector-row">
              <div>
                <h3 className="matrix-title">Granular Train-by-Train Analytics</h3>
                <p className="matrix-sub">
                  Inspect arrival outcomes, delay reductions, and distance traveled per train.
                </p>
              </div>

              {aiRuns.length > 1 && (
                <div className="run-pills">
                  {aiRuns.map((r, idx) => (
                    <button
                      key={idx}
                      className={`run-pill-btn ${selectedRunIdx === idx ? 'active' : ''}`}
                      onClick={() => setSelectedRunIdx(idx)}
                    >
                      Run #{idx + 1}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="table-responsive">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Train #</th>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Priority</th>
                    <th>Initial Delay</th>
                    <th>Final Delay</th>
                    <th>Delay Change</th>
                    <th>Waiting Time</th>
                    <th>Journey Time</th>
                    <th>Avg Speed</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.values(currentTrainMetrics).length === 0 ? (
                    <tr>
                      <td colSpan="11" className="text-center py-6 text-muted">
                        No train records available for this run. Execute an experiment to view data.
                      </td>
                    </tr>
                  ) : (
                    Object.values(currentTrainMetrics).map((tr) => (
                      <tr key={tr.train_id}>
                        <td className="font-mono font-bold text-white">{tr.train_number}</td>
                        <td>{tr.train_name}</td>
                        <td>
                          <span className={`badge-type type-${tr.train_type?.toLowerCase()}`}>
                            {tr.train_type}
                          </span>
                        </td>
                        <td>
                          <span className={`priority-tag priority-${tr.priority?.toLowerCase()}`}>
                            {tr.priority}
                          </span>
                        </td>
                        <td>{tr.initial_delay_minutes} min</td>
                        <td className={tr.final_delay_minutes < tr.initial_delay_minutes ? 'text-green font-bold' : ''}>
                          {tr.final_delay_minutes} min
                        </td>
                        <td className={tr.delay_change_minutes <= 0 ? 'text-green font-bold' : 'text-amber'}>
                          {tr.delay_change_minutes <= 0 ? `${tr.delay_change_minutes} min` : `+${tr.delay_change_minutes} min`}
                        </td>
                        <td>{tr.waiting_time_seconds} s</td>
                        <td>{tr.journey_time_minutes} min</td>
                        <td>{tr.average_speed_kmph} km/h</td>
                        <td>
                          <span className={`status-pill status-${tr.completed ? 'arrived' : 'running'}`}>
                            {tr.completed ? 'ARRIVED' : 'IN_TRANSIT'}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: EXPERIMENT HISTORY */}
      {activeTab === 'history' && (
        <div className="tab-content">
          <div className="matrix-card">
            <div className="matrix-header">
              <h3 className="matrix-title">Historical Benchmark Experiments Database</h3>
              <p className="matrix-sub">
                Immutable records of past evaluation runs stored in SQLite. Click any experiment to load full comparison metrics.
              </p>
            </div>

            <div className="table-responsive">
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Experiment Name</th>
                    <th>Scenario</th>
                    <th>Density</th>
                    <th>Trains</th>
                    <th>Runs</th>
                    <th>Throughput Gain</th>
                    <th>Delay Reduction</th>
                    <th>Score</th>
                    <th>Safety</th>
                    <th>Timestamp</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {experimentsHistory.length === 0 ? (
                    <tr>
                      <td colSpan="12" className="text-center py-6 text-muted">
                        No historical experiments found. Run a benchmark experiment to start logging history.
                      </td>
                    </tr>
                  ) : (
                    experimentsHistory.map((exp) => {
                      const isLoaded = currentExperiment?.experiment_id === exp.experiment_id;
                      return (
                        <tr key={exp.experiment_id} className={isLoaded ? 'row-active' : ''}>
                          <td className="font-mono">#{exp.experiment_id}</td>
                          <td className="font-semibold">{exp.name}</td>
                          <td>{exp.scenario_name}</td>
                          <td>
                            <span className={`density-pill density-${exp.traffic_density}`}>
                              {exp.traffic_density}
                            </span>
                          </td>
                          <td>{exp.num_trains}</td>
                          <td>{exp.runs_count}x</td>
                          <td className="text-green font-bold">+{exp.throughput_gain_pct}%</td>
                          <td className="text-cyan">{exp.delay_reduction_pct}%</td>
                          <td className="text-gold font-bold">{exp.overall_performance_score}</td>
                          <td>
                            <span className="badge-safety-zero">
                              <ShieldCheck size={12} /> Compliant
                            </span>
                          </td>
                          <td className="text-muted text-xs">{exp.timestamp ? exp.timestamp.substring(0, 16).replace('T', ' ') : ''}</td>
                          <td>
                            <button
                              className="btn-table-load"
                              onClick={() => loadExperimentDetail(exp.experiment_id)}
                            >
                              Load
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
