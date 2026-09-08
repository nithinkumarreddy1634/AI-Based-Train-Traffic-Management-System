import React, { useState } from 'react';
import { Play, CheckCircle2, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';
import { runOptimizationBenchmark } from '../services/api';

export default function BenchmarkScenarioRunner() {
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runOptimizationBenchmark();
      setBenchmarks(data);
    } catch (err) {
      console.error('Benchmark execution error:', err);
      setError('Failed to run benchmark suite.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card benchmark-scenario-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">RIGOROUS VERIFICATION SUITE</div>
          <h3 className="card-title">Standard Dispatch Benchmark Scenarios</h3>
        </div>

        <button
          className="btn btn-primary btn-sm flex items-center gap-1"
          onClick={handleRunAll}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Evaluating CP-SAT...' : '⚡ Run All 4 Benchmark Scenarios'}
        </button>
      </div>

      <div className="card-body">
        {error && <div className="error-banner mb-3">{error}</div>}

        {benchmarks.length === 0 ? (
          <div className="empty-benchmark-prompt">
            <p>Click <strong>"Run All 4 Benchmark Scenarios"</strong> to evaluate optimizer performance across Low, Medium, Heavy Bottleneck, and Cascading High-Delay traffic patterns.</p>
          </div>
        ) : (
          <div className="benchmark-results-grid">
            {benchmarks.map((b) => (
              <div key={b.scenario_id} className="benchmark-card">
                <div className="benchmark-card-header">
                  <div>
                    <h4 className="scenario-title">{b.scenario_name}</h4>
                    <span className="scenario-meta">
                      {b.train_count} Trains | Level: <strong>{b.traffic_level}</strong>
                    </span>
                  </div>
                  <span className="badge badge-success">{b.status}</span>
                </div>

                <div className="benchmark-metrics-row">
                  {/* Throughput */}
                  <div className="b-metric">
                    <span className="b-metric-label">THROUGHPUT</span>
                    <div className="b-metric-val font-mono">
                      {b.current_throughput} ➔ <strong className="text-emerald-400">{b.optimized_throughput}</strong>
                    </div>
                    <span className="b-gain text-emerald-400">+{b.throughput_gain_pct}% gain</span>
                  </div>

                  {/* Delay */}
                  <div className="b-metric">
                    <span className="b-metric-label">TOTAL DELAY</span>
                    <div className="b-metric-val font-mono">
                      {b.current_delay}m ➔ <strong className="text-sky-400">{b.optimized_delay}m</strong>
                    </div>
                    <span className="b-gain text-sky-400">-{b.delay_reduction_pct}% reduction</span>
                  </div>

                  {/* Waiting */}
                  <div className="b-metric">
                    <span className="b-metric-label">WAIT TIME</span>
                    <div className="b-metric-val font-mono">
                      {b.current_waiting}m ➔ <strong className="text-purple-400">{b.optimized_waiting}m</strong>
                    </div>
                    <span className="b-gain text-purple-400">-{b.waiting_reduction_pct}% reduction</span>
                  </div>
                </div>

                <div className="b-explanation mt-2">
                  <small className="text-slate-300">{b.explanation}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

