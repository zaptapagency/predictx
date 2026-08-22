import React, { useState, useEffect } from 'react';
import '../styles/creator-dashboard.css';

interface CreatorPlaybook {
  id: number;
  name: string;
  slug: string;
  status: string;
  downloads: number;
  active_users: number;
  avg_rating: number;
  review_count: number;
  total_revenue: number;
  price_monthly: number;
  published_at: string;
}

interface CreatorDashboardData {
  playbooks: CreatorPlaybook[];
  earnings_this_month: {
    total_revenue: number;
    creator_share: number;
    forecastx_share: number;
    active_subscriptions: number;
  };
  all_time_stats: {
    total_earnings: number;
    total_purchases: number;
    total_active_users: number;
    avg_rating: number;
  };
}

interface EarningsEntry {
  month: string;
  total_revenue: number;
  creator_share: number;
  forecastx_share: number;
  active_subscriptions: number;
  churn_rate: string;
  payout_status: string;
  payout_date: string;
}

export default function CreatorDashboard() {
  const [dashboard, setDashboard] = useState<CreatorDashboardData | null>(null);
  const [earnings, setEarnings] = useState<EarningsEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlaybook, setSelectedPlaybook] = useState<CreatorPlaybook | null>(null);

  useEffect(() => {
    fetchDashboard();
    fetchEarnings();
  }, []);

  async function fetchDashboard() {
    try {
      const response = await fetch('/api/marketplace/creator/dashboard');
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchEarnings() {
    try {
      const response = await fetch('/api/marketplace/creator/earnings');
      const data = await response.json();
      setEarnings(data.earnings);
    } catch (error) {
      console.error('Error fetching earnings:', error);
    }
  }

  if (loading) return <div className="creator-dashboard"><div className="loading">Loading dashboard...</div></div>;
  if (!dashboard) return <div className="creator-dashboard"><div className="error">Failed to load dashboard</div></div>;

  const thisMonth = dashboard.earnings_this_month;
  const allTime = dashboard.all_time_stats;

  return (
    <div className="creator-dashboard">
      <div className="creator-header">
        <h1>👑 Creator Dashboard</h1>
        <p>Manage your playbooks and track earnings</p>
      </div>

      {/* KEY METRICS */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">💰</div>
          <div className="metric-content">
            <div className="metric-label">This Month's Earnings</div>
            <div className="metric-value">${thisMonth.creator_share.toLocaleString()}</div>
            <div className="metric-detail">70% of ${thisMonth.total_revenue.toLocaleString()} revenue</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <div className="metric-label">All-Time Revenue</div>
            <div className="metric-value">${allTime.total_earnings.toLocaleString()}</div>
            <div className="metric-detail">{allTime.total_purchases.toLocaleString()} purchases</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">👥</div>
          <div className="metric-content">
            <div className="metric-label">Active Subscriptions</div>
            <div className="metric-value">{thisMonth.active_subscriptions.toLocaleString()}</div>
            <div className="metric-detail">{allTime.total_active_users.toLocaleString()} total users</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⭐</div>
          <div className="metric-content">
            <div className="metric-label">Average Rating</div>
            <div className="metric-value">{allTime.avg_rating.toFixed(1)}</div>
            <div className="metric-detail">Across all playbooks</div>
          </div>
        </div>
      </div>

      <div className="dashboard-layout">
        {/* PLAYBOOKS LIST */}
        <div className="playbooks-section">
          <div className="section-header">
            <h2>📋 Your Playbooks</h2>
            <a href="/create-playbook" className="create-btn">+ Create New</a>
          </div>

          {dashboard.playbooks.length === 0 ? (
            <div className="empty-state">
              <p>You haven't created any playbooks yet</p>
              <a href="/create-playbook" className="empty-state-btn">Create Your First Playbook</a>
            </div>
          ) : (
            <div className="playbooks-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Downloads</th>
                  <th>Rating</th>
                  <th>Revenue</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.playbooks.map((pb) => (
                  <tr
                    key={pb.id}
                    className={selectedPlaybook?.id === pb.id ? 'selected' : ''}
                    onClick={() => setSelectedPlaybook(pb)}
                  >
                    <td className="playbook-name">
                      <div className="name">{pb.name}</div>
                      <div className="slug">/{pb.slug}</div>
                    </td>
                    <td>
                      <span className={`status-badge ${pb.status}`}>
                        {pb.status === 'published' ? '✅' : '⏳'} {pb.status}
                      </span>
                    </td>
                    <td className="numeric">{pb.downloads.toLocaleString()}</td>
                    <td className="rating">
                      ⭐ {pb.avg_rating.toFixed(1)} ({pb.review_count})
                    </td>
                    <td className="numeric">${pb.total_revenue.toLocaleString()}</td>
                    <td className="actions">
                      <button className="action-btn">📊 View</button>
                      <button className="action-btn">✏️ Edit</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </div>
          )}
        </div>

        {/* PLAYBOOK DETAIL */}
        {selectedPlaybook && (
          <div className="playbook-detail-panel">
            <h3>{selectedPlaybook.name}</h3>
            <div className="detail-stats">
              <div className="detail-stat">
                <div className="label">Downloads</div>
                <div className="value">{selectedPlaybook.downloads}</div>
              </div>
              <div className="detail-stat">
                <div className="label">Active Users</div>
                <div className="value">{selectedPlaybook.active_users}</div>
              </div>
              <div className="detail-stat">
                <div className="label">Monthly Price</div>
                <div className="value">${selectedPlaybook.price_monthly}</div>
              </div>
              <div className="detail-stat">
                <div className="label">Total Revenue</div>
                <div className="value">${selectedPlaybook.total_revenue.toLocaleString()}</div>
              </div>
            </div>

            <div className="detail-actions">
              <button className="detail-btn primary">📊 View Analytics</button>
              <button className="detail-btn">✏️ Edit Playbook</button>
              <button className="detail-btn">👥 View Reviews</button>
              <button className="detail-btn">🔗 Share Link</button>
            </div>
          </div>
        )}
      </div>

      {/* EARNINGS HISTORY */}
      <div className="earnings-section">
        <h2>💰 Earnings History</h2>
        <div className="earnings-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Revenue</th>
              <th>Your Share (70%)</th>
              <th>Subscriptions</th>
              <th>Churn Rate</th>
              <th>Payout Status</th>
            </tr>
          </thead>
          <tbody>
            {earnings.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty">No earnings yet</td>
              </tr>
            ) : (
              earnings.map((entry, idx) => (
                <tr key={idx}>
                  <td className="month">{entry.month}</td>
                  <td className="numeric">${entry.total_revenue.toLocaleString()}</td>
                  <td className="numeric earnings">${entry.creator_share.toLocaleString()}</td>
                  <td className="numeric">{entry.active_subscriptions}</td>
                  <td className="numeric">{entry.churn_rate}</td>
                  <td>
                    <span className={`payout-badge ${entry.payout_status}`}>
                      {entry.payout_status === 'paid' ? '✅' : '⏳'} {entry.payout_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </div>
      </div>

      {/* INFO SECTION */}
      <div className="info-section">
        <div className="info-card">
          <h3>💡 How to Increase Earnings</h3>
          <ul>
            <li>📈 Optimize your playbook for proven results (higher success rate = more customers)</li>
            <li>⭐ Maintain high ratings (encourage customers to leave reviews)</li>
            <li>📢 Share your playbook on social media and communities</li>
            <li>🎯 Target specific use cases and industries for better discoverability</li>
            <li>🔄 Keep playbook updated based on customer feedback</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>🎯 Revenue Model</h3>
          <ul>
            <li>✅ You receive 70% of all subscription revenue</li>
            <li>✅ ForecastX handles payment processing and support</li>
            <li>✅ Payouts processed monthly via Stripe</li>
            <li>✅ No minimum revenue threshold</li>
            <li>✅ Lifetime earnings from each customer</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>🚀 Growth Tips</h3>
          <ul>
            <li>🎓 Create playbooks for underserved use cases</li>
            <li>🏆 Aim for 80%+ success rate (customers will buy)</li>
            <li>📊 Publish case studies showing ROI achieved</li>
            <li>🤝 Engage with reviewers and customers</li>
            <li>💼 Build multiple playbooks to diversify income</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
