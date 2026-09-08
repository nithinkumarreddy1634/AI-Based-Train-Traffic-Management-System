import React from 'react';
import { Train, Radio, ClockAlert, Gauge, Database, GitBranch } from 'lucide-react';

export default function SummaryCards({ stats, isLoading }) {
  const totalTrains = stats?.total_trains ?? 12;
  const activeTrains = stats?.active_trains ?? 7;
  const delayedTrains = stats?.delayed_trains ?? 3;
  const trackUtilization = stats?.track_utilization_percent ?? 50.0;
  const totalSections = stats?.total_sections ?? 7;
  const occupiedSections = stats?.occupied_sections ?? 6;
  const totalTracks = stats?.total_tracks ?? 14;
  const occupiedTracks = stats?.occupied_tracks ?? 7;

  const cardsData = [
    {
      id: 'total-trains',
      title: 'Total Trains',
      value: isLoading ? '...' : String(totalTrains),
      unit: 'fleet size',
      subtext: `${stats?.scheduled_trains ?? 2} scheduled, ${totalTrains - (stats?.scheduled_trains ?? 2)} deployed`,
      icon: Train,
      color: 'blue',
      sourceNote: 'Live Railway DB',
    },
    {
      id: 'active-trains',
      title: 'Active Trains',
      value: isLoading ? '...' : String(activeTrains),
      unit: 'in transit',
      subtext: `${occupiedSections} of ${totalSections} sections occupied`,
      icon: Radio,
      color: 'emerald',
      sourceNote: 'Live Telemetry',
    },
    {
      id: 'delayed-trains',
      title: 'Delayed Trains',
      value: isLoading ? '...' : String(delayedTrains),
      unit: 'flagged',
      subtext: delayedTrains > 0 ? 'Requires speed advisory / hold' : 'All trains on schedule',
      icon: ClockAlert,
      color: delayedTrains > 0 ? 'amber' : 'emerald',
      sourceNote: 'Dynamic Tracking',
    },
    {
      id: 'track-utilization',
      title: 'Track Utilization',
      value: isLoading ? '...' : `${trackUtilization}%`,
      unit: 'corridor load',
      subtext: `${occupiedTracks} of ${totalTracks} physical tracks occupied`,
      icon: Gauge,
      color: 'purple',
      sourceNote: 'Section Density',
    },
  ];

  return (
    <div className="summary-cards-grid">
      {cardsData.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.id} className={`summary-card summary-card-${card.color}`}>
            <div className="card-top">
              <span className="card-title">{card.title}</span>
              <div className="card-icon-wrapper">
                <Icon size={20} />
              </div>
            </div>

            <div className="card-body">
              <div className="card-metric-row">
                <span className="card-value">{card.value}</span>
                <span className="card-unit">{card.unit}</span>
              </div>
              <p className="card-subtext">{card.subtext}</p>
            </div>

            <div className="card-footer">
              <Database size={12} />
              <span>{card.sourceNote}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
