import React, { useState } from 'react';
import { X, Check, AlertTriangle, PlayCircle, Eye, ShieldCheck, ShieldAlert } from 'lucide-react';
import { previewOptimization, applyOptimization } from '../services/api';
import SafetyStatusBadge from './SafetyStatusBadge';

export default function OptimizationPreviewModal({
  isOpen,
  onClose,
  optimizationId,
  recommendations = [],
  safetyValidation = null,
  onApplySuccess,
}) {
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [error, setError] = useState(null);
  const [applied, setApplied] = useState(false);

  const isSafetyRejected = safetyValidation?.status === 'REJECTED' || safetyValidation?.safety_score_status === 'UNSAFE';

  React.useEffect(() => {
    if (isOpen && recommendations.length > 0) {
      setLoading(true);
      setError(null);
      setApplied(false);
      previewOptimization(recommendations)
        .then((res) => {
          setPreviewData(res);
        })
        .catch((err) => {
          console.error('Preview fetch error:', err);
          setError('Failed to generate simulation preview.');
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, recommendations]);

  if (!isOpen) return null;

  const handleApply = async () => {
    if (isSafetyRejected) {
      setError('Dispatch blocked: This plan has active safety violations and cannot be applied.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await applyOptimization(optimizationId, recommendations);
      setApplied(true);
      if (onApplySuccess) onApplySuccess(res);
    } catch (err) {
      console.error('Apply dispatch error:', err);
      setError(err.response?.data?.detail?.message || 'Failed to apply optimization plan to simulation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-container preview-modal-container">
        {/* Header */}
        <div className="modal-header">
          <div className="flex items-center gap-2">
            <Eye className="text-sky-400" size={20} />
            <h3 className="modal-title">Simulation Preview & Safety Gatekeeper</h3>
          </div>
          <div className="flex items-center gap-3">
            <SafetyStatusBadge validation={safetyValidation} />
            <button className="modal-close-btn" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="modal-body">
          {isSafetyRejected ? (
            <div className="preview-advisory-banner border-red-500 bg-red-950/40 text-red-200">
              <ShieldAlert size={22} className="text-red-400 shrink-0" />
              <div>
                <strong>Fail-Safe Gatekeeper Interlock (Action Required):</strong>
                <p>
                  This recommendation has been <strong>REJECTED</strong> by the independent Safety Validation Engine.
                  Application to the live simulation is strictly prohibited until violations are cleared.
                </p>
              </div>
            </div>
          ) : (
            <div className="preview-advisory-banner">
              <ShieldCheck size={20} className="text-emerald-400 shrink-0" />
              <div>
                <strong>Controller Safety Gate & Verification:</strong>
                <p>
                  Recommendation verified against 9 civil engineering and headway safety rules.
                  Will only update simulation signals, holds, and speeds upon explicit authorization.
                </p>
              </div>
            </div>
          )}

          {loading && <div className="loading-state-box"><p>Loading simulation projection...</p></div>}
          {error && <div className="error-banner mt-3">{error}</div>}

          {applied ? (
            <div className="applied-success-banner mt-4">
              <Check size={24} className="text-emerald-400" />
              <div>
                <h4>Dispatch Orders Successfully Applied to Simulation!</h4>
                <p>Train movement agents are now executing the optimized entry timing and headway sequence.</p>
              </div>
            </div>
          ) : (
            previewData && (
              <div className="preview-timeline-section mt-3">
                <h4 className="preview-section-title">Forward-Projected Schedule Timeline</h4>
                <div className="table-responsive">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>Order</th>
                        <th>Train</th>
                        <th>Action</th>
                        <th>Entry Time Offset</th>
                        <th>Hold Time</th>
                        <th>Expected Delay</th>
                        <th>Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.projected_timeline?.map((item, idx) => (
                        <tr key={idx}>
                          <td><strong>#{idx + 1}</strong></td>
                          <td><span className="font-mono fw-bold">{item.train_number}</span></td>
                          <td>
                            <span className={`action-badge action-${item.action.toLowerCase()}`}>
                              {item.action}
                            </span>
                          </td>
                          <td className="font-mono">+{item.entry_offset_sec}s</td>
                          <td>{item.hold_duration_sec > 0 ? `${item.hold_duration_sec}s` : 'None'}</td>
                          <td className="font-mono text-purple-400">{item.expected_delay_min} min</td>
                          <td><small className="text-slate-300">{item.reason}</small></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            {applied ? 'Close' : 'Cancel'}
          </button>
          {!applied && (
            <button
              type="button"
              className={`btn ${isSafetyRejected ? 'btn-danger' : 'btn-success'} flex items-center gap-2`}
              onClick={handleApply}
              disabled={loading || recommendations.length === 0 || isSafetyRejected}
              title={isSafetyRejected ? 'Safety violations must be cleared before applying.' : 'Authorize dispatch orders'}
            >
              <PlayCircle size={16} />
              {isSafetyRejected ? 'Blocked by Safety Gatekeeper' : (loading ? 'Applying...' : 'Authorize & Apply to Simulation')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

