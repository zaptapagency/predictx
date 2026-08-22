import React, { useState, useEffect } from 'react';
import '../styles/leaderboard.css';

interface LeaderboardData {
  period: string;
  leaderboard: LeaderboardUser[];
  current_user_position: number;
}

interface LeaderboardUser {
  rank: number;
  medal: string;
  user_name: string;
  score: number;
  rank_change: string;
  customers_saved: number;
  expansions_closed: number;
  actions_taken: number;
  revenue_generated: string;
  action_streak: number;
  is_current_user: boolean;
  is_top_performer: boolean;
  achievements: Achievement[];
}

interface Achievement {
  name: string;
  icon: string;
  rarity: string;
}

interface PersonalStats {
  user: { name: string; role: string };
  stats: any;
  engagement: any;
  achievements: { total: number; recent: any[] };
  recent_activity: any[];
}

interface ActivityFeed {
  activity: Activity[];
}

interface Activity {
  id: number;
  user: string;
  activity: string;
  description: string;
  icon: string;
  revenue_impact: string;
  reactions: number;
  when: string;
  is_celebratory: boolean;
}

export default function Leaderboard() {
  const [period, setPeriod] = useState('week');
  const [leaderboard, setLeaderboard] = useState<LeaderboardData | null>(null);
  const [personalStats, setPersonalStats] = useState<PersonalStats | null>(null);
  const [activityFeed, setActivityFeed] = useState<ActivityFeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('rankings');

  useEffect(() => {
    fetchLeaderboardData();
  }, [period]);

  async function fetchLeaderboardData() {
    setLoading(true);
    try {
      const [leaderboardRes, statsRes, activityRes] = await Promise.all([
        fetch(`/api/leaderboard/rankings?period=${period}`),
        fetch('/api/leaderboard/my-stats'),
        fetch('/api/leaderboard/activity-feed')
      ]);

      const leaderboardData = await leaderboardRes.json();
      const statsData = await statsRes.json();
      const activityData = await activityRes.json();

      setLeaderboard(leaderboardData);
      setPersonalStats(statsData);
      setActivityFeed(activityData);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="leaderboard"><div className="loading">Loading leaderboard...</div></div>;
  if (!leaderboard) return <div className="leaderboard"><div className="error">Failed to load leaderboard</div></div>;

  return (
    <div className="leaderboard">
      {/* HEADER */}
      <div className="leaderboard-header">
        <h1>🏆 Team Leaderboard</h1>
        <p>Competition drives excellence. See who's crushing it this week.</p>
      </div>

      {/* TABS */}
      <div className="leaderboard-tabs">
        <button
          className={`tab-btn ${activeTab === 'rankings' ? 'active' : ''}`}
          onClick={() => setActiveTab('rankings')}
        >
          🏆 Rankings
        </button>
        <button
          className={`tab-btn ${activeTab === 'you' ? 'active' : ''}`}
          onClick={() => setActiveTab('you')}
        >
          👤 Your Stats
        </button>
        <button
          className={`tab-btn ${activeTab === 'activity' ? 'active' : ''}`}
          onClick={() => setActiveTab('activity')}
        >
          📰 Activity Feed
        </button>
      </div>

      {/* PERIOD SELECTOR */}
      {activeTab === 'rankings' && (
        <div className="period-selector">
          {['day', 'week', 'month', 'all_time'].map((p) => (
            <button
              key={p}
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {p === 'day' && '📅 Today'}
              {p === 'week' && '📊 This Week'}
              {p === 'month' && '📈 This Month'}
              {p === 'all_time' && '⭐ All Time'}
            </button>
          ))}
        </div>
      )}

      {/* TAB CONTENT */}
      <div className="leaderboard-content">
        {/* RANKINGS TAB */}
        {activeTab === 'rankings' && (
          <div className="rankings-section">
            <div className="rankings-table">
              {leaderboard.leaderboard.map((user) => (
                <div
                  key={user.rank}
                  className={`ranking-row ${user.is_current_user ? 'current-user' : ''} ${
                    user.is_top_performer ? 'top-performer' : ''
                  }`}
                >
                  {/* MEDAL & RANK */}
                  <div className="rank-cell">
                    <span className="medal">{user.medal}</span>
                    {user.rank_change !== '→' && (
                      <span className={`trend ${user.rank_change.includes('↑') ? 'up' : 'down'}`}>
                        {user.rank_change}
                      </span>
                    )}
                  </div>

                  {/* USER INFO */}
                  <div className="user-cell">
                    <div className="user-name">
                      {user.user_name}
                      {user.is_current_user && <span className="you-badge">you</span>}
                    </div>
                    {user.achievements.length > 0 && (
                      <div className="achievements-small">
                        {user.achievements.slice(0, 3).map((achievement, idx) => (
                          <span key={idx} className="achievement-icon" title={achievement.name}>
                            {achievement.icon}
                          </span>
                        ))}
                        {user.achievements.length > 3 && (
                          <span className="more-achievements">+{user.achievements.length - 3}</span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* STATS */}
                  <div className="stat-cell">
                    <div className="stat-item">
                      <span className="stat-label">Saved</span>
                      <span className="stat-value">{user.customers_saved}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Expanded</span>
                      <span className="stat-value">{user.expansions_closed}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Actions</span>
                      <span className="stat-value">{user.actions_taken}</span>
                    </div>
                  </div>

                  {/* REVENUE & STREAK */}
                  <div className="right-cell">
                    <div className="revenue">{user.revenue_generated}</div>
                    {user.action_streak > 0 && (
                      <div className="streak">
                        🔥 {user.action_streak}d streak
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* YOUR STATS TAB */}
        {activeTab === 'you' && personalStats && (
          <div className="stats-section">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="icon">⚡</div>
                <div className="stat-content">
                  <div className="label">Actions Taken</div>
                  <div className="value">{personalStats.stats.total_actions}</div>
                  <div className="subtext">This month: {personalStats.stats.this_month_actions}</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="icon">🛡️</div>
                <div className="stat-content">
                  <div className="label">Customers Saved</div>
                  <div className="value">{personalStats.stats.customers_saved}</div>
                  <div className="subtext">From churn</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="icon">📈</div>
                <div className="stat-content">
                  <div className="label">Expansions Closed</div>
                  <div className="value">{personalStats.stats.expansions_closed}</div>
                  <div className="subtext">Revenue growth</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="icon">🔥</div>
                <div className="stat-content">
                  <div className="label">Current Streak</div>
                  <div className="value">{personalStats.engagement.current_streak}</div>
                  <div className="subtext">Best: {personalStats.engagement.longest_streak} days</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="icon">🎯</div>
                <div className="stat-content">
                  <div className="label">Accuracy</div>
                  <div className="value">{personalStats.stats.prediction_accuracy}</div>
                  <div className="subtext">Prediction accuracy</div>
                </div>
              </div>

              <div className="stat-card">
                <div className="icon">💰</div>
                <div className="stat-content">
                  <div className="label">Total Impact</div>
                  <div className="value">{personalStats.stats.total_revenue}</div>
                  <div className="subtext">Revenue generated</div>
                </div>
              </div>
            </div>

            {/* ACHIEVEMENTS */}
            <div className="achievements-section">
              <h3>🏅 Your Badges</h3>
              <div className="achievements-grid">
                {personalStats.achievements.recent.map((achievement, idx) => (
                  <div key={idx} className="achievement-badge" title={achievement.name}>
                    <div className="achievement-icon">{achievement.icon}</div>
                    <div className="achievement-name">{achievement.name}</div>
                    <div className={`achievement-rarity ${achievement.rarity}`}>
                      {achievement.rarity}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ACTIVITY FEED TAB */}
        {activeTab === 'activity' && activityFeed && (
          <div className="activity-section">
            <h3>📰 What's Happening</h3>
            <div className="activity-feed">
              {activityFeed.activity.map((activity) => (
                <div
                  key={activity.id}
                  className={`activity-card ${activity.is_celebratory ? 'celebratory' : ''}`}
                >
                  <div className="activity-icon">{activity.icon}</div>
                  <div className="activity-content">
                    <div className="activity-title">{activity.user}</div>
                    <div className="activity-text">{activity.activity}</div>
                    {activity.description && (
                      <div className="activity-description">{activity.description}</div>
                    )}
                    <div className="activity-footer">
                      {activity.revenue_impact && (
                        <span className="revenue-badge">{activity.revenue_impact}</span>
                      )}
                      <span className="time">
                        {new Date(activity.when).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {activity.reactions > 0 && (
                    <div className="reactions">{activity.reactions} 👏</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="leaderboard-cta">
        <h2>🚀 Ready to climb the ranks?</h2>
        <p>Take more actions, save more customers, and earn badges.</p>
        <a href="/dashboard/actions" className="cta-button">
          View Action Center →
        </a>
      </div>
    </div>
  );
}
