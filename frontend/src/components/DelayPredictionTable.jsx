import React, { useState } from 'react';

export default function DelayPredictionTable({ predictions = [], onSelectTrain }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  const filtered = predictions.filter((p) => {
    const matchesSearch =
      !searchQuery ||
      p.train_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.train_name?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesType =
      filterType === 'ALL' || p.train_type === filterType;

    return matchesSearch && matchesType;
  });

  const getAdditionalDelayBadge = (addDelay) => {
    if (addDelay <= 0.5) {
      return <span className="delay-chip delay-chip-green">+{addDelay} min (Nominal)</span>;
    }
    if (addDelay <= 4.0) {
      return <span className="delay-chip delay-chip-amber">+{addDelay} min (Moderate)</span>;
    }
    return <span className="delay-chip delay-chip-red">+{addDelay} min (High Risk)</span>;
  };

  return (
    <div className="card delay-prediction-table-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">REAL-TIME FORECAST STREAM</div>
          <h3 className="card-title">Active Train Delay Forecast</h3>
        </div>

        <div className="table-filter-toolbar">
          <input
            type="text"
            className="filter-input search-box"
            placeholder="Search train..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <select
            className="filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="ALL">All Train Types</option>
            <option value="EXPRESS">Express</option>
            <option value="PASSENGER">Passenger</option>
            <option value="LOCAL">Local</option>
            <option value="FREIGHT">Freight</option>
          </select>
        </div>
      </div>

      <div className="card-body p-0">
        {filtered.length === 0 ? (
          <div className="empty-state-card">
            <p>No active trains currently matching filter.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="delay-table">
              <thead>
                <tr>
                  <th>Train</th>
                  <th>Type / Priority</th>
                  <th>Current Delay</th>
                  <th>Predicted Total Delay</th>
                  <th>Expected Added Delay</th>
                  <th>Speed / Distance</th>
                  <th>Status</th>
                  <th>Forecast Time</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr
                    key={item.train_id}
                    className="delay-table-row"
                    onClick={() => onSelectTrain && onSelectTrain(item)}
                  >
                    <td>
                      <div className="train-id-badge">{item.train_number}</div>
                      <div className="train-name-sub">{item.train_name}</div>
                    </td>
                    <td>
                      <span className="type-tag">{item.train_type}</span>
                      <span className={`prio-tag prio-${item.priority.toLowerCase()}`}>
                        {item.priority}
                      </span>
                    </td>
                    <td>
                      <span className="delay-val current-delay-val">
                        {item.current_delay_minutes} min
                      </span>
                    </td>
                    <td>
                      <span className="delay-val predicted-delay-val">
                        {item.predicted_delay_minutes} min
                      </span>
                    </td>
                    <td>
                      {getAdditionalDelayBadge(item.expected_additional_delay)}
                    </td>
                    <td>
                      <div className="numeric-meta">
                        {item.current_speed_kmph} km/h | {item.distance_remaining_km} km rem
                      </div>
                    </td>
                    <td>
                      <span className={`status-dot status-${item.status.toLowerCase()}`}>
                        {item.status}
                      </span>
                    </td>
                    <td>
                      <span className="timestamp-cell">{item.last_prediction_time || 'Live'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

