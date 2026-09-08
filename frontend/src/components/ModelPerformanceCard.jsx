import React from 'react';

export default function ModelPerformanceCard({ modelInfo }) {
  if (!modelInfo || !modelInfo.metrics) {
    return (
      <div className="card model-performance-card">
        <div className="card-header">
          <h3 className="card-title">ML Model Benchmark & Intelligence</h3>
        </div>
        <div className="card-body">
          <p className="text-slate-400">Loading model performance metrics...</p>
        </div>
      </div>
    );
  }

  const {
    model_name = 'HistGradientBoosting',
    metrics = { MAE: 0.851, RMSE: 1.118, R2: 0.9782 },
    all_model_comparison = {},
    feature_importances = [],
    dataset_size = 6500,
    version = '1.0.0',
    training_date = '',
  } = modelInfo;

  return (
    <div className="card model-performance-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">PRODUCTION REGRESSION MODEL</div>
          <h3 className="card-title">
            {model_name} <span className="version-pill">v{version}</span>
          </h3>
        </div>
        <span className="badge badge-success">Active Production Pipeline</span>
      </div>

      <div className="card-body">
        {/* Top 3 KPI Badges */}
        <div className="model-kpi-row">
          <div className="kpi-metric-box">
            <span className="metric-label">MEAN ABSOLUTE ERROR</span>
            <div className="metric-num text-emerald-400">{metrics.MAE} <small>min</small></div>
            <span className="metric-sub">Average error margin</span>
          </div>

          <div className="kpi-metric-box">
            <span className="metric-label">ROOT MEAN SQ ERROR</span>
            <div className="metric-num text-sky-400">{metrics.RMSE} <small>min</small></div>
            <span className="metric-sub">Standard deviation of residuals</span>
          </div>

          <div className="kpi-metric-box">
            <span className="metric-label">R² ACCURACY SCORE</span>
            <div className="metric-num text-purple-400">{(metrics.R2 * 100).toFixed(1)}%</div>
            <span className="metric-sub">Variance explained (R²: {metrics.R2})</span>
          </div>

          <div className="kpi-metric-box">
            <span className="metric-label">TRAINING DATASET</span>
            <div className="metric-num text-amber-400">{dataset_size.toLocaleString()}</div>
            <span className="metric-sub">Domain synthetic records</span>
          </div>
        </div>

        {/* Feature Importance & Model Comparison 2-Column */}
        <div className="model-intel-grid">
          {/* Top Feature Importances */}
          <div className="intel-col">
            <h4 className="intel-col-title">Top Influential Features (Weighting)</h4>
            <div className="feature-importance-list">
              {feature_importances.slice(0, 6).map((item, idx) => (
                <div key={idx} className="feat-imp-item">
                  <div className="feat-imp-header">
                    <span className="feat-name">{item.feature}</span>
                    <span className="feat-pct">{item.percentage}%</span>
                  </div>
                  <div className="feat-bar-track">
                    <div
                      className="feat-bar-fill"
                      style={{
                        width: `${Math.min(100, item.percentage * 2.5)}%`,
                        background: idx === 0
                          ? 'linear-gradient(90deg, #38bdf8, #0284c7)'
                          : idx === 1
                          ? 'linear-gradient(90deg, #a855f7, #7e22ce)'
                          : 'linear-gradient(90deg, #10b981, #059669)',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Model Comparison Benchmark Table */}
          <div className="intel-col">
            <h4 className="intel-col-title">Candidate Models Benchmark Comparison</h4>
            <div className="table-responsive">
              <table className="comparison-mini-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>MAE</th>
                    <th>RMSE</th>
                    <th>R²</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(all_model_comparison).map(([name, m]) => {
                    const isSelected = name === model_name;
                    return (
                      <tr key={name} className={isSelected ? 'selected-model-row' : ''}>
                        <td>
                          <strong>{name}</strong>
                          {isSelected && <span className="selected-tag">BEST</span>}
                        </td>
                        <td>{m.MAE} min</td>
                        <td>{m.RMSE} min</td>
                        <td>
                          <span className={isSelected ? 'text-success fw-bold' : ''}>
                            {m.R2}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

