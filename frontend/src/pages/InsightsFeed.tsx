import React, { useState, useEffect } from 'react';
import '../styles/insights-feed.css';

interface Insight {
  id: number;
  title: string;
  description: string;
  icon: string;
  recommended_action: string;
  estimated_impact: string;
  confidence: string;
  is_urgent: boolean;
  is_read: boolean;
  related_entity: string;
}

interface DailyDigest {
  digest_date: string;
  insight_count: number;
  urgent_count: number;
  insights: Insight[];
  message: string;
}

export default function InsightsFeed() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [digest, setDigest] = useState<DailyDigest | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('today');

  useEffect(() => {
    fetchInsights();
  }, [activeTab]);

  async function fetchInsights() {
    setLoading(true);
    try {
      const [feedRes, digestRes] = await Promise.all([
        fetch('/api/insights/feed?limit=10'),
        fetch('/api/insights/daily-digest')
      ]);

      const feedData = await feedRes.json();
      const digestData = await digestRes.json();

      setInsights(feedData.insights || []);
      setDigest(digestData);
      setUnreadCount(feedData.unread_count || 0);
    } catch (error) {
      console.error('Error fetching insights:', error);
    } finally {
      setLoading(false);
    }
  }

  async function markAsRead(insightId: number) {
    try {
      await fetch(`/api/insights/mark-read/${insightId}`, { method: 'POST' });
      setInsights(insights.map(i => i.id === insightId ? { ...i, is_read: true } : i));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  }

  async function dismissInsight(insightId: number) {
    try {
      await fetch(`/api/insights/dismiss/${insightId}`, { method: 'POST' });
      setInsights(insights.filter(i => i.id !== insightId));
    } catch (error) {
      console.error('Error dismissing insight:', error);
    }
  }

  if (loading) return <div className="insights-feed"><div className="loading">Loading insights...</div></div>;

  return (
    <div className="insights-feed">
      {/* HEADER */}
      <div className="insights-header">
        <h1>💡 Daily Insights</h1>
        <p>Personalized recommendations to maximize your impact</p>
        {unreadCount > 0 && <span className="unread-badge">{unreadCount} new</span>}
      </div>

      {/* TABS */}
      <div className="insights-tabs">
        <button
          className={`tab-btn ${activeTab === 'today' ? 'active' : ''}`}
          onClick={() => setActiveTab('today')}
        >
          📅 Today's Digest
        </button>
        <button
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          📋 All Insights
        </button>
      </div>

      {/* TODAY'S DIGEST */}
      {activeTab === 'today' && digest && (
        <div className="digest-section">
          <div className="digest-banner">
            <div className="digest-icon">📊</div>
            <div className="digest-content">
              <h2>Today's Summary</h2>
              <p>{digest.message}</p>
              <div className="digest-stats">
                <div className="stat">
                  <span className="label">Total Insights</span>
                  <span className="value">{digest.insight_count}</span>
                </div>
                <div className="stat urgent">
                  <span className="label">🔴 Urgent</span>
                  <span className="value">{digest.urgent_count}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="insights-grid">
            {digest.insights.map((insight) => (
              <div
                key={insight.id}
                className={`insight-card ${insight.is_urgent ? 'urgent' : ''} ${insight.is_read ? 'read' : 'unread'}`}
              >
                <div className="insight-header">
                  <span className="icon">{insight.icon}</span>
                  {insight.is_urgent && <span className="urgent-badge">🔴 URGENT</span>}
                </div>
                <h3>{insight.title}</h3>
                <p className="description">{insight.description}</p>
                {insight.recommended_action && (
                  <div className="action">
                    <strong>Action:</strong> {insight.recommended_action}
                  </div>
                )}
                <div className="footer">
                  <span className="impact">{insight.estimated_impact}</span>
                  <span className="confidence">{insight.confidence}</span>
                </div>
                <div className="card-actions">
                  <button
                    className="btn-read"
                    onClick={() => markAsRead(insight.id)}
                    disabled={insight.is_read}
                  >
                    {insight.is_read ? '✓ Read' : 'Mark Read'}
                  </button>
                  <button
                    className="btn-dismiss"
                    onClick={() => dismissInsight(insight.id)}
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ALL INSIGHTS */}
      {activeTab === 'all' && (
        <div className="all-insights-section">
          <div className="insights-list">
            {insights.map((insight) => (
              <div
                key={insight.id}
                className={`insight-row ${insight.is_urgent ? 'urgent' : ''} ${insight.is_read ? 'read' : ''}`}
              >
                <div className="row-icon">
                  <span className="icon">{insight.icon}</span>
                </div>

                <div className="row-content">
                  <div className="row-title">
                    {insight.title}
                    {insight.is_urgent && <span className="urgent-indicator">🔴</span>}
                  </div>
                  <div className="row-description">{insight.description}</div>
                  <div className="row-action">{insight.recommended_action}</div>
                </div>

                <div className="row-metrics">
                  <div className="metric">
                    <span className="label">Impact</span>
                    <span className="value">{insight.estimated_impact}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Confidence</span>
                    <span className="value">{insight.confidence}</span>
                  </div>
                </div>

                <div className="row-actions">
                  <button
                    className="action-btn"
                    onClick={() => markAsRead(insight.id)}
                    title="Mark as read"
                  >
                    {insight.is_read ? '✓' : '○'}
                  </button>
                  <button
                    className="action-btn dismiss"
                    onClick={() => dismissInsight(insight.id)}
                    title="Dismiss"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="insights-cta">
        <h2>🚀 Act on these insights</h2>
        <p>Each insight represents an opportunity to save customers or create revenue</p>
        <a href="/dashboard/actions" className="cta-button">
          Go to Action Center →
        </a>
      </div>
    </div>
  );
}
