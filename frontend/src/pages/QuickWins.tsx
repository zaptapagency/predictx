import React, { useState, useEffect } from 'react';
import '../styles/quick-wins.css';

interface QuickWin {
  id: number;
  title: string;
  description: string;
  icon: string;
  action_type: string;
  estimated_target_count: number;
  estimated_impact: string;
  success_probability: string;
}

interface Execution {
  quick_win: string;
  target_count: number;
  success_count: number;
  success_rate: string;
  actual_impact: string;
  status: string;
  executed_at: string;
}

export default function QuickWins() {
  const [quickWins, setQuickWins] = useState<QuickWin[]>([]);
  const [history, setHistory] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState('available');

  useEffect(() => {
    fetchQuickWins();
  }, []);

  async function fetchQuickWins() {
    setLoading(true);
    try {
      const [winRes, histRes] = await Promise.all([
        fetch('/api/quick-wins/available'),
        fetch('/api/quick-wins/history')
      ]);

      const winData = await winRes.json();
      const histData = await histRes.json();

      setQuickWins(winData.quick_wins || []);
      setHistory(histData.history || []);
    } catch (error) {
      console.error('Error fetching quick wins:', error);
    } finally {
      setLoading(false);
    }
  }

  async function executeQuickWin(winId: number, title: string) {
    setExecutingId(winId);
    try {
      const response = await fetch(`/api/quick-wins/${winId}/execute`, { method: 'POST' });
      const data = await response.json();

      // Show success message
      alert(`✓ ${title} executed!\nAffecting ${data.message.split(' ').slice(-1)[0]} targets`);

      // Refresh
      fetchQuickWins();
    } catch (error) {
      console.error('Error executing quick win:', error);
      alert('Error executing quick win');
    } finally {
      setExecutingId(null);
    }
  }

  if (loading) return <div className="quick-wins"><div className="loading">Loading quick wins...</div></div>;

  return (
    <div className="quick-wins">
      {/* HEADER */}
      <div className="quick-wins-header">
        <h1>⚡ Quick Wins</h1>
        <p>One-click actions to maximize impact instantly</p>
      </div>

      {/* TABS */}
      <div className="quick-wins-tabs">
        <button
          className={`tab-btn ${activeTab === 'available' ? 'active' : ''}`}
          onClick={() => setActiveTab('available')}
        >
          ⚡ Available Actions
        </button>
        <button
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📋 Execution History
        </button>
      </div>

      {/* AVAILABLE QUICK WINS */}
      {activeTab === 'available' && (
        <div className="quick-wins-grid">
          {quickWins.map((win) => (
            <div key={win.id} className="quick-win-card">
              {/* ICON */}
              <div className="win-icon">{win.icon}</div>

              {/* CONTENT */}
              <div className="win-content">
                <h3>{win.title}</h3>
                <p className="description">{win.description}</p>

                <div className="win-details">
                  <div className="detail">
                    <span className="label">Targets</span>
                    <span className="value">{win.estimated_target_count}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Impact</span>
                    <span className="value">{win.estimated_impact}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Success Rate</span>
                    <span className="value">{win.success_probability}</span>
                  </div>
                </div>

                <div className="action-type">
                  <span className="tag">{win.action_type}</span>
                </div>
              </div>

              {/* BUTTON */}
              <button
                className="btn-execute-win"
                onClick={() => executeQuickWin(win.id, win.title)}
                disabled={executingId === win.id}
              >
                {executingId === win.id ? '⏳ Executing...' : '🚀 Execute Now'}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* EXECUTION HISTORY */}
      {activeTab === 'history' && (
        <div className="history-section">
          <div className="history-stats">
            <div className="stat">
              <div className="label">Total Executions</div>
              <div className="value">{history.length}</div>
            </div>
            <div className="stat">
              <div className="label">Total Impact</div>
              <div className="value">
                {history.reduce((sum, h) => {
                  const amount = h.actual_impact?.replace(/[^0-9]/g, '') || '0';
                  return sum + parseInt(amount);
                }, 0).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="history-list">
            {history.map((execution, idx) => (
              <div key={idx} className="history-item">
                <div className="item-left">
                  <div className="quick-win-name">{execution.quick_win}</div>
                  <div className="item-details">
                    <span className="detail">Targets: {execution.target_count}</span>
                    <span className="detail">Success: {execution.success_count}</span>
                    <span className="detail">Rate: {execution.success_rate}</span>
                  </div>
                </div>

                <div className="item-right">
                  <div className="impact">{execution.actual_impact}</div>
                  <div className={`status ${execution.status}`}>
                    {execution.status === 'completed' && '✓ Completed'}
                    {execution.status === 'pending' && '⏳ Pending'}
                    {execution.status === 'failed' && '✕ Failed'}
                  </div>
                  <div className="time">
                    {new Date(execution.executed_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="quick-wins-cta">
        <h2>💪 Compound your impact</h2>
        <p>Quick wins are your secret to consistent growth</p>
        <a href="/dashboard/leaderboard" className="cta-button">
          View Leaderboard →
        </a>
      </div>
    </div>
  );
}
