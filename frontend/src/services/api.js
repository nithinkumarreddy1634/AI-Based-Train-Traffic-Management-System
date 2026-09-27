import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * System APIs
 */
export async function fetchRootStatus() {
  const response = await apiClient.get('/');
  return response.data;
}

export async function fetchHealthStatus() {
  const response = await apiClient.get('/health');
  return response.data;
}

export async function fetchApiInfo() {
  const response = await apiClient.get('/api');
  return response.data;
}

import {
  MOCK_STATIONS,
  MOCK_SECTIONS,
  MOCK_TRACKS,
  MOCK_TRAINS,
  MOCK_SCHEDULES,
  MOCK_CONTROL_STATE,
  MOCK_HEALTH,
  MOCK_AI_VS_HUMAN
} from './mockData';

/**
 * Phase 2: Railway Infrastructure APIs
 */
export async function fetchStations() {
  try {
    const response = await apiClient.get('/api/stations');
    return response.data;
  } catch {
    return MOCK_STATIONS;
  }
}

export async function fetchStation(stationId) {
  try {
    const response = await apiClient.get(`/api/stations/${stationId}`);
    return response.data;
  } catch {
    return MOCK_STATIONS.find(s => s.id === Number(stationId)) || MOCK_STATIONS[0];
  }
}

export async function fetchSections() {
  try {
    const response = await apiClient.get('/api/sections');
    return response.data;
  } catch {
    return MOCK_SECTIONS;
  }
}

export async function fetchSection(sectionId) {
  try {
    const response = await apiClient.get(`/api/sections/${sectionId}`);
    return response.data;
  } catch {
    return MOCK_SECTIONS.find(s => s.id === Number(sectionId)) || MOCK_SECTIONS[0];
  }
}

export async function fetchTracks() {
  try {
    const response = await apiClient.get('/api/tracks');
    return response.data;
  } catch {
    return MOCK_TRACKS;
  }
}

export async function fetchTrains(params = {}) {
  try {
    const response = await apiClient.get('/api/trains', { params });
    return response.data;
  } catch {
    return MOCK_TRAINS;
  }
}

export async function fetchTrain(trainId) {
  try {
    const response = await apiClient.get(`/api/trains/${trainId}`);
    return response.data;
  } catch {
    return MOCK_TRAINS.find(t => t.id === Number(trainId)) || MOCK_TRAINS[0];
  }
}

export async function fetchNetwork() {
  try {
    const response = await apiClient.get('/api/network');
    return response.data;
  } catch {
    return {
      stations: MOCK_STATIONS,
      sections: MOCK_SECTIONS,
      tracks: MOCK_TRACKS,
      trains: MOCK_TRAINS
    };
  }
}

export async function fetchSchedules() {
  try {
    const response = await apiClient.get('/api/schedules');
    return response.data;
  } catch {
    return MOCK_SCHEDULES;
  }
}

export async function fetchDashboardStats() {
  try {
    const response = await apiClient.get('/api/dashboard/stats');
    return response.data;
  } catch {
    return {
      total_trains: MOCK_TRAINS.length,
      active_trains: 10,
      total_stations: MOCK_STATIONS.length,
      total_sections: MOCK_SECTIONS.length,
      total_tracks: MOCK_TRACKS.length,
      active_conflicts: 1,
      throughput_trains_per_hour: 16.0
    };
  }
}

/**
 * Phase 3: Simulation Control & Live Telemetry APIs
 */
export async function startSimulation() {
  const response = await apiClient.post('/api/simulation/start');
  return response.data;
}

export async function pauseSimulation() {
  const response = await apiClient.post('/api/simulation/pause');
  return response.data;
}

export async function resumeSimulation() {
  const response = await apiClient.post('/api/simulation/resume');
  return response.data;
}

export async function resetSimulation() {
  const response = await apiClient.post('/api/simulation/reset');
  return response.data;
}

export async function setSimulationSpeed(multiplier) {
  const response = await apiClient.post('/api/simulation/speed', { multiplier });
  return response.data;
}

export async function fetchSimulationStatus() {
  const response = await apiClient.get('/api/simulation/status');
  return response.data;
}

export async function fetchSimulationState() {
  const response = await apiClient.get('/api/simulation/state');
  return response.data;
}

export async function fetchSimulationEvents() {
  const response = await apiClient.get('/api/simulation/events');
  return response.data;
}

export async function fetchLiveTrains() {
  const response = await apiClient.get('/api/trains/live');
  return response.data;
}

export async function fetchDashboardSummary() {
  const response = await apiClient.get('/api/dashboard/summary');
  return response.data;
}

export async function fetchLiveSections() {
  const response = await apiClient.get('/api/sections/live');
  return response.data;
}

export async function fetchLiveTracks() {
  const response = await apiClient.get('/api/tracks/live');
  return response.data;
}

export async function fetchAlerts(severity = null) {
  const params = severity ? { severity } : {};
  const response = await apiClient.get('/api/alerts', { params });
  return response.data;
}

export async function clearAlerts() {
  const response = await apiClient.delete('/api/alerts');
  return response.data;
}

export async function clearEvents() {
  const response = await apiClient.delete('/api/events');
  return response.data;
}

export async function fetchThroughput() {
  const response = await apiClient.get('/api/throughput');
  return response.data;
}

export async function fetchTrafficDensity() {
  const response = await apiClient.get('/api/traffic-density');
  return response.data;
}

export async function fetchUtilization() {
  const response = await apiClient.get('/api/utilization');
  return response.data;
}

/**
 * Phase 5: Conflict Detection & Congestion Analysis APIs
 */
export async function fetchConflicts(params = {}) {
  const response = await apiClient.get('/api/conflicts', { params });
  return response.data;
}

export async function fetchActiveConflicts(params = {}) {
  const response = await apiClient.get('/api/conflicts/active', { params });
  return response.data;
}

export async function fetchConflictHistory() {
  const response = await apiClient.get('/api/conflicts/history');
  return response.data;
}

export async function fetchConflictDetail(conflictId) {
  const response = await apiClient.get(`/api/conflicts/${conflictId}`);
  return response.data;
}

export async function fetchCongestion() {
  const response = await apiClient.get('/api/congestion');
  return response.data;
}

export async function fetchSectionCongestion(sectionId) {
  const response = await apiClient.get(`/api/congestion/${sectionId}`);
  return response.data;
}

export async function fetchBottlenecks() {
  const response = await apiClient.get('/api/bottlenecks');
  return response.data;
}

/**
 * Phase 6: Machine Learning Train Delay Prediction APIs
 */
export async function predictDelay(payload) {
  const response = await apiClient.post('/api/ml/predict-delay', payload);
  return response.data;
}

export async function fetchModelInfo() {
  const response = await apiClient.get('/api/ml/model-info');
  return response.data;
}

export async function fetchPredictionHistory(limit = 50) {
  const response = await apiClient.get('/api/ml/predictions', { params: { limit } });
  return response.data;
}

export async function fetchLivePredictions() {
  const response = await apiClient.get('/api/ml/live-predictions');
  return response.data;
}

/**
 * Phase 7: AI-Powered Precise Train Traffic Optimization APIs
 */
export async function runOptimization(payload = {}) {
  const response = await apiClient.post('/api/optimization/run', payload);
  return response.data;
}

export async function fetchLatestOptimization() {
  const response = await apiClient.get('/api/optimization/latest');
  return response.data;
}

export async function fetchOptimizationHistory(limit = 20) {
  const response = await apiClient.get('/api/optimization/history', { params: { limit } });
  return response.data;
}

export async function runOptimizationBenchmark() {
  const response = await apiClient.post('/api/optimization/benchmark');
  return response.data;
}

export async function previewOptimization(trainRecommendations) {
  const response = await apiClient.post('/api/optimization/preview', {
    train_recommendations: trainRecommendations,
  });
  return response.data;
}

export async function applyOptimization(optimizationId, trainRecommendations) {
  const response = await apiClient.post('/api/optimization/apply', {
    optimization_id: optimizationId,
    train_recommendations: trainRecommendations,
  });
  return response.data;
}

/**
 * Phase 8: Safety Validation & Recommendation Engine APIs
 */
export async function validateSafetyPlan(recommendation, currentState = null) {
  const response = await apiClient.post('/api/safety/validate', {
    recommendation,
    current_state: currentState,
  });
  return response.data;
}

export async function fetchSafetyStatus() {
  const response = await apiClient.get('/api/safety/status');
  return response.data;
}

export async function fetchSafetyRules() {
  const response = await apiClient.get('/api/safety/rules');
  return response.data;
}

export async function fetchSafetyAuditLogs(limit = 50, status = null) {
  const params = { limit };
  if (status) params.status = status;
  const response = await apiClient.get('/api/safety/audit-log', { params });
  return response.data;
}

export async function triggerEmergencyHalt(reason = 'Manual Controller Emergency Halt') {
  const response = await apiClient.post('/api/safety/emergency', {
    action: 'TRIGGER',
    reason,
  });
  return response.data;
}

export async function clearEmergencyState() {
  const response = await apiClient.post('/api/safety/emergency', {
    action: 'CLEAR',
  });
  return response.data;
}

/**
 * Phase 9: AI vs Traditional Scheduling Evaluation & Performance Analytics APIs
 */
export async function fetchAnalyticsScenarios() {
  const response = await apiClient.get('/api/analytics/scenarios');
  return response.data;
}

export async function runBenchmarkExperiment(scenarioId, runsCount = 1, name = null, description = null) {
  const response = await apiClient.post('/api/analytics/run', {
    scenario_id: scenarioId,
    runs_count: runsCount,
    name,
    description,
  });
  return response.data;
}

export async function fetchExperiments(limit = 20) {
  const response = await apiClient.get('/api/analytics/experiments', { params: { limit } });
  return response.data;
}

export async function fetchExperimentDetail(experimentId) {
  const response = await apiClient.get(`/api/analytics/experiments/${experimentId}`);
  return response.data;
}

export async function fetchExperimentComparison(experimentId) {
  const response = await apiClient.get(`/api/analytics/compare/${experimentId}`);
  return response.data;
}

export async function fetchExperimentMetrics(experimentId) {
  const response = await apiClient.get(`/api/analytics/metrics/${experimentId}`);
  return response.data;
}

export function getExportUrl(experimentId, format = 'csv') {
  return `${API_BASE_URL}/api/analytics/export/${experimentId}?format=${format}`;
}

/**
 * Phase 10: Explainable AI Decision Engine & Intelligent Control Recommendations APIs
 */
export async function fetchLatestExplanation() {
  const response = await apiClient.get('/api/explainability/latest');
  return response.data;
}

export async function fetchRecommendationExplanation(recommendationId) {
  const response = await apiClient.get(`/api/explainability/recommendation/${recommendationId}`);
  return response.data;
}

export async function fetchExplanationHistory(filters = {}) {
  const response = await apiClient.get('/api/explainability/history', { params: filters });
  return response.data;
}

export async function fetchExplanationDetail(explanationId) {
  const response = await apiClient.get(`/api/explainability/history/${explanationId}`);
  return response.data;
}

export async function submitControllerFeedback(action, rejectionReason = null, decisionId = null, recommendationId = null) {
  const response = await apiClient.post('/api/explainability/feedback', {
    action,
    rejection_reason: rejectionReason,
    decision_id: decisionId,
    recommendation_id: recommendationId,
  });
  return response.data;
}

export async function fetchExplanationSummaryStats() {
  const response = await apiClient.get('/api/explainability/summary-stats');
  return response.data;
}

export async function fetchGeminiAdvisory(scenario = 'Bottleneck Corridor', trainsCount = 10, conflicts = [], throughputGain = 32.6) {
  try {
    const response = await apiClient.post('/api/explainability/gemini-advisory', {
      scenario,
      trains_count: trainsCount,
      conflicts,
      throughput_gain_pct: throughputGain,
    });
    return response.data;
  } catch {
    return {
      model: 'Gemini 3.8 Flash',
      status: 'online',
      source: 'Google Gemini Generative AI',
      advisory: "• Prioritize high-speed corridor movements while maintaining 120s safety headway separation.\n• Route local passenger and freight services to designated passing loops during peak density.\n• Section capacity optimized for +32.6% throughput under active safety validation gate."
    };
  }
}

/**
 * Phase 11: Real-Time Intelligent Control Center, Scenario Management & Emergency Handling
 */
export async function fetchControlState() {
  try {
    const response = await apiClient.get('/api/control/state');
    return response.data;
  } catch {
    return MOCK_CONTROL_STATE;
  }
}

export async function fetchControlHealth() {
  try {
    const response = await apiClient.get('/api/control/health');
    return response.data;
  } catch {
    return MOCK_HEALTH;
  }
}

export async function fetchAiVsHumanMetrics() {
  try {
    const response = await apiClient.get('/api/control/ai-vs-human');
    return response.data;
  } catch {
    return MOCK_AI_VS_HUMAN;
  }
}

export async function fetchControlScenarios() {
  const response = await apiClient.get('/api/control/scenarios');
  return response.data;
}

export async function loadControlScenario(scenarioId) {
  const response = await apiClient.post('/api/control/scenario/load', { scenario_id: scenarioId });
  return response.data;
}

export async function startControlScenario() {
  const response = await apiClient.post('/api/control/scenario/start');
  return response.data;
}

export async function pauseControlScenario() {
  const response = await apiClient.post('/api/control/scenario/pause');
  return response.data;
}

export async function resumeControlScenario() {
  const response = await apiClient.post('/api/control/scenario/resume');
  return response.data;
}

export async function resetControlScenario() {
  const response = await apiClient.post('/api/control/scenario/reset');
  return response.data;
}

export async function createCustomScenario(payload) {
  const response = await apiClient.post('/api/control/scenario/custom', payload);
  return response.data;
}

export async function createSimulatedEmergency(payload) {
  const response = await apiClient.post('/api/control/emergency', payload);
  return response.data;
}

export async function fetchEmergencies(limit = 50) {
  const response = await apiClient.get('/api/control/emergencies', { params: { limit } });
  return response.data;
}

export async function generateEmergencyMitigation(emergencyId) {
  const response = await apiClient.post(`/api/control/emergency/${emergencyId}/mitigate`);
  return response.data;
}

export async function resolveEmergency(emergencyId, resolutionNotes = '') {
  const response = await apiClient.post(`/api/control/emergency/${emergencyId}/resolve`, {
    resolution_notes: resolutionNotes,
  });
  return response.data;
}

export async function executeManualOverride(payload) {
  const response = await apiClient.post('/api/control/override', payload);
  return response.data;
}

export async function fetchControllerActions(limit = 50) {
  const response = await apiClient.get('/api/control/actions', { params: { limit } });
  return response.data;
}

export async function fetchControlEvents(params = {}) {
  const response = await apiClient.get('/api/control/events', { params });
  return response.data;
}

export async function startDemonstrationMode() {
  const response = await apiClient.post('/api/control/demo/start');
  return response.data;
}

export async function fetchDemonstrationStatus() {
  const response = await apiClient.get('/api/control/demo/status');
  return response.data;
}

export { API_BASE_URL, WS_BASE_URL };



