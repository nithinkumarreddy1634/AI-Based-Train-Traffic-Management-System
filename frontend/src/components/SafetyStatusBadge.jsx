import React from 'react';

/**
 * SafetyStatusBadge renders a formal fail-safe validation stamp.
 * Statuses: APPROVED (Green), WARNING (Yellow/Amber), REJECTED / CRITICAL (Red).
 */
export default function SafetyStatusBadge({ validation, emergencyActive = false }) {
  if (emergencyActive) {
    return (
      <span className="safety-badge safety-badge-critical">
        <span className="safety-indicator-dot pulse-red"></span>
        EMERGENCY INTERLOCK ACTIVE
      </span>
    );
  }

  if (!validation) {
    return (
      <span className="safety-badge safety-badge-neutral">
        <span className="safety-indicator-dot"></span>
        PENDING SAFETY AUDIT
      </span>
    );
  }

  const status = (validation.status || '').toUpperCase();
  const scoreStatus = (validation.safety_score_status || '').toUpperCase();
  const violationsCount = (validation.violations || []).length;
  const warningsCount = (validation.warnings || []).length;

  if (status === 'REJECTED' || scoreStatus === 'UNSAFE') {
    return (
      <span className="safety-badge safety-badge-rejected" title={`${violationsCount} safety violations detected`}>
        <span className="safety-indicator-dot red"></span>
        SAFETY REJECTED ({violationsCount} Violation{violationsCount === 1 ? '' : 's'})
      </span>
    );
  }

  if (scoreStatus === 'WARNING' || warningsCount > 0) {
    return (
      <span className="safety-badge safety-badge-warning" title={`${warningsCount} operational caution(s)`}>
        <span className="safety-indicator-dot amber"></span>
        APPROVED WITH CAUTION ({warningsCount} Warning{warningsCount === 1 ? '' : 's'})
      </span>
    );
  }

  return (
    <span className="safety-badge safety-badge-approved" title="All 9 safety rules strictly satisfied">
      <span className="safety-indicator-dot green"></span>
      SAFETY APPROVED (9/9 Rules Verified)
    </span>
  );
}

