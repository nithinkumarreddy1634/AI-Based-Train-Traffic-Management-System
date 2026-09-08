/**
 * Shared formatting utilities for the Train Traffic Control frontend.
 */

export function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '--:--';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const pad = (n) => String(n).padStart(2, '0');
  if (hrs > 0) {
    return `${pad(hrs)}:${pad(mins)}:${pad(secs)}`;
  }
  return `${pad(mins)}:${pad(secs)}`;
}

export function formatDelay(minutes) {
  if (minutes === null || minutes === undefined || isNaN(minutes)) return '0m';
  const rounded = Math.round(minutes * 10) / 10;
  if (rounded === 0) return 'On Time';
  if (rounded > 0) return `+${rounded}m`;
  return `${rounded}m`;
}

export function formatSpeed(kmph) {
  if (kmph === null || kmph === undefined || isNaN(kmph)) return '0 km/h';
  return `${Math.round(kmph)} km/h`;
}

export function formatPercent(val) {
  if (val === null || val === undefined || isNaN(val)) return '0%';
  return `${Math.round(val * 10) / 10}%`;
}

export function getStatusColor(status) {
  const norm = String(status || '').toUpperCase();
  switch (norm) {
    case 'RUNNING':
    case 'CLEAR':
    case 'FREE':
    case 'NORMAL':
    case 'HEALTHY':
    case 'APPROVED':
      return 'emerald';
    case 'WAITING':
    case 'OCCUPIED':
    case 'CONGESTED':
    case 'MEDIUM':
      return 'amber';
    case 'BLOCKED':
    case 'EMERGENCY':
    case 'STOPPED':
    case 'REJECTED':
    case 'CRITICAL':
      return 'rose';
    default:
      return 'blue';
  }
}

