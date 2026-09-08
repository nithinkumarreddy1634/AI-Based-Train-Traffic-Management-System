import React from 'react';
import { TrendingUp, ArrowDownRight, Clock, Gauge } from 'lucide-react';

export default function BeforeVsAfterScorecard({ metrics }) {
  if (!metrics) {
    return null;
  }

  const {
    current_throughput = 0.0,
    optimized_throughput = 0.0,
    throughput_improvement_pct = 0.0,
    current_total_delay = 0.0,
    optimized_total_delay = 0.0,
    delay_reduction_pct = 0.0,
    current_waiting_time = 0.0,
    optimized_waiting_time = 0.0,
    waiting_time_reduction_pct = 0.0,
    current_section_utilization = 0.0,
    optimized_section_utilization = 0.0,
  } = metrics;

  return (
    <div className="card before-after-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">RIGOROUS PERFORMANCE AUDIT</div>
          <h3 className="card-title">Before vs After AI Optimization Impact</h3>
        </div>
        <span className="badge badge-primary">Dynamic Baseline Comparison</span>
      </div>

      <div className="card-body">
        <div className="before-after-grid">
          {/* Metric 1: Throughput */}
          <div className="scorecard-tile throughput-tile">
            <div className="scorecard-header">
              <span className="scorecard-title">SECTION THROUGHPUT</span>
              <span className="improvement-chip chip-success">
                +{throughput_improvement_pct}%
              </span>
            </div>
            <div className="comparison-values">
              <div className="val-box val-before">
                <span className="val-sub">BEFORE</span>
                <span className="val-num text-slate-400">{current_throughput}</span>
                <span className="val-unit">trains/hr</span>
              </div>
              <div className="val-arrow">➔</div>
              <div className="val-box val-after">
                <span className="val-sub">OPTIMIZED</span>
                <span className="val-num text-emerald-400 font-bold">{optimized_throughput}</span>
                <span className="val-unit">trains/hr</span>
              </div>
            </div>
            <div className="scorecard-progress">
              <div
                className="scorecard-bar-fill fill-success"
                style={{ width: `${Math.min(100, (optimized_throughput / 20.0) * 100)}%` }}
              />
            </div>
          </div>

          {/* Metric 2: Total Delay */}
          <div className="scorecard-tile delay-tile">
            <div className="scorecard-header">
              <span className="scorecard-title">TOTAL CORRIDOR DELAY</span>
              <span className="improvement-chip chip-info">
                -{delay_reduction_pct}%
              </span>
            </div>
            <div className="comparison-values">
              <div className="val-box val-before">
                <span className="val-sub">BEFORE</span>
                <span className="val-num text-slate-400">{current_total_delay}</span>
                <span className="val-unit">min</span>
              </div>
              <div className="val-arrow">➔</div>
              <div className="val-box val-after">
                <span className="val-sub">OPTIMIZED</span>
                <span className="val-num text-sky-400 font-bold">{optimized_total_delay}</span>
                <span className="val-unit">min</span>
              </div>
            </div>
            <div className="scorecard-progress">
              <div
                className="scorecard-bar-fill fill-sky"
                style={{ width: `${Math.max(15, 100 - delay_reduction_pct)}%` }}
              />
            </div>
          </div>

          {/* Metric 3: Waiting Time */}
          <div className="scorecard-tile wait-tile">
            <div className="scorecard-header">
              <span className="scorecard-title">AVERAGE HOLDING TIME</span>
              <span className="improvement-chip chip-purple">
                -{waiting_time_reduction_pct}%
              </span>
            </div>
            <div className="comparison-values">
              <div className="val-box val-before">
                <span className="val-sub">BEFORE</span>
                <span className="val-num text-slate-400">{current_waiting_time}</span>
                <span className="val-unit">min</span>
              </div>
              <div className="val-arrow">➔</div>
              <div className="val-box val-after">
                <span className="val-sub">OPTIMIZED</span>
                <span className="val-num text-purple-400 font-bold">{optimized_waiting_time}</span>
                <span className="val-unit">min</span>
              </div>
            </div>
            <div className="scorecard-progress">
              <div
                className="scorecard-bar-fill fill-purple"
                style={{ width: `${Math.max(15, 100 - waiting_time_reduction_pct)}%` }}
              />
            </div>
          </div>

          {/* Metric 4: Utilization */}
          <div className="scorecard-tile util-tile">
            <div className="scorecard-header">
              <span className="scorecard-title">SECTION UTILIZATION</span>
              <span className="improvement-chip chip-amber">
                Optimized
              </span>
            </div>
            <div className="comparison-values">
              <div className="val-box val-before">
                <span className="val-sub">BEFORE</span>
                <span className="val-num text-slate-400">{current_section_utilization}%</span>
                <span className="val-unit">capacity</span>
              </div>
              <div className="val-arrow">➔</div>
              <div className="val-box val-after">
                <span className="val-sub">OPTIMIZED</span>
                <span className="val-num text-amber-400 font-bold">{optimized_section_utilization}%</span>
                <span className="val-unit">balanced</span>
              </div>
            </div>
            <div className="scorecard-progress">
              <div
                className="scorecard-bar-fill fill-amber"
                style={{ width: `${Math.min(100, optimized_section_utilization)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

