import React, { useState } from 'react';

export default function ConflictTable({
  conflicts = [],
  resolvedHistory = [],
  onSelectConflict,
}) {
  const [activeTab, setActiveTab] = useState('active');
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');

  const dataset = activeTab === 'active' ? conflicts : resolvedHistory;

  const filteredConflicts = dataset.filter((c) => {
    const matchesSearch =
      !searchQuery ||
      c.conflict_id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.train_number_1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.train_number_2 && c.train_number_2.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (c.section_name && c.section_name.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesSeverity =
      severityFilter === 'ALL' || c.severity === severityFilter;

    const matchesType =
      typeFilter === 'ALL' || c.conflict_type === typeFilter;

    return matchesSearch && matchesSeverity && matchesType;
  });

  const getSeverityBadgeClass = (sev) => {
    switch (sev) {
      case 'CRITICAL': return 'badge-critical';
      case 'HIGH': return 'badge-high';
      case 'MEDIUM': return 'badge-medium';
      case 'LOW': return 'badge-low';
      default: return 'badge-info';
    }
  };

  const getUrgencyBadgeClass = (urg) => {
    switch (urg) {
      case 'IMMEDIATE': return 'urgency-immediate';
      case 'SOON': return 'urgency-soon';
      default: return 'urgency-monitor';
    }
  };

  return (
    <div className="card conflict-table-card">
      <div className="card-header conflict-table-header">
        <div className="tab-group-pill">
          <button
            className={`pill-btn ${activeTab === 'active' ? 'active' : ''}`}
            onClick={() => setActiveTab('active')}
          >
            Active Conflicts ({conflicts.length})
          </button>
          <button
            className={`pill-btn ${activeTab === 'resolved' ? 'active' : ''}`}
            onClick={() => setActiveTab('resolved')}
          >
            Resolved History ({resolvedHistory.length})
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="conflict-filters">
          <input
            type="text"
            className="filter-input search-box"
            placeholder="Search train, section, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <select
            className="filter-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            className="filter-select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="ALL">All Types</option>
            <option value="SAME_SECTION">Same Section</option>
            <option value="REAR_END">Rear End</option>
            <option value="OPPOSITE_DIRECTION">Head-On / Opposite</option>
            <option value="JUNCTION">Junction</option>
            <option value="INSUFFICIENT_HEADWAY">Headway</option>
          </select>
        </div>
      </div>

      <div className="card-body p-0">
        {filteredConflicts.length === 0 ? (
          <div className="empty-conflicts-state">
            <span className="empty-icon">🛡️</span>
            <h4>{activeTab === 'active' ? 'Zero Active Conflicts Detected' : 'No Resolved Conflicts in History'}</h4>
            <p>
              {activeTab === 'active'
                ? 'Railway block sections operating with nominal headway and clear clearance margins.'
                : 'Resolved conflicts will be logged here as trains clear occupied blocks.'}
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="conflict-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Conflict ID / Type</th>
                  <th>Affected Trains</th>
                  <th>Section</th>
                  <th>Gap</th>
                  <th>TTC</th>
                  <th>Urgency</th>
                  <th>Advisory Action</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredConflicts.map((c) => {
                  const ttcDisplay = c.time_to_conflict_seconds !== null && c.time_to_conflict_seconds !== undefined
                    ? `${c.time_to_conflict_seconds}s`
                    : '—';

                  return (
                    <tr key={c.conflict_id} className={`conflict-row-${c.severity.toLowerCase()}`}>
                      <td>
                        <span className={`badge ${getSeverityBadgeClass(c.severity)}`}>
                          {c.severity}
                        </span>
                      </td>
                      <td>
                        <div className="cell-main-title">{c.conflict_id}</div>
                        <div className="cell-sub-type">{c.conflict_type.replace('_', ' ')}</div>
                      </td>
                      <td>
                        <div className="trains-pair-cell">
                          <span className="train-chip chip-primary">{c.train_number_1}</span>
                          {c.train_number_2 ? (
                            <>
                              <span className="pair-separator">↔</span>
                              <span className="train-chip chip-secondary">{c.train_number_2}</span>
                            </>
                          ) : (
                            <span className="single-target-tag">Fixed Block</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="section-label">{c.section_name || `Sec #${c.section_id}`}</span>
                      </td>
                      <td>
                        <span className="numeric-data">{c.distance_km?.toFixed(2)} km</span>
                      </td>
                      <td>
                        <span className={`numeric-data ${c.time_to_conflict_seconds && c.time_to_conflict_seconds <= 60 ? 'text-danger fw-bold' : ''}`}>
                          {ttcDisplay}
                        </span>
                      </td>
                      <td>
                        <span className={`urgency-pill ${getUrgencyBadgeClass(c.urgency)}`}>
                          {c.urgency}
                        </span>
                      </td>
                      <td className="recommendation-cell">
                        <span className="rec-snippet" title={c.recommendation}>
                          {c.recommendation ? c.recommendation.slice(0, 55) + '...' : 'Monitor'}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn-investigate"
                          onClick={() => onSelectConflict(c)}
                          title="View kinematic dossier and advice"
                        >
                          Investigate
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

