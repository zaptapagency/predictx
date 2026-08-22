import React, { useState, useEffect } from 'react';
import '../styles/adoption-tracker.css';

interface TeamSummary {
  team_size: number;
  active_users: number;
  adoption_rate: string;
  dau: number;
  wau: number;
  mau: number;
  avg_actions_per_user: string;
  total_actions: number;
  playbooks_deployed: number;
  avg_playbooks_per_user: string;
  health: string;
}

interface UserAdoption {
  user_id: number;
  churn_risk: string;
  stage: string;
  days_active: number;
  last_active: string;
  recommended_action: string;
}

export default function AdoptionTracker() {
  const [summary, setSummary] = useState<TeamSummary | null>(null);
  const [myAdoption, setMyAdoption] = useState<any>(null);
  const [atRiskUsers, setAtRiskUsers] = useState<UserAdoption[]>([]);
  const [powerUsers, setPowerUsers] = useState<UserAdoption[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAdoptionData();
  }, []);

  async function fetchAdoptionData() {
    setLoading(true);
    try {
      const [summaryRes, myRes, atRiskRes, powerRes] = await Promise.all([
        fetch('/api/adoption/team-summary'),
        fetch('/api/adoption/my-adoption'),
        fetch('/api/adoption/at-risk-users'),
        fetch('/api/adoption/power-users')
      ]);

      const summaryData = await summaryRes.json();
      const myData = await myRes.json();
      const atRiskData = await atRiskRes.json();
      const powerData = await powerRes.json();

      setSummary(summaryData);
      setMyAdoption(myData);
      setAtRiskUsers(atRiskData.users || []);
      setPowerUsers(powerData.users || []);
    } catch (error) {
      console.error('Error fetching adoption data:', error);
    } finally {
      setLoading(false);
    }
  }

  const getStageEmoji = (stage: string): string => {
    const emojis: Record<string, string> = {
      onboarded: '👋',
      activated: '🎉',
      habit_forming: '💪',
      power_user: '⭐',
      churned: '😞'
    };
    return emojis[stage] || '❓';
  };

  const getStageColor = (stage: string): string => {
    const colors: Record<string, string> = {
      onboarded: '#60a5fa',
      activated: '#f97316',
      habit_forming: '#fbbf24',
      power_user: '#10b981',
      churned: '#ef4444'
    };
    return colors[stage] || '#94a3b8';
  };

  if (loading) return <div className="adoption-tracker"><div className="loading">Analyzing team adoption...</div></div>;

  return (
    <div className="adoption-tracker">
      {/* HEADER */}
      <div className="adoption-header">
        <h1>📊 Adoption Tracker</h1>
        <p>Monitor team adoption and identify at-risk users</p>
      </div>

      {/* TABS */}
      <div className="adoption-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📈 Team Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'you' ? 'active' : ''}`}
          onClick={() => setActiveTab('you')}
        >
          👤 Your Progress
        </button>
        <button
          className={`tab-btn ${activeTab === 'atrisk' ? 'active' : ''}`}
          onClick={() => setActiveTab('atrisk')}
        >
          ⚠️ At-Risk Users
        </button>
        <button
          className={`tab-btn ${activeTab === 'stars' ? 'active' : ''}`}
          onClick={() => setActiveTab('stars')}
        >
          ⭐ Power Users
        </button>
      </div>

      {/* TEAM OVERVIEW */}
      {activeTab === 'overview' && summary && (
        <div className="overview-section">
          <div className="health-banner" style={{ borderLeft: `4px solid ${summary.health === 'excellent' ? '#10b981' : summary.health === 'good' ? '#fbbf24' : '#ef4444'}` }}>
            <h2>Team Health: {summary.health.toUpperCase()}</h2>
            <p>Adoption Rate: {summary.adoption_rate}</p>
          </div>

          <div className="metrics-grid">
            <div className="metric-card">
              <div className="icon">👥</div>
              <div className="content">
                <div className="label">Team Size</div>
                <div className="value">{summary.team_size}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">⚡</div>
              <div className="content">
                <div className="label">Active Users</div>
                <div className="value">{summary.active_users}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">📊</div>
              <div className="content">
                <div className="label">Daily Active</div>
                <div className="value">{summary.dau}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">📈</div>
              <div className="content">
                <div className="label">Weekly Active</div>
                <div className="value">{summary.wau}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">📋</div>
              <div className="content">
                <div className="label">Monthly Active</div>
                <div className="value">{summary.mau}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">🚀</div>
              <div className="content">
                <div className="label">Avg Actions/User</div>
                <div className="value">{summary.avg_actions_per_user}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">⚙️</div>
              <div className="content">
                <div className="label">Total Actions</div>
                <div className="value">{summary.total_actions}</div>
              </div>
            </div>

            <div className="metric-card">
              <div className="icon">📚</div>
              <div className="content">
                <div className="label">Playbooks Deployed</div>
                <div className="value">{summary.playbooks_deployed}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* YOUR PROGRESS */}
      {activeTab === 'you' && myAdoption && (
        <div className="personal-section">
          <div className="progress-card">
            <div className="stage-indicator" style={{ backgroundColor: getStageColor(myAdoption.stage) }}>
              {getStageEmoji(myAdoption.stage)}
            </div>
            <div className="progress-content">
              <h2>Your Current Stage</h2>
              <div className="stage-name">{myAdoption.stage.replace('_', ' ').toUpperCase()}</div>
              <div className="engagement">
                Engagement Score: <strong>{myAdoption.engagement_score}</strong>
              </div>
              <div className="churn-risk">
                Churn Risk: <strong>{myAdoption.churn_risk}</strong>
              </div>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat">
              <div className="label">Days Active</div>
              <div className="value">{myAdoption.days_active}</div>
            </div>
            <div className="stat">
              <div className="label">Total Actions</div>
              <div className="value">{myAdoption.total_actions}</div>
            </div>
            <div className="stat">
              <div className="label">Total Predictions</div>
              <div className="value">{myAdoption.total_predictions}</div>
            </div>
            <div className="stat">
              <div className="label">Playbooks Deployed</div>
              <div className="value">{myAdoption.playbooks_deployed}</div>
            </div>
            <div className="stat">
              <div className="label">Features Used</div>
              <div className="value">{myAdoption.features_used}</div>
            </div>
            <div className="stat">
              <div className="label">Last Active</div>
              <div className="value">
                {myAdoption.last_active_at
                  ? new Date(myAdoption.last_active_at).toLocaleDateString()
                  : 'Never'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AT-RISK USERS */}
      {activeTab === 'atrisk' && (
        <div className="atrisk-section">
          <div className="section-header">
            <h2>⚠️ Users at Risk of Churning</h2>
            <p>{atRiskUsers.length} users need attention</p>
          </div>

          <div className="users-list">
            {atRiskUsers.map((user) => (
              <div key={user.user_id} className="user-item at-risk">
                <div className="user-info">
                  <div className="user-stage" style={{ backgroundColor: getStageColor(user.stage) }}>
                    {getStageEmoji(user.stage)}
                  </div>
                  <div className="user-details">
                    <div className="user-id">User #{user.user_id}</div>
                    <div className="user-stage-name">{user.stage}</div>
                    <div className="user-activity">
                      Days Active: {user.days_active} • Last: {user.last_active}
                    </div>
                  </div>
                </div>

                <div className="user-metrics">
                  <div className="risk-badge">
                    🔴 {user.churn_risk} Risk
                  </div>
                  <div className="recommendation">
                    {user.recommended_action}
                  </div>
                </div>

                <button className="btn-action">📧 Send Email</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* POWER USERS */}
      {activeTab === 'stars' && (
        <div className="stars-section">
          <div className="section-header">
            <h2>⭐ Power Users (Adoption Champions)</h2>
            <p>{powerUsers.length} users are crushing it</p>
          </div>

          <div className="users-grid">
            {powerUsers.map((user) => (
              <div key={user.user_id} className="user-card power-user">
                <div className="user-badge">⭐</div>
                <div className="user-id">User #{user.user_id}</div>
                <div className="user-label">Adoption Champion</div>
                <p className="recommendation">{user.recommended_action}</p>
                <button className="btn-action">👋 Connect</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="adoption-cta">
        <h2>🎯 Drive adoption forward</h2>
        <p>Help at-risk users succeed and celebrate power users</p>
        <a href="/dashboard/actions" className="cta-button">
          Take Action →
        </a>
      </div>
    </div>
  );
}
