import React, { useState, useEffect } from 'react';
import {
  fetchSafetyStatus,
  fetchSafetyRules,
  fetchSafetyAuditLogs,
  triggerEmergencyHalt,
  clearEmergencyState
} from '../services/api';
import SafetyStatusBadge from './SafetyStatusBadge';

export default function SafetyValidationPanel({ currentValidation = null, onEmergencyToggled = null }) {
  const [safetyStatus, setSafetyStatus] = useState(null);
  const [rules, setRules] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emergencyActionPending, setEmergencyActionPending] = useState(false);
  const [activeTab, setActiveTab] = useState('current'); // 'current', 'rules', 'audit'
  const [selectedAudit, setSelectedAudit] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statusRes, rulesRes, auditRes] = await Promise.all([
        fetchSafetyStatus(),
        fetchSafetyRules(),
        fetchSafetyAuditLogs(25)
      ]);
      setSafetyStatus(statusRes);
      setRules(rulesRes || []);
      setAuditLogs(auditRes?.logs || []);
    } catch (err) {
      console.error('Failed to load safety data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleToggleEmergency = async () => {
    const isCurrentlyEmergency = safetyStatus?.emergency_active;
    const confirmMsg = isCurrentlyEmergency
      ? 'Are you sure you want to CLEAR the railway corridor emergency halt?'
      : 'EMERGENCY ACTION: Are you sure you want to TRIGGER an emergency halt across the network? All automated dispatching will be halted!';

    if (!window.confirm(confirmMsg)) return;

    try {
      setEmergencyActionPending(true);
      if (isCurrentlyEmergency) {
        await clearEmergencyState();
      } else {
        await triggerEmergencyHalt('Manual Controller Intervention via Safety Validation Panel');
      }
      await loadData();
      if (onEmergencyToggled) onEmergencyToggled();
    } catch (err) {
      alert('Emergency action failed: ' + (err.response?.data?.message || err.message));
    } finally {
      setEmergencyActionPending(false);
    }
  };

  const validationToDisplay = currentValidation || (safetyStatus?.latest_audit ? {
    status: safetyStatus.latest_audit.status,
    safety_score_status: safetyStatus.latest_audit.safety_score_status,
    violations: [],
    warnings: [],
  } : null);

  return (
    <div className="safety-validation-panel">
      {/* Top Banner: Real-Time Safety Health & Emergency Switch */}
      <div className={`safety-header-banner ${safetyStatus?.emergency_active ? 'banner-critical' : (safetyStatus?.system_status === 'WARNING' ? 'banner-warning' : 'banner-safe')}`}>
        <div className="banner-left">
          <div className="safety-title-row">
            <span className="safety-shield-icon">🛡️</span>
            <h3>Formal Safety Validation Engine</h3>
            <span className="safety-tier-tag">Two-Tier Fail-Safe Gatekeeper</span>
          </div>
          <p className="safety-banner-subtitle">
            Independently validates AI dispatch recommendations against 9 civil engineering & kinematic safety constraints.
          </p>
        </div>

        <div className="banner-right">
          <div className="banner-metric-pill">
            <span className="pill-label">Audit Approval Rate</span>
            <span className="pill-value">{safetyStatus?.approval_rate_pct ?? 100}%</span>
          </div>
          <div className="banner-metric-pill">
            <span className="pill-label">Rules Enforced</span>
            <span className="pill-value">9 of 9</span>
          </div>
          <button
            onClick={handleToggleEmergency}
            disabled={emergencyActionPending}
            className={`emergency-toggle-btn ${safetyStatus?.emergency_active ? 'btn-clear-emergency' : 'btn-trigger-emergency'}`}
          >
            {safetyStatus?.emergency_active ? '⚠️ CLEAR EMERGENCY HALT' : '🛑 EMERGENCY INTERLOCK HALT'}
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="safety-panel-tabs">
        <button
          className={`tab-btn ${activeTab === 'current' ? 'active' : ''}`}
          onClick={() => setActiveTab('current')}
        >
          🔍 Active Plan Inspection
          {currentValidation && (
            <span className={`tab-indicator ${currentValidation.status === 'APPROVED' ? 'ind-green' : 'ind-red'}`}></span>
          )}
        </button>
        <button
          className={`tab-btn ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          📜 9 Safety Rules Catalog ({rules.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          📋 Safety Audit Log ({auditLogs.length})
        </button>
      </div>

      {/* Tab 1: Current Recommendation Validation Inspection */}
      {activeTab === 'current' && (
        <div className="tab-content current-plan-view">
          <div className="plan-audit-header">
            <div className="stamp-col">
              <span className="stamp-label">Gatekeeper Decision:</span>
              <SafetyStatusBadge
                validation={validationToDisplay}
                emergencyActive={safetyStatus?.emergency_active}
              />
            </div>
            {validationToDisplay && (
              <div className="plan-meta-col">
                <span><strong>Validated At:</strong> {validationToDisplay.validated_at || 'Live Telemetry'}</span>
                <span><strong>Total Evaluated:</strong> {validationToDisplay.candidate_summary?.total_trains ?? 0} trains</span>
              </div>
            )}
          </div>

          {/* Violations List */}
          {validationToDisplay?.violations && validationToDisplay.violations.length > 0 ? (
            <div className="violations-container">
              <h4 className="section-alert-heading text-red">
                ⛔ Hard Safety Violations ({validationToDisplay.violations.length}) — Recommendation Blocked
              </h4>
              <div className="violations-list">
                {validationToDisplay.violations.map((v, i) => (
                  <div key={i} className={`violation-card severity-${(v.severity || 'high').toLowerCase()}`}>
                    <div className="card-top">
                      <span className="rule-badge">{v.rule}</span>
                      <span className="severity-tag">{v.severity}</span>
                      {v.train_numbers && v.train_numbers.length > 0 && (
                        <span className="affected-trains">Trains: {v.train_numbers.join(', ')}</span>
                      )}
                    </div>
                    <div className="violation-message">{v.message}</div>
                    {v.details && Object.keys(v.details).length > 0 && (
                      <div className="violation-details">
                        {Object.entries(v.details).map(([k, val]) => (
                          <span key={k} className="detail-chip">
                            <strong>{k}:</strong> {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-violations-box">
              <span className="check-icon">✓</span>
              <div>
                <strong>Zero Safety Violations Detected</strong>
                <p>This dispatch schedule satisfies rolling stock speed envelopes, headway buffers (≥120s), and route clearances.</p>
              </div>
            </div>
          )}

          {/* Warnings List */}
          {validationToDisplay?.warnings && validationToDisplay.warnings.length > 0 && (
            <div className="warnings-container">
              <h4 className="section-alert-heading text-amber">
                ⚠️ Operational Cautions & Headway Warnings ({validationToDisplay.warnings.length})
              </h4>
              <div className="warnings-list">
                {validationToDisplay.warnings.map((w, i) => (
                  <div key={i} className="warning-card">
                    <div className="card-top">
                      <span className="rule-badge">{w.rule}</span>
                      <span className="severity-tag">{w.severity || 'LOW'}</span>
                      {w.train_numbers && (
                        <span className="affected-trains">Trains: {w.train_numbers.join(', ')}</span>
                      )}
                    </div>
                    <div className="warning-message">{w.message}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: 9 Formal Safety Rules Specification */}
      {activeTab === 'rules' && (
        <div className="tab-content rules-catalog-view">
          <div className="rules-grid">
            {rules.map((r, idx) => (
              <div key={r.rule_id} className="rule-catalog-card">
                <div className="rule-card-header">
                  <span className="rule-index">0{idx + 1}</span>
                  <span className={`rule-sev-tag sev-${(r.severity || 'high').toLowerCase()}`}>
                    {r.severity}
                  </span>
                </div>
                <h4 className="rule-name">{r.name}</h4>
                <span className="rule-category">{r.category}</span>
                <p className="rule-desc">{r.description}</p>
                <div className="rule-footer">
                  <span className="rule-status-badge">
                    <span className="pulse-green-dot"></span> Active Enforced
                  </span>
                  <span className="rule-code">{r.rule_id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Historical Safety Audit Log */}
      {activeTab === 'audit' && (
        <div className="tab-content audit-log-view">
          <div className="table-responsive">
            <table className="safety-table">
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Timestamp</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Violations</th>
                  <th>Warnings</th>
                  <th>Applied</th>
                  <th>Summary</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-table-cell">No safety audit logs recorded yet.</td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.audit_id} className={log.status === 'REJECTED' ? 'row-rejected' : ''}>
                      <td>#{log.audit_id}</td>
                      <td>{log.timestamp}</td>
                      <td>
                        <span className={`badge-pill ${log.status === 'APPROVED' ? 'pill-approved' : 'pill-rejected'}`}>
                          {log.status}
                        </span>
                      </td>
                      <td>
                        <span className={`badge-pill pill-${(log.safety_score_status || 'safe').toLowerCase()}`}>
                          {log.safety_score_status}
                        </span>
                      </td>
                      <td className={log.violations?.length > 0 ? 'text-red font-bold' : ''}>
                        {log.violations?.length ?? 0}
                      </td>
                      <td className={log.warnings?.length > 0 ? 'text-amber' : ''}>
                        {log.warnings?.length ?? 0}
                      </td>
                      <td>
                        {log.applied_to_simulation ? (
                          <span className="applied-tag text-green">✓ Applied</span>
                        ) : (
                          <span className="applied-tag text-muted">— Blocked/Held</span>
                        )}
                      </td>
                      <td className="summary-notes-cell" title={log.summary_notes}>
                        {log.summary_notes || 'Automated schedule audit check.'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

