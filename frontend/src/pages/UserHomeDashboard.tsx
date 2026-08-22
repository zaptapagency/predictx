import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/user-home-dashboard.css';

interface UserHome {
  user_name: string;
  this_month_impact: string;
  revenue_saved: string;
  revenue_created: string;
  rank: number;
  rank_change: string;
  current_streak: number;
  badges_earned: number;
  next_badge: {
    name: string;
    icon: string;
    progress: number;
    target: number;
  };
  top_actions: Array<{
    id: number;
    title: string;
    icon: string;
    impact: string;
    priority: string;
  }>;
  forecast_next_month: string;
  forecast_confidence: string;
  recent_wins: Array<{
    title: string;
    impact: string;
    when: string;
  }>;
  recommended_playbooks: Array<{
    id: number;
    name: string;
    roi: string;
    reason: string;
  }>;
}

export default function UserHomeDashboard() {
  const [data, setData] = useState<UserHome | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserHome();
  }, []);

  async function fetchUserHome() {
    setLoading(true);
    try {
      const response = await fetch('/api/user/home');
      const homeData = await response.json();
      setData(homeData);
    } catch (error) {
      console.error('Error fetching user home:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="user-home"><div className="loading">Loading your dashboard...</div></div>;
  }

  if (!data) {
    return <div className="user-home"><div className="error">Failed to load dashboard</div></div>;
  }

  return (
    <div className="user-home">
      {/* HERO SECTION */}
      <div className="hero-section">
        <div className="hero-greeting">
          <h1>Welcome back, {data.user_name}! 👋</h1>
          <p>Here's your impact this month</p>
        </div>

        <div className="hero-metrics">
          <div className="metric hero-metric">
            <div className="icon">💰</div>
            <div className="content">
              <div className="label">THIS MONTH'S IMPACT</div>
              <div className="value">{data.this_month_impact}</div>
              <div className="breakdown">
                🛡️ Saved: {data.revenue_saved} • 📈 Created: {data.revenue_created}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* STATUS SECTION */}
      <div className="status-section">
        <h2>Your Status</h2>
        <div className="status-grid">
          <div className="status-card rank">
            <div className="status-icon">🏆</div>
            <div className="status-content">
              <div className="status-label">LEADERBOARD RANK</div>
              <div className="status-value">#{data.rank}</div>
              <div className="status-trend">
                {data.rank_change.includes('↑') ? '↑ Moving up' : data.rank_change.includes('↓') ? '↓ Moving down' : '→ Steady'}
              </div>
            </div>
          </div>

          <div className="status-card streak">
            <div className="status-icon">🔥</div>
            <div className="status-content">
              <div className="status-label">ACTION STREAK</div>
              <div className="status-value">{data.current_streak}d</div>
              <div className="status-trend">Keep it going!</div>
            </div>
          </div>

          <div className="status-card badges">
            <div className="status-icon">🏅</div>
            <div className="status-content">
              <div className="status-label">BADGES EARNED</div>
              <div className="status-value">{data.badges_earned}</div>
              <div className="status-trend">Collect them all!</div>
            </div>
          </div>

          <div className="status-card progress">
            <div className="status-icon">{data.next_badge.icon}</div>
            <div className="status-content">
              <div className="status-label">NEXT: {data.next_badge.name.toUpperCase()}</div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{width: `${(data.next_badge.progress / data.next_badge.target) * 100}%`}}
                />
              </div>
              <div className="status-trend">{data.next_badge.progress}/{data.next_badge.target}</div>
            </div>
          </div>
        </div>
      </div>

      {/* FOCUS TODAY SECTION */}
      <div className="focus-section">
        <div className="focus-header">
          <h2>🎯 Focus Today</h2>
          <p>Top 3 actions that will move the needle</p>
        </div>

        <div className="actions-list">
          {data.top_actions.map((action, idx) => (
            <div key={action.id} className={`action-item priority-${action.priority.toLowerCase()}`}>
              <div className="action-rank">{idx + 1}</div>
              <div className="action-icon">{action.icon}</div>
              <div className="action-content">
                <div className="action-title">{action.title}</div>
                <div className="action-impact">Impact: {action.impact}</div>
              </div>
              <div className="action-priority">
                {action.priority === 'CRITICAL' && <span className="badge critical">🔴 CRITICAL</span>}
                {action.priority === 'HIGH' && <span className="badge high">🟠 HIGH</span>}
                {action.priority === 'MEDIUM' && <span className="badge medium">🟡 MEDIUM</span>}
              </div>
              <Link to="/dashboard/actions" className="btn-action">
                Take Action →
              </Link>
            </div>
          ))}
        </div>

        <Link to="/dashboard/actions" className="btn-primary full-width">
          View All Actions
        </Link>
      </div>

      {/* RECENT WINS SECTION */}
      <div className="wins-section">
        <h2>🎉 Recent Wins</h2>
        <div className="wins-list">
          {data.recent_wins.map((win, idx) => (
            <div key={idx} className="win-item">
              <div className="win-emoji">✨</div>
              <div className="win-content">
                <div className="win-title">{win.title}</div>
                <div className="win-details">
                  <span className="win-impact">{win.impact}</span>
                  <span className="win-time">{win.when}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* FORECAST SECTION */}
      <div className="forecast-section">
        <div className="forecast-card">
          <div className="forecast-icon">🔮</div>
          <div className="forecast-content">
            <h3>Next Month's Forecast</h3>
            <div className="forecast-value">{data.forecast_next_month}</div>
            <div className="forecast-confidence">Confidence: {data.forecast_confidence}</div>
            <p className="forecast-text">Based on your current pace and growth trajectory</p>
          </div>
        </div>
      </div>

      {/* RECOMMENDED PLAYBOOKS SECTION */}
      <div className="playbooks-section">
        <h2>📚 Recommended for You</h2>
        <p className="section-subtitle">These playbooks will ROI fastest based on your use case</p>

        <div className="playbooks-grid">
          {data.recommended_playbooks.map((pb) => (
            <div key={pb.id} className="playbook-card">
              <div className="playbook-roi">{pb.roi}</div>
              <h3>{pb.name}</h3>
              <p className="playbook-reason">{pb.reason}</p>
              <Link to="/marketplace" className="btn-secondary">
                Deploy Now
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* QUICK NAV SECTION */}
      <div className="quick-nav-section">
        <h2>Quick Access</h2>
        <div className="quick-nav-grid">
          <Link to="/dashboard/roi" className="nav-card">
            <div className="nav-icon">💹</div>
            <div className="nav-title">ROI Tracker</div>
            <div className="nav-desc">View detailed impact</div>
          </Link>

          <Link to="/dashboard/leaderboard" className="nav-card">
            <div className="nav-icon">🏆</div>
            <div className="nav-title">Leaderboard</div>
            <div className="nav-desc">Compare with team</div>
          </Link>

          <Link to="/dashboard/copilot" className="nav-card">
            <div className="nav-icon">🤖</div>
            <div className="nav-title">AI Copilot</div>
            <div className="nav-desc">Smart recommendations</div>
          </Link>

          <Link to="/dashboard/quick-wins" className="nav-card">
            <div className="nav-icon">⚡</div>
            <div className="nav-title">Quick Wins</div>
            <div className="nav-desc">1-click actions</div>
          </Link>

          <Link to="/dashboard/heatmap" className="nav-card">
            <div className="nav-icon">🔥</div>
            <div className="nav-title">Health Map</div>
            <div className="nav-desc">Customer urgency</div>
          </Link>

          <Link to="/dashboard/insights" className="nav-card">
            <div className="nav-icon">💡</div>
            <div className="nav-title">Insights</div>
            <div className="nav-desc">Daily reminders</div>
          </Link>
        </div>
      </div>

      {/* MOTIVATION SECTION */}
      <div className="motivation-section">
        <div className="motivation-card">
          <h2>🚀 You're Crushing It!</h2>
          <p>
            You've earned {data.badges_earned} badges this month and maintained a {data.current_streak}-day streak.
            Keep this momentum going and you could reach #1 by end of month!
          </p>
          <div className="motivation-actions">
            <Link to="/dashboard/actions" className="btn-primary">
              Take Next Action
            </Link>
            <Link to="/dashboard/leaderboard" className="btn-secondary">
              See Leaderboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
