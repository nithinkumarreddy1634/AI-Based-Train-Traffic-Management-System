import { useState, useEffect, useRef, useCallback } from 'react';
import {
  WS_BASE_URL,
  startSimulation,
  pauseSimulation,
  resumeSimulation,
  resetSimulation,
  setSimulationSpeed,
  fetchSimulationState,
  clearAlerts as clearAlertsApi,
  clearEvents as clearEventsApi,
} from '../services/api';

export function useSimulation() {
  const [simulationStatus, setSimulationStatus] = useState({
    running: false,
    paused: false,
    simulation_time: '00:00:00',
    speed_multiplier: 1.0,
    active_trains: 0,
    delayed_trains: 0,
    completed_trains: 0,
    throughput_trains_per_hour: 0.0,
  });

  const [summary, setSummary] = useState({
    total_trains: 12,
    running_trains: 0,
    waiting_trains: 0,
    delayed_trains: 0,
    arrived_trains: 0,
    stopped_trains: 0,
    total_sections: 7,
    occupied_sections: 0,
    total_tracks: 14,
    occupied_tracks: 0,
    throughput_trains_per_hour: 0.0,
    completed_trains: 0,
  });

  const [liveTrains, setLiveTrains] = useState([]);
  const [liveTracks, setLiveTracks] = useState([]);
  const [liveSections, setLiveSections] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [density, setDensity] = useState({ network_density: 'LOW', average_trains_per_section: 0, sections: [] });
  const [utilization, setUtilization] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [resolvedConflicts, setResolvedConflicts] = useState([]);
  const [congestion, setCongestion] = useState([]);
  const [bottlenecks, setBottlenecks] = useState([]);
  const [conflictSummary, setConflictSummary] = useState({
    total_active_conflicts: 0,
    critical_conflicts: 0,
    high_conflicts: 0,
    medium_conflicts: 0,
    low_conflicts: 0,
    total_resolved_conflicts: 0,
    critical_bottlenecks: 0,
    elevated_bottlenecks: 0,
  });
  const [mlPredictions, setMlPredictions] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [isWsConnected, setIsWsConnected] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // Fallback Polling Function
  const pollFallback = useCallback(async () => {
    try {
      const state = await fetchSimulationState();
      if (state) {
        if (state.status) setSimulationStatus(state.status);
        if (state.summary) setSummary(state.summary);
        if (state.trains) setLiveTrains(state.trains);
        if (state.tracks) setLiveTracks(state.tracks);
        if (state.sections) setLiveSections(state.sections);
        if (state.alerts) setAlerts(state.alerts);
        if (state.density) setDensity(state.density);
        if (state.utilization) setUtilization(state.utilization);
        if (state.events) setRecentEvents(state.events);
        if (state.conflicts) setConflicts(state.conflicts);
        if (state.resolved_conflicts) setResolvedConflicts(state.resolved_conflicts);
        if (state.congestion) setCongestion(state.congestion);
        if (state.bottlenecks) setBottlenecks(state.bottlenecks);
        if (state.conflict_summary) setConflictSummary(state.conflict_summary);
        if (state.ml_predictions) setMlPredictions(state.ml_predictions);
        if (state.model_info) setModelInfo(state.model_info);
      }
    } catch (err) {
      console.warn('Fallback polling error:', err);
    }
  }, []);

  // Initialize WebSocket Connection
  useEffect(() => {
    let isMounted = true;

    const connectWebSocket = () => {
      try {
        const wsUrl = `${WS_BASE_URL}/ws/train-updates`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isMounted) {
            setIsWsConnected(true);
            // Clear polling fallback if WS is active
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            if (data.status) setSimulationStatus(data.status);
            if (data.summary) setSummary(data.summary);
            if (data.trains) setLiveTrains(data.trains);
            if (data.tracks) setLiveTracks(data.tracks);
            if (data.sections) setLiveSections(data.sections);
            if (data.alerts) setAlerts(data.alerts);
            if (data.density) setDensity(data.density);
            if (data.utilization) setUtilization(data.utilization);
            if (data.events) setRecentEvents(data.events);
            if (data.conflicts) setConflicts(data.conflicts);
            if (data.resolved_conflicts) setResolvedConflicts(data.resolved_conflicts);
            if (data.congestion) setCongestion(data.congestion);
            if (data.bottlenecks) setBottlenecks(data.bottlenecks);
            if (data.conflict_summary) setConflictSummary(data.conflict_summary);
            if (data.ml_predictions) setMlPredictions(data.ml_predictions);
            if (data.model_info) setModelInfo(data.model_info);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        ws.onclose = () => {
          if (isMounted) {
            setIsWsConnected(false);
            // Start polling fallback while reconnecting
            if (!pollingIntervalRef.current) {
              pollingIntervalRef.current = setInterval(pollFallback, 1500);
            }
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
          }
        };

        ws.onerror = (err) => {
          console.warn('WebSocket error, falling back to polling:', err);
          ws.close();
        };
      } catch (err) {
        console.error('WebSocket initialization error:', err);
        if (!pollingIntervalRef.current) {
          pollingIntervalRef.current = setInterval(pollFallback, 1500);
        }
      }
    };

    // Initial fetch and WS connect
    pollFallback();
    connectWebSocket();

    return () => {
      isMounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [pollFallback]);

  // Simulation Actions
  const handleStart = async () => {
    setActionLoading(true);
    try {
      const res = await startSimulation();
      if (res?.status) setSimulationStatus(res.status);
    } catch (err) {
      console.error('Failed to start simulation:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePause = async () => {
    setActionLoading(true);
    try {
      const res = await pauseSimulation();
      if (res?.status) setSimulationStatus(res.status);
    } catch (err) {
      console.error('Failed to pause simulation:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      const res = await resumeSimulation();
      if (res?.status) setSimulationStatus(res.status);
    } catch (err) {
      console.error('Failed to resume simulation:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReset = async () => {
    setActionLoading(true);
    try {
      const res = await resetSimulation();
      if (res?.status) setSimulationStatus(res.status);
      await pollFallback();
    } catch (err) {
      console.error('Failed to reset simulation:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSetSpeed = async (multiplier) => {
    try {
      const res = await setSimulationSpeed(multiplier);
      if (res?.status) setSimulationStatus(res.status);
    } catch (err) {
      console.error('Failed to set simulation speed:', err);
    }
  };

  const handleClearAlerts = async () => {
    try {
      await clearAlertsApi();
      setAlerts([]);
    } catch (err) {
      console.error('Failed to clear alerts:', err);
    }
  };

  const handleClearEvents = async () => {
    try {
      await clearEventsApi();
      setRecentEvents([]);
    } catch (err) {
      console.error('Failed to clear events:', err);
    }
  };

  return {
    status: simulationStatus,
    summary,
    trains: liveTrains,
    tracks: liveTracks,
    sections: liveSections,
    alerts,
    density,
    utilization,
    events: recentEvents,
    conflicts,
    resolvedConflicts,
    congestion,
    bottlenecks,
    conflictSummary,
    mlPredictions,
    modelInfo,
    isWsConnected,
    actionLoading,
    start: handleStart,
    pause: handlePause,
    resume: handleResume,
    reset: handleReset,
    setSpeed: handleSetSpeed,
    clearAlerts: handleClearAlerts,
    clearEvents: handleClearEvents,
    refresh: pollFallback,
  };
}


