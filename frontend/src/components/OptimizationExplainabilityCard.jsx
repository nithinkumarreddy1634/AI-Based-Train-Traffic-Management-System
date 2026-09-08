import React from 'react';
import { HelpCircle, Info, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function OptimizationExplainabilityCard({ explanation, factorContributions = {} }) {
  const factors = [
    {
      key: 'throughput_maximization',
      label: 'Throughput Maximization',
      pct: factorContributions.throughput_maximization || 35.0,
      gradient: 'linear-gradient(90deg, #10b981, #059669)',
      desc: 'Pack train block occupations tightly within safe minimum headway envelopes.',
    },
    {
      key: 'delay_mitigation',
      label: 'Delay Mitigation (Phase 6 ML)',
      pct: factorContributions.delay_mitigation || 30.0,
      gradient: 'linear-gradient(90deg, #38bdf8, #0284c7)',
      desc: 'Prioritize trains with severe predicted arrival delays to prevent cascade effects.',
    },
    {
      key: 'waiting_time_minimization',
      label: 'Waiting Time Minimization',
      pct: factorContributions.waiting_time_minimization || 15.0,
      gradient: 'linear-gradient(90deg, #a855f7, #7e22ce)',
      desc: 'Prevent excessive signal holds and station siding queue lockups.',
    },
    {
      key: 'conflict_safety_headway',
      label: 'Safety Headway & Conflict Avoidance',
      pct: factorContributions.conflict_safety_headway || 12.0,
      gradient: 'linear-gradient(90deg, #f59e0b, #d97706)',
      desc: 'Enforce dynamic braking distance buffers and eliminate Phase 5 potential conflicts.',
    },
    {
      key: 'priority_adherence',
      label: 'Train Priority Adherence',
      pct: factorContributions.priority_adherence || 8.0,
      gradient: 'linear-gradient(90deg, #f43f5e, #be123c)',
      desc: 'Weight Express & High-Priority schedules over lower-priority freight runs.',
    },
  ];

  return (
    <div className="card explainability-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">TRANSPARENT DECISION SUPPORT</div>
          <h3 className="card-title">AI Optimization Decision Rationale & Trade-offs</h3>
        </div>
        <span className="badge badge-info">Multi-Criteria Attribution</span>
      </div>

      <div className="card-body">
        {/* Narrative Explanation Box */}
        <div className="narrative-box">
          <div className="narrative-header">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span className="narrative-title">Dispatcher Synthesis</span>
          </div>
          <p className="narrative-body">
            {explanation ||
              'The optimizer selected this sequence to maximize section clearance rates while respecting braking headways and prioritizing higher-class trains with cascading predicted delay.'}
          </p>
        </div>

        {/* Factor Breakdown Bars */}
        <div className="factors-section mt-4">
          <h4 className="factors-section-title">Relative Decision Factor Contributions</h4>
          <p className="factors-section-sub">
            Calculated mathematical weights evaluated by the CP-SAT objective function during sequence exploration:
          </p>

          <div className="factor-bars-list">
            {factors.map((f) => (
              <div key={f.key} className="factor-bar-item">
                <div className="factor-bar-header">
                  <span className="factor-name">{f.label}</span>
                  <span className="factor-pct font-mono">{f.pct}%</span>
                </div>
                <div className="factor-progress-track">
                  <div
                    className="factor-progress-fill"
                    style={{ width: `${Math.min(100, f.pct * 2)}%`, background: f.gradient }}
                  />
                </div>
                <span className="factor-desc">{f.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

