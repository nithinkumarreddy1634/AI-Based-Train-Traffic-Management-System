import React, { useState } from 'react';
import ConflictTable from '../components/ConflictTable';
import ConflictDetailsModal from '../components/ConflictDetailsModal';
import CongestionPanel from '../components/CongestionPanel';
import BottleneckPanel from '../components/BottleneckPanel';

export default function ConflictMonitoring({ simulation }) {
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [activeSubTab, setActiveSubTab] = useState('all');

  const {
    conflicts = [],
    resolvedConflicts = [],
    congestion = [],
    bottlenecks = [],
    conflictSummary = {},
    status = {},
  } = simulation;

  const topBottleneck = bottlenecks.length > 0 ? bottlenecks[0] : null;

  return (
    <div className="page-container conflict-monitoring-page">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <div className="page-tag">PHASE 5 ENGINE</div>
          <h1 className="page-title">Conflict Detection & Congestion Management</h1>
          <p className="page-description">
            Real-time kinematic collision detection, dynamic headway enforcement, and transparent capacity bottleneck ranking.
          </p>
        </div>

        <div className="header-status-badge-wrap">
          <div className="live-pulse-dot" />
          <span>Real-Time Engine: {status.running ? (status.paused ? 'PAUSED' : 'ONLINE') : 'STANDBY'}</span>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="summary-grid conflict-kpi-grid">
        <div className="card summary-card kpi-card-active-conflicts">
          <div className="summary-card-icon">⚡</div>
          <div className="summary-card-content">
            <div className="summary-card-label">ACTIVE CONFLICTS</div>
            <div className="summary-card-value">{conflicts.length}</div>
            <div className="summary-card-meta">
              <span className="text-danger fw-bold">{conflictSummary.critical_conflicts || 0} Critical</span>
              {' • '}
              <span className="text-warning">{conflictSummary.high_conflicts || 0} High</span>
            </div>
          </div>
        </div>

        <div className="card summary-card kpi-card-resolved-conflicts">
          <div className="summary-card-icon">✅</div>
          <div className="summary-card-content">
            <div className="summary-card-label">RESOLVED CONFLICTS</div>
            <div className="summary-card-value">{resolvedConflicts.length}</div>
            <div className="summary-card-meta text-success">Cleared without incident</div>
          </div>
        </div>

        <div className="card summary-card kpi-card-top-bottleneck">
          <div className="summary-card-icon">⚠️</div>
          <div className="summary-card-content">
            <div className="summary-card-label">TOP BOTTLENECK</div>
            <div className="summary-card-value">
              {topBottleneck ? `${topBottleneck.bottleneck_score}` : 'None'}
            </div>
            <div className="summary-card-meta">
              {topBottleneck ? topBottleneck.section_name : 'Nominal corridor throughput'}
            </div>
          </div>
        </div>

        <div className="card summary-card kpi-card-network-health">
          <div className="summary-card-icon">🚦</div>
          <div className="summary-card-content">
            <div className="summary-card-label">CRITICAL BOTTLENECK SECTIONS</div>
            <div className="summary-card-value">{conflictSummary.critical_bottlenecks || 0}</div>
            <div className="summary-card-meta">
              {conflictSummary.elevated_bottlenecks || 0} elevated chokepoints
            </div>
          </div>
        </div>
      </div>

      {/* Sub-Tab Navigation */}
      <div className="sub-tab-bar">
        <button
          className={`sub-tab-btn ${activeSubTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('all')}
        >
          All-In-One Overview
        </button>
        <button
          className={`sub-tab-btn ${activeSubTab === 'conflicts' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('conflicts')}
        >
          Conflicts ({conflicts.length})
        </button>
        <button
          className={`sub-tab-btn ${activeSubTab === 'bottlenecks' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('bottlenecks')}
        >
          Bottlenecks Leaderboard ({bottlenecks.length})
        </button>
        <button
          className={`sub-tab-btn ${activeSubTab === 'congestion' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('congestion')}
        >
          Section Flow & Congestion ({congestion.length})
        </button>
      </div>

      {/* Content Layout */}
      {(activeSubTab === 'all' || activeSubTab === 'conflicts') && (
        <div className="mb-4">
          <ConflictTable
            conflicts={conflicts}
            resolvedHistory={resolvedConflicts}
            onSelectConflict={(c) => setSelectedConflict(c)}
          />
        </div>
      )}

      {activeSubTab === 'all' && (
        <div className="conflict-two-col-grid">
          <BottleneckPanel bottlenecks={bottlenecks} />
          <CongestionPanel congestion={congestion} />
        </div>
      )}

      {activeSubTab === 'bottlenecks' && (
        <div className="mb-4">
          <BottleneckPanel bottlenecks={bottlenecks} />
        </div>
      )}

      {activeSubTab === 'congestion' && (
        <div className="mb-4">
          <CongestionPanel congestion={congestion} />
        </div>
      )}

      {/* Conflict Investigation Modal */}
      {selectedConflict && (
        <ConflictDetailsModal
          conflict={selectedConflict}
          onClose={() => setSelectedConflict(null)}
        />
      )}
    </div>
  );
}

