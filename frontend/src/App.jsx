import React, { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import SimulationControls from './components/SimulationControls';
import Dashboard from './pages/Dashboard';
import Trains from './pages/Trains';
import RailwayNetwork from './pages/RailwayNetwork';
import TrafficControl from './pages/TrafficControl';
import ConflictMonitoring from './pages/ConflictMonitoring';
import AIOptimization from './pages/AIOptimization';
import Analytics from './pages/Analytics';
import ExplainableAI from './pages/ExplainableAI';
import ControlCenter from './pages/ControlCenter';
import SystemStatus from './pages/SystemStatus';
import { useBackendStatus } from './hooks/useBackendStatus';
import { useSimulation } from './hooks/useSimulation';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('control_center');
  const { status, healthData, error, latency, refetch } = useBackendStatus(5000);
  const simulation = useSimulation();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'control_center':
        return <ControlCenter simulation={simulation} onNavigate={(tab) => setActiveTab(tab)} />;
      case 'dashboard':
        return (
          <Dashboard
            backendStatus={status}
            healthData={healthData}
            error={error}
            latency={latency}
            simulation={simulation}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        );
      case 'trains':
        return <Trains simulation={simulation} />;
      case 'network':
        return <RailwayNetwork simulation={simulation} />;
      case 'control':
        return <TrafficControl simulation={simulation} />;
      case 'conflicts':
        return <ConflictMonitoring simulation={simulation} />;
      case 'optimization':
        return <AIOptimization simulation={simulation} />;
      case 'analytics':
        return <Analytics />;
      case 'explainability':
        return <ExplainableAI simulation={simulation} />;
      case 'status':
        return <SystemStatus />;
      default:
        return (
          <Dashboard
            backendStatus={status}
            healthData={healthData}
            error={error}
            latency={latency}
            simulation={simulation}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        );
    }
  };

  return (
    <div className="app-container">
      <Header
        backendStatus={status}
        latency={latency}
        error={error}
        onRefresh={refetch}
      />
      <div className="app-body">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="app-main">
          <SimulationControls simulation={simulation} />
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
}


