import React from 'react';
import { Layers, Train, CheckCircle2, Ban, Radio } from 'lucide-react';

export default function TrackOccupancyPanel({ tracks }) {
  const getStatusBadge = (status) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'OCCUPIED':
        return <span className="status-chip chip-occupied"><Radio size={10} /> OCCUPIED</span>;
      case 'AVAILABLE':
        return <span className="status-chip chip-available"><CheckCircle2 size={10} /> AVAILABLE</span>;
      case 'BLOCKED':
        return <span className="status-chip chip-blocked"><Ban size={10} /> BLOCKED</span>;
      default:
        return <span className="status-chip chip-muted">{status}</span>;
    }
  };

  return (
    <div className="track-occupancy-panel">
      <div className="track-panel-header">
        <div className="panel-title-row">
          <Layers size={17} className="text-sky-400" />
          <h3>Physical Track Occupancy Rack</h3>
        </div>
        <span className="count-pill">{tracks?.length || 0} Directional Tracks</span>
      </div>

      <div className="track-rack-grid">
        {tracks?.map((track) => {
          const isOcc = track.status === 'OCCUPIED';
          return (
            <div
              key={track.track_id}
              className={`track-rack-card ${isOcc ? 'track-card-occupied' : 'track-card-available'}`}
            >
              <div className="track-card-top">
                <span className="track-id-tag">TRK-{String(track.track_id).padStart(2, '0')}</span>
                <span className="track-dir-pill">{track.direction}</span>
                {getStatusBadge(track.status)}
              </div>

              <div className="track-card-body">
                <span className="track-section-label">Section {track.section_id} (Track #{track.track_number})</span>
                {track.occupied_train_number ? (
                  <div className="track-occupied-train">
                    <Train size={13} className="text-sky-400" />
                    <strong>{track.occupied_train_number}</strong>
                    {track.occupied_train_name && <small>({track.occupied_train_name})</small>}
                  </div>
                ) : (
                  <span className="track-free-text">Track Clear</span>
                )}
              </div>

              <div className="track-card-footer">
                <span>Speed Cap: {track.maximum_speed || 100} km/h</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

