import React from 'react';
import { ArrowRight, Clock, ShieldCheck, AlertCircle, Zap, PauseCircle } from 'lucide-react';

export default function RecommendedSequenceCard({ recommendations = [], onSelectTrain }) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="card sequence-card empty-state-box">
        <p className="text-slate-400">No train recommendations available. Click "Run AI Optimization" to generate a dispatch sequence.</p>
      </div>
    );
  }

  const getActionBadge = (action, holdSec) => {
    switch (action) {
      case 'PROCEED':
        return (
          <span className="action-badge action-proceed">
            <Zap size={13} /> PROCEED
          </span>
        );
      case 'PRIORITIZE':
        return (
          <span className="action-badge action-prioritize">
            <ShieldCheck size={13} /> PRIORITIZE
          </span>
        );
      case 'DIVERT_LOOP':
        return (
          <span className="action-badge action-divert">
            <AlertCircle size={13} /> LOOP SIDING ({Math.round(holdSec / 60)}m)
          </span>
        );
      case 'HOLD':
      default:
        return (
          <span className="action-badge action-hold">
            <PauseCircle size={13} /> HOLD ({holdSec}s)
          </span>
        );
    }
  };

  return (
    <div className="card sequence-panel-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">AI DISPATCH DIRECTIVE</div>
          <h3 className="card-title">Recommended Train Movement Sequence ({recommendations.length})</h3>
        </div>
        <span className="badge badge-success">Optimal Headway Spacing</span>
      </div>

      <div className="card-body p-0">
        <div className="sequence-list">
          {recommendations.map((rec, index) => (
            <div
              key={rec.train_id || index}
              className={`sequence-item-row ${rec.action === 'PRIORITIZE' ? 'item-prioritized' : ''}`}
              onClick={() => onSelectTrain && onSelectTrain(rec)}
            >
              {/* Sequence Order Step Number */}
              <div className="seq-step-badge">
                <span className="step-num">#{index + 1}</span>
              </div>

              {/* Train Identity */}
              <div className="seq-train-info">
                <div className="train-id-badge">{rec.train_number}</div>
                <div className="train-meta-sub">
                  <span className="type-tag">{rec.train_type}</span>
                  <span className={`prio-tag prio-${rec.priority?.toLowerCase()}`}>
                    {rec.priority}
                  </span>
                </div>
              </div>

              {/* Action Directive */}
              <div className="seq-action-col">
                {getActionBadge(rec.action, rec.hold_duration_seconds)}
                <div className="seq-entry-time font-mono">
                  <Clock size={12} /> {rec.recommended_entry_time}
                </div>
              </div>

              {/* Delay Impact */}
              <div className="seq-delay-col">
                <div className="delay-metric-label">PROJECTED DELAY</div>
                <div className="delay-val predicted-delay-val">
                  {rec.expected_delay_minutes} min
                </div>
                {rec.predicted_additional_delay > 0 && (
                  <div className="added-delay-sub text-amber-400">
                    +{rec.predicted_additional_delay}m ML cascade
                  </div>
                )}
              </div>

              {/* Operational Rationale */}
              <div className="seq-reason-col">
                <p className="seq-reason-text">{rec.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

