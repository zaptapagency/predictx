import React, { useState, useEffect } from 'react';
import '../styles/activity-feed-page.css';

interface Activity {
  id: number;
  user: string;
  title: string;
  description: string;
  type: string;
  entity_name: string;
  revenue_impact: string;
  customers_affected: number;
  reactions: number;
  is_celebratory: boolean;
  created_at: string;
}

export default function ActivityFeedPage() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [celebrations, setCelebrations] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [userReactions, setUserReactions] = useState<Record<number, string>>({});

  useEffect(() => {
    fetchActivities();
  }, [activeTab]);

  async function fetchActivities() {
    setLoading(true);
    try {
      const [allRes, celebRes] = await Promise.all([
        fetch('/api/activity-feed/team?limit=30'),
        fetch('/api/activity-feed/celebratory/feed?limit=10')
      ]);

      const allData = await allRes.json();
      const celebData = await celebRes.json();

      setActivities(allData.activities || []);
      setCelebrations(celebData.celebrations || []);
    } catch (error) {
      console.error('Error fetching activities:', error);
    } finally {
      setLoading(false);
    }
  }

  async function reactToActivity(activityId: number, emoji: string) {
    try {
      const response = await fetch(
        `/api/activity-feed/${activityId}/react?emoji=${emoji}`,
        { method: 'POST' }
      );
      const data = await response.json();

      setUserReactions({
        ...userReactions,
        [activityId]: emoji
      });

      // Refresh activities
      fetchActivities();
    } catch (error) {
      console.error('Error reacting to activity:', error);
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) return <div className="activity-feed-page"><div className="loading">Loading activity feed...</div></div>;

  return (
    <div className="activity-feed-page">
      {/* HEADER */}
      <div className="activity-header">
        <h1>📰 Team Activity Feed</h1>
        <p>Celebrate wins, stay connected, build momentum</p>
      </div>

      {/* TABS */}
      <div className="activity-tabs">
        <button
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          📋 All Activity
        </button>
        <button
          className={`tab-btn ${activeTab === 'celebrations' ? 'active' : ''}`}
          onClick={() => setActiveTab('celebrations')}
        >
          🎉 Celebrations
        </button>
      </div>

      {/* ALL ACTIVITY */}
      {activeTab === 'all' && (
        <div className="activity-section">
          <div className="activity-list">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className={`activity-item ${activity.is_celebratory ? 'celebratory' : ''}`}
              >
                <div className="activity-left">
                  <div className="user-avatar">{activity.user.charAt(0)}</div>
                </div>

                <div className="activity-middle">
                  <div className="activity-user">{activity.user}</div>
                  <div className="activity-title">{activity.title}</div>
                  {activity.description && (
                    <div className="activity-description">{activity.description}</div>
                  )}

                  <div className="activity-meta">
                    {activity.entity_name && (
                      <span className="meta-item">
                        📌 {activity.entity_name}
                      </span>
                    )}
                    {activity.revenue_impact && (
                      <span className="meta-item revenue">
                        💰 {activity.revenue_impact}
                      </span>
                    )}
                    {activity.customers_affected && (
                      <span className="meta-item">
                        👥 {activity.customers_affected} customers
                      </span>
                    )}
                    <span className="meta-item time">
                      {formatTime(activity.created_at)}
                    </span>
                  </div>
                </div>

                <div className="activity-right">
                  <div className="reactions">
                    {['👏', '❤️', '🔥', '🚀'].map((emoji) => (
                      <button
                        key={emoji}
                        className={`reaction-btn ${
                          userReactions[activity.id] === emoji ? 'active' : ''
                        }`}
                        onClick={() => reactToActivity(activity.id, emoji)}
                        title={emoji}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                  <div className="reaction-count">
                    {activity.reactions > 0 && (
                      <span>{activity.reactions} 👏</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CELEBRATIONS */}
      {activeTab === 'celebrations' && (
        <div className="celebrations-section">
          <div className="celebration-grid">
            {celebrations.map((activity) => (
              <div key={activity.id} className="celebration-card">
                <div className="celebration-badge">🎉</div>
                <div className="celebration-user">{activity.user}</div>
                <div className="celebration-title">{activity.title}</div>
                {activity.revenue_impact && (
                  <div className="celebration-impact">
                    <span className="impact-label">Impact</span>
                    <span className="impact-value">{activity.revenue_impact}</span>
                  </div>
                )}
                <div className="celebration-time">
                  {formatTime(activity.created_at)}
                </div>
                <div className="celebration-reactions">
                  {['👏', '❤️', '🔥'].map((emoji) => (
                    <button
                      key={emoji}
                      className="reaction-btn"
                      onClick={() => reactToActivity(activity.id, emoji)}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="activity-cta">
        <h2>💪 Keep the momentum going</h2>
        <p>Take action to create more wins for the team</p>
        <a href="/dashboard/actions" className="cta-button">
          Take Action →
        </a>
      </div>
    </div>
  );
}
