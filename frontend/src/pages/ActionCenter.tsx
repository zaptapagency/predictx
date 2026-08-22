import React, { useState, useEffect } from 'react';
import '../styles/action-center.css';

interface Action {
  id: number;
  title: string;
  description: string;
  action_type: string;
  priority: string;
  status: string;
  entity_type: string;
  entity_name: string;
  entity_email: string;
  estimated_impact: number;
  impact_type: string;
  due_at: string;
}

interface QuickAction {
  id: number;
  name: string;
  description: string;
  icon: string;
  impact_estimate: number;
  times_used: number;
  success_rate: number;
}

interface DashboardData {
  actions_by_priority: {
    critical: Action[];
    high: Action[];
    medium: Action[];
    low: Action[];
  };
  stats: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    total_estimated_impact: number;
    impact_unit: string;
  };
  quick_actions: QuickAction[];
}

export default function ActionCenter() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPriority, setSelectedPriority] = useState('critical');
  const [executingIds, setExecutingIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function fetchDashboard() {
    setLoading(true);
    try {
      const response = await fetch('/api/actions/dashboard');
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error('Error fetching actions:', error);
    } finally {
      setLoading(false);
    }
  }

  async function executeAction(actionId: number) {
    setExecutingIds(prev => new Set(prev).add(actionId));
    try {
      const response = await fetch('/api/actions/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_id: actionId,
          execution_type: 'immediate'
        })
      });

      const data = await response.json();
      if (data.success) {
        alert('✅ Action executed!');
        fetchDashboard();
      }
    } catch (error) {
      console.error('Error executing action:', error);
      alert('❌ Failed to execute action');
    } finally {
      setExecutingIds(prev => {
        const next = new Set(prev);
        next.delete(actionId);
        return next;
      });
    }
  }

  async function executeBulkAction(actionIds: number[]) {
    if (!confirm(`Execute ${actionIds.length} actions?`)) return;

    try {
      const response = await fetch('/api/actions/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_ids: actionIds,
          execution_type: 'bulk'
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(`✅ Executed ${data.executed.length} actions!`);
        fetchDashboard();
      }
    } catch (error) {
      console.error('Error executing bulk action:', error);
    }
  }

  async function executeQuickAction(quickActionId: number) {
    if (!confirm('Execute this quick action?')) return;

    try {
      const response = await fetch('/api/actions/quick-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quick_action_id: quickActionId
        })
      });

      const data = await response.json();
      if (data.success) {
        alert(`✅ Executed ${data.actions_executed} actions!`);
        fetchDashboard();
      }
    } catch (error) {
      console.error('Error executing quick action:', error);
    }
  }

  if (loading) return <div className="action-center"><div className="loading">Loading action center...</div></div>;
  if (!dashboard) return <div className="action-center"><div className="error">Failed to load actions</div></div>;

  const priorityLevels = ['critical', 'high', 'medium', 'low'];
  const priorityInfo = {
    critical: { icon: '🔴', label: 'Critical', color: 'critical' },
    high: { icon: '🟠', label: 'High', color: 'high' },
    medium: { icon: '🟡', label: 'Medium', color: 'medium' },
    low: { icon: '🟢', label: 'Low', color: 'low' }
  };

  const currentActions = dashboard.actions_by_priority[selectedPriority as keyof typeof dashboard.actions_by_priority];

  return (
    <div className="action-center">
      {/* HEADER */}
      <div className="action-center-header">
        <h1>🎯 Action Center</h1>
        <p>Take action on predictions and drive results</p>
      </div>

      {/* KEY METRICS */}
      <div className="action-metrics">
        <div className="metric">
          <div className="metric-icon">📋</div>
          <div className="metric-content">
            <div className="metric-label">Total Actions</div>
            <div className="metric-value">{dashboard.stats.total}</div>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">⏱️</div>
          <div className="metric-content">
            <div className="metric-label">Pending</div>
            <div className="metric-value">{dashboard.stats.critical + dashboard.stats.high + dashboard.stats.medium + dashboard.stats.low}</div>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">💰</div>
          <div className="metric-content">
            <div className="metric-label">Estimated Impact</div>
            <div className="metric-value">
              ${(dashboard.stats.total_estimated_impact / 1000).toFixed(0)}K
            </div>
          </div>
        </div>

        <div className="metric">
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <div className="metric-label">By Priority</div>
            <div className="metric-breakdown">
              {dashboard.stats.critical} 🔴 {dashboard.stats.high} 🟠 {dashboard.stats.medium} 🟡 {dashboard.stats.low} 🟢
            </div>
          </div>
        </div>
      </div>

      {/* QUICK ACTIONS */}
      {dashboard.quick_actions.length > 0 && (
        <div className="quick-actions-section">
          <h2>⚡ Quick Actions (30 seconds)</h2>
          <div className="quick-actions-grid">
            {dashboard.quick_actions.map((qa) => (
              <button
                key={qa.id}
                className="quick-action-btn"
                onClick={() => executeQuickAction(qa.id)}
                title={qa.description}
              >
                <div className="qa-icon">{qa.icon}</div>
                <div className="qa-name">{qa.name}</div>
                <div className="qa-impact">${(qa.impact_estimate / 1000).toFixed(0)}K</div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="action-layout">
        {/* PRIORITY TABS */}
        <div className="priority-tabs">
          {priorityLevels.map((priority) => {
            const info = priorityInfo[priority as keyof typeof priorityInfo];
            const count = dashboard.stats[priority as keyof typeof dashboard.stats];
            return (
              <button
                key={priority}
                className={`priority-tab ${priority} ${selectedPriority === priority ? 'active' : ''}`}
                onClick={() => setSelectedPriority(priority)}
              >
                <span className="icon">{info.icon}</span>
                <span className="label">{info.label}</span>
                <span className="count">{count}</span>
              </button>
            );
          })}
        </div>

        {/* ACTIONS LIST */}
        <div className="actions-list">
          {currentActions.length === 0 ? (
            <div className="empty-state">
              <p>✅ No {selectedPriority} priority actions</p>
              <p className="subtext">Great job staying on top of things!</p>
            </div>
          ) : (
            <>
              <div className="actions-header">
                <h3>{currentActions.length} {selectedPriority.toUpperCase()} Priority Actions</h3>
                <button
                  className="bulk-action-btn"
                  onClick={() => executeBulkAction(currentActions.map(a => a.id))}
                >
                  Execute All ({currentActions.length})
                </button>
              </div>

              <div className="actions-cards">
                {currentActions.map((action) => (
                  <div key={action.id} className={`action-card ${action.priority.toLowerCase()}`}>
                    {/* ACTION TYPE BADGE */}
                    <div className="action-type-badge">
                      {action.action_type === 'email' && '📧'}
                      {action.action_type === 'slack' && '💬'}
                      {action.action_type === 'task' && '✅'}
                      {action.action_type === 'meeting' && '📞'}
                      {action.action_type === 'salesforce' && '☁️'}
                      {action.action_type === 'webhook' && '🔗'}
                      {action.action_type === 'custom' && '⚙️'}
                      <span className="type-label">{action.action_type.toUpperCase()}</span>
                    </div>

                    {/* TITLE */}
                    <h4 className="action-title">{action.title}</h4>

                    {/* DESCRIPTION */}
                    <p className="action-description">{action.description}</p>

                    {/* ENTITY INFO */}
                    <div className="entity-info">
                      <div className="entity-name">{action.entity_name}</div>
                      {action.entity_email && (
                        <div className="entity-email">{action.entity_email}</div>
                      )}
                    </div>

                    {/* IMPACT */}
                    <div className="action-impact">
                      <span className="icon">💰</span>
                      <span className="value">
                        ${(action.estimated_impact / 1000).toFixed(0)}K {action.impact_type}
                      </span>
                    </div>

                    {/* METADATA */}
                    <div className="action-meta">
                      <span className="entity-type">
                        {action.entity_type === 'customer' && '👤'}
                        {action.entity_type === 'lead' && '🎯'}
                        {action.entity_type === 'employee' && '👥'}
                        {action.entity_type} • {action.entity_type}
                      </span>
                      {action.due_at && (
                        <span className="due-date">
                          Due: {new Date(action.due_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* ACTION BUTTONS */}
                    <div className="action-buttons">
                      <button
                        className="action-btn primary"
                        onClick={() => executeAction(action.id)}
                        disabled={executingIds.has(action.id)}
                      >
                        {executingIds.has(action.id) ? '⏳ Executing...' : '→ Execute Now'}
                      </button>
                      <button className="action-btn secondary">
                        🔗 Open
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* CTA SECTION */}
      {dashboard.stats.total > 0 && (
        <div className="action-cta">
          <h3>🚀 Ready to take action?</h3>
          <p>
            You have <strong>${(dashboard.stats.total_estimated_impact / 1000).toFixed(0)}K</strong> in
            estimated impact waiting to be captured across <strong>{dashboard.stats.total}</strong> actions.
          </p>
          <p className="subtext">Start with Critical priority items → High → Medium → Low</p>
        </div>
      )}
    </div>
  );
}
