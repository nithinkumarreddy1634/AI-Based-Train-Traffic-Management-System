import { useState, useEffect, useCallback } from 'react';
import { fetchHealthStatus, API_BASE_URL } from '../services/api';

export function useBackendStatus(pollIntervalMs = 5000) {
  const [status, setStatus] = useState('checking'); // 'checking' | 'connected' | 'disconnected'
  const [healthData, setHealthData] = useState(null);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const checkHealth = useCallback(async () => {
    const start = performance.now();
    try {
      const data = await fetchHealthStatus();
      const elapsed = Math.round(performance.now() - start);
      setLatency(elapsed);
      setHealthData(data);
      setStatus('connected');
      setError(null);
      setLastChecked(new Date());
    } catch (err) {
      const elapsed = Math.round(performance.now() - start);
      setLatency(elapsed);
      setStatus('disconnected');
      setHealthData(null);
      setError(
        err.response?.data?.message ||
        err.message ||
        `Unable to reach backend at ${API_BASE_URL}`
      );
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [checkHealth, pollIntervalMs]);

  return {
    status,
    healthData,
    error,
    latency,
    lastChecked,
    refetch: checkHealth,
  };
}

