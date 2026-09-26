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

const NAV_GROUPS = [
  {
    category: 'Operations',
    items: [
      { id: 'control_center', label: 'Control Center', icon: Activity, badge: 'Live Room' },
      { id: 'control', label: 'Traffic Control', icon: Sliders, badge: 'Phase 4' },
      { id: 'conflicts', label: 'Conflicts & Congestion', icon: AlertTriangle, badge: 'Hazards' },
    ],
  },
  {
    category: 'AI & Intelligence',
    items: [
      { id: 'optimization', label: 'AI Optimization', icon: Cpu, badge: 'Phase 8' },
      { id: 'explainability', label: 'Explainable AI', icon: HelpCircle, badge: 'XAI' },
      { id: 'analytics', label: 'Performance Analytics', icon: BarChart3, badge: '+32.6%' },
    ],
  },
  {
    category: 'Infrastructure & Fleet',
    items: [
      { id: 'network', label: 'Railway Network', icon: Network, badge: 'Topology' },
      { id: 'trains', label: 'Train Fleet', icon: Train, badge: 'Fleet' },
    ],
  },
  {
    category: 'System Diagnostics',
    items: [
      { id: 'status', label: 'System Health', icon: ShieldCheck, badge: '9/9 OK' },
      { id: 'dashboard', label: 'Overview Board', icon: LayoutDashboard },
    ],
  },
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="app-sidebar">
      <nav className="sidebar-nav">
        {NAV_GROUPS.map((group) => (
          <div key={group.category} className="sidebar-group">
            <div className="sidebar-group-title">{group.category}</div>
            <div className="sidebar-group-items">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`nav-btn ${isActive ? 'nav-btn-active' : ''}`}
                  >
                    <Icon size={17} className="nav-icon" />
                    <span className="nav-label">{item.label}</span>
                    {item.badge && (
                      <span className={`nav-pill ${isActive ? 'nav-pill-active' : ''}`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="system-spec">
          <div className="spec-indicator-ring"></div>
          <div>
            <div className="spec-title">Simulation Engine</div>
            <div className="spec-desc">FastAPI • ML • React 18</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

