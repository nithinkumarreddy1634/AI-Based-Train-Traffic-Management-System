import React, { useState } from 'react';
import { predictDelay } from '../services/api';

export default function WhatIfDelayCalculator() {
  const [formData, setFormData] = useState({
    train_type: 'EXPRESS',
    priority: 'HIGH',
    scheduled_duration: 60,
    distance_remaining_km: 35,
    current_speed_kmph: 75,
    maximum_speed_kmph: 120,
    current_delay_minutes: 5,
    number_of_stops_remaining: 2,
    station_dwell_time: 4,
    number_of_trains_in_section: 3,
    section_utilization: 72,
    traffic_density: 65,
    waiting_train_count: 1,
    time_of_day: 'EVENING',
    day_type: 'WEEKDAY',
  });

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleRunPrediction = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await predictDelay(formData);
      setPrediction(res);
    } catch (err) {
      console.error('Prediction calculation error:', err);
      setError('Failed to compute prediction. Check backend status.');
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (presetType) => {
    if (presetType === 'low') {
      setFormData({
        train_type: 'EXPRESS',
        priority: 'HIGH',
        scheduled_duration: 60,
        distance_remaining_km: 30,
        current_speed_kmph: 115,
        maximum_speed_kmph: 120,
        current_delay_minutes: 0,
        number_of_stops_remaining: 1,
        station_dwell_time: 2,
        number_of_trains_in_section: 1,
        section_utilization: 15,
        traffic_density: 10,
        waiting_train_count: 0,
        time_of_day: 'NIGHT',
        day_type: 'WEEKDAY',
      });
    } else if (presetType === 'congested') {
      setFormData({
        train_type: 'FREIGHT',
        priority: 'LOW',
        scheduled_duration: 120,
        distance_remaining_km: 45,
        current_speed_kmph: 20,
        maximum_speed_kmph: 75,
        current_delay_minutes: 10,
        number_of_stops_remaining: 3,
        station_dwell_time: 5,
        number_of_trains_in_section: 4,
        section_utilization: 90,
        traffic_density: 85,
        waiting_train_count: 2,
        time_of_day: 'MORNING',
        day_type: 'WEEKDAY',
      });
    }
  };

  return (
    <div className="card what-if-calculator-card">
      <div className="card-header">
        <div>
          <div className="card-subtitle">DISPATCHER SCENARIO SANDBOX</div>
          <h3 className="card-title">What-If Delay Prediction Simulator</h3>
        </div>

        <div className="preset-btn-group">
          <button
            type="button"
            className="preset-btn"
            onClick={() => loadPreset('low')}
          >
            Load Low-Traffic Preset
          </button>
          <button
            type="button"
            className="preset-btn preset-congested"
            onClick={() => loadPreset('congested')}
          >
            Load Heavy-Traffic Preset
          </button>
        </div>
      </div>

      <div className="card-body">
        <form onSubmit={handleRunPrediction} className="whatif-form-grid">
          {/* Column 1: Train Kinematics */}
          <div className="form-col">
            <h4 className="form-section-title">Train Kinematics & Schedule</h4>

            <div className="form-group">
              <label>Train Category</label>
              <select
                name="train_type"
                value={formData.train_type}
                onChange={handleChange}
                className="form-input"
              >
                <option value="EXPRESS">Express Passenger</option>
                <option value="PASSENGER">Standard Passenger</option>
                <option value="LOCAL">Local Commuter</option>
                <option value="FREIGHT">Heavy Freight</option>
              </select>
            </div>

            <div className="form-group">
              <label>Dispatch Priority</label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className="form-input"
              >
                <option value="HIGH">High Priority (1)</option>
                <option value="MEDIUM">Medium Priority (2)</option>
                <option value="LOW">Low Priority (3)</option>
              </select>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>Current Speed (km/h)</label>
                <input
                  type="number"
                  name="current_speed_kmph"
                  value={formData.current_speed_kmph}
                  onChange={handleChange}
                  min="0"
                  max="160"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Max Speed Limit</label>
                <input
                  type="number"
                  name="maximum_speed_kmph"
                  value={formData.maximum_speed_kmph}
                  onChange={handleChange}
                  min="40"
                  max="160"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>Current Delay (min)</label>
                <input
                  type="number"
                  step="0.5"
                  name="current_delay_minutes"
                  value={formData.current_delay_minutes}
                  onChange={handleChange}
                  min="0"
                  className="form-input text-amber-400 fw-bold"
                />
              </div>
              <div className="form-group">
                <label>Remaining Dist (km)</label>
                <input
                  type="number"
                  name="distance_remaining_km"
                  value={formData.distance_remaining_km}
                  onChange={handleChange}
                  min="1"
                  className="form-input"
                />
              </div>
            </div>
          </div>

          {/* Column 2: Infrastructure & Congestion */}
          <div className="form-col">
            <h4 className="form-section-title">Section Traffic & Bottleneck State</h4>

            <div className="form-row-2">
              <div className="form-group">
                <label>Section Utilization (%)</label>
                <input
                  type="number"
                  name="section_utilization"
                  value={formData.section_utilization}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Traffic Density (%)</label>
                <input
                  type="number"
                  name="traffic_density"
                  value={formData.traffic_density}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>Trains in Section</label>
                <input
                  type="number"
                  name="number_of_trains_in_section"
                  value={formData.number_of_trains_in_section}
                  onChange={handleChange}
                  min="1"
                  max="6"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Waiting Trains</label>
                <input
                  type="number"
                  name="waiting_train_count"
                  value={formData.waiting_train_count}
                  onChange={handleChange}
                  min="0"
                  max="5"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>Stops Remaining</label>
                <input
                  type="number"
                  name="number_of_stops_remaining"
                  value={formData.number_of_stops_remaining}
                  onChange={handleChange}
                  min="0"
                  max="10"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Dwell Time (min)</label>
                <input
                  type="number"
                  step="0.5"
                  name="station_dwell_time"
                  value={formData.station_dwell_time}
                  onChange={handleChange}
                  min="0"
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label>Time of Day</label>
                <select
                  name="time_of_day"
                  value={formData.time_of_day}
                  onChange={handleChange}
                  className="form-input"
                >
                  <option value="MORNING">Morning Peak</option>
                  <option value="AFTERNOON">Afternoon</option>
                  <option value="EVENING">Evening Peak</option>
                  <option value="NIGHT">Night / Low Traffic</option>
                </select>
              </div>
              <div className="form-group">
                <label>Day Type</label>
                <select
                  name="day_type"
                  value={formData.day_type}
                  onChange={handleChange}
                  className="form-input"
                >
                  <option value="WEEKDAY">Weekday</option>
                  <option value="WEEKEND">Weekend</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary run-predict-btn"
            >
              {loading ? 'Computing ML Forecast...' : '⚡ Compute Delay Forecast'}
            </button>
          </div>
        </form>

        {error && <div className="error-banner mt-3">{error}</div>}

        {/* Prediction Results Card */}
        {prediction && (
          <div className="prediction-result-banner mt-4">
            <div className="result-metric-card">
              <span className="res-label">CURRENT DELAY</span>
              <div className="res-num">{prediction.current_delay_minutes} <small>min</small></div>
            </div>

            <div className="result-operator">+</div>

            <div className="result-metric-card highlight-added">
              <span className="res-label">EXPECTED ADDED DELAY</span>
              <div className="res-num text-amber-400">
                +{prediction.expected_additional_delay} <small>min</small>
              </div>
            </div>

            <div className="result-operator">=</div>

            <div className="result-metric-card highlight-total">
              <span className="res-label">PROJECTED TOTAL ARRIVAL DELAY</span>
              <div className="res-num text-rose-400">
                {prediction.predicted_delay_minutes} <small>min</small>
              </div>
            </div>

            <div className="result-meta-box">
              <div>Model: <strong>{prediction.model}</strong></div>
              <div>Status: <span className="text-success">Verified</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

