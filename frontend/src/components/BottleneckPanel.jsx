import React from 'react';

export default function BottleneckPanel({ bottlenecks = [] }) {
  const getTrafficLevelBadgeClass = (level) => {
    switch (level) {
      case 'CRITICAL': return 'badge-critical';
      case 'ELEVATED': return 'badge-high';
      default: return 'badge-low';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return '#ef4444';
    if (score >= 45) return '#f59e0b';
    if (score >= 20) return '#3b82f6';
    return '#10b981';
  };

  return (
    <div className="card bottleneck-panel-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">CAPACITY CHOKEPOINT LEADERBOARD</div>
          <h3 className="card-title">Transparent Bottleneck Analysis & Scoring</h3>
        </div>
        <span className="badge badge-primary">Ranked by Bottleneck Severity</span>
      </div>

      <div className="card-body">
        {bottlenecks.length === 0 ? (
          <div className="empty-state-card">
            <p>No bottleneck data available.</p>
          </div>
        ) : (
          <div className="bottleneck-list">
            {bottlenecks.map((item, idx) => {
              const rank = idx + 1;
              const score = item.bottleneck_score || 0;
              const isTop3 = rank <= 3 && score > 0;

              return (
                <div
                  key={item.section_id}
                  className={`bottleneck-card ${isTop3 ? 'bottleneck-card-hot' : ''}`}
                >
                  <div className="bottleneck-main-row">
                    <div className="rank-badge-wrap">
                      <span className={`rank-badge ${rank === 1 ? 'rank-gold' : rank === 2 ? 'rank-silver' : ''}`}>
                        #{rank}
                      </span>
                    </div>

                    <div className="bottleneck-info">
                      <div className="bottleneck-name-wrap">
                        <span className="bottleneck-name">{item.section_name}</span>
                        <span className={`badge ${getTrafficLevelBadgeClass(item.traffic_level)}`}>
                          {item.traffic_level}
                        </span>
                      </div>
                      <div className="bottleneck-explanation">
                        <strong>Diagnosis:</strong> {item.explanation}
                      </div>
                    </div>

                    <div className="bottleneck-score-wrap">
                      <div className="score-val" style={{ color: getScoreColor(score) }}>
                        {score}
                      </div>
                      <div className="score-label">BOTTLENECK INDEX</div>
                      <div className="score-gauge-mini">
                        <div
                          className="score-gauge-fill"
                          style={{
                            width: `${Math.min(100, score)}%`,
                            backgroundColor: getScoreColor(score),
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Factor Breakdown Chips */}
                  {item.factors && (
                    <div className="factor-breakdown-row">
                      <span className="factor-chip">
                        Wait Factor: <strong>{item.factors.waiting_score?.toFixed(0)}</strong>
                      </span>
                      <span className="factor-chip">
                        Density Factor: <strong>{item.factors.density_score?.toFixed(0)}</strong>
                      </span>
                      <span className="factor-chip">
                        Utilization: <strong>{item.factors.utilization_score?.toFixed(0)}%</strong>
                      </span>
                      <span className="factor-chip">
                        Speed Loss: <strong>{item.factors.speed_drop_score?.toFixed(0)}%</strong>
                      </span>
                    </div>
                  )}

                  {/* Mitigation Advice */}
                  <div className="bottleneck-mitigation-row">
                    <span className="mitigation-icon">💡</span>
                    <span className="mitigation-text">
                      <strong>Mitigation Strategy:</strong> {item.recommendation}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

