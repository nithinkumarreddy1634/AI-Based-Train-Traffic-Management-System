import React from 'react';
import { Activity, Gauge, TrendingUp, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function TrafficDensityCard({ density }) {
  const netDensity = (density?.network_density || 'LOW').toUpperCase();
  const avgTrains = density?.average_trains_per_section ?? 0.0;
  const activeCount = density?.total_active_trains_in_sections ?? 0;
  const sections = density?.sections || [];

  const getDensityColor = (lvl) => {
    switch (lvl) {
      case 'CRITICAL':
        return { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.4)' };
      case 'HIGH':
        return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)' };
      case 'MEDIUM':
        return { color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.4)' };
      default:
        return { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.4)' };
    }
  };

  const style = getDensityColor(netDensity);

  return (
    <div className="density-card">
      <div className="density-card-header">
        <div className="density-title-group">
          <Activity size={18} className="text-sky-400" />
          <h4>Corridor Traffic Density</h4>
        </div>
        <div
          className="density-badge"
          style={{ color: style.color, background: style.bg, borderColor: style.border }}
        >
          <span className="state-pulse-dot" style={{ background: style.color, boxShadow: `0 0 6px ${style.color}` }} />
          <span>{netDensity} LOAD</span>
        </div>
      </div>

      <div className="density-metrics-row">
        <div className="density-metric">
          <span className="d-label">Average Load / Section</span>
          <span className="d-val">{avgTrains} <small>trains/sec</small></span>
        </div>
        <div className="density-metric">
          <span className="d-label">Active Block Ingress</span>
          <span className="d-val">{activeCount} <small>trains moving</small></span>
        </div>
      </div>

      {/* Mini Section Density Bar Distribution */}
      <div className="section-density-bars">
        <span className="d-subtext">Section Saturation Spectrum:</span>
        <div className="bars-row">
          {sections.map((s) => {
            const sStyle = getDensityColor(s.density);
            return (
              <div
                key={s.section_id}
                className="density-mini-bar"
                title={`${s.section_name}: ${s.train_count} train(s) [${s.density}]`}
              >
                <div
                  className="bar-fill"
                  style={{
                    height: `${Math.max(20, Math.min(100, s.train_count * 45))}%`,
                    background: sStyle.color,
                  }}
                />
                <span className="bar-label">S{s.section_id}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

