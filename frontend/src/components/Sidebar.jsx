import React from 'react';
import {
  Activity,
  LayoutDashboard,
  Train,
  Network,
  Sliders,
  AlertTriangle,
  Cpu,
  BarChart3,
  HelpCircle,
  Info,
  ShieldCheck,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'control_center', label: 'Control Center', icon: Activity, badge: 'Phase 11' },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'network', label: 'Railway Network', icon: Network, badge: 'Live' },
  { id: 'trains', label: 'Train Fleet', icon: Train, badge: 'Live' },
  { id: 'control', label: 'Traffic Control', icon: Sliders, badge: 'Phase 4' },
  { id: 'conflicts', label: 'Conflicts & Congestion', icon: AlertTriangle, badge: 'Phase 5' },
  { id: 'optimization', label: 'AI Optimization', icon: Cpu, badge: 'Phase 8' },
  { id: 'analytics', label: 'Performance Analytics', icon: BarChart3, badge: 'Phase 9' },
  { id: 'explainability', label: 'Explainable AI', icon: HelpCircle, badge: 'Phase 10' },
  { id: 'status', label: 'System Status', icon: ShieldCheck, badge: 'Phase 13' },
];


export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="app-sidebar">
      <div className="sidebar-section-title">Navigation</div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`nav-btn ${isActive ? 'nav-btn-active' : ''}`}
            >
              <Icon size={18} className="nav-icon" />
              <span className="nav-label">{item.label}</span>
              {item.badge && (
                <span className={`nav-pill ${isActive ? 'nav-pill-active' : ''}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-spec">
          <Info size={14} />
          <div>
            <div className="spec-title">Prototype Engine</div>
            <div className="spec-desc">FastAPI + SQLite + React</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

