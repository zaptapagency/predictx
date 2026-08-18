import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/admin.css';

interface SubscriptionStats {
  total_subscriptions: number;
  free_tier: number;
  pro_tier: number;
  enterprise_tier: number;
  active_subscriptions: number;
  canceled_subscriptions: number;
  monthly_recurring_revenue: number;
}

const AdminSubscriptions: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SubscriptionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchStats();
  }, [navigate]);

  const fetchStats = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch('/api/admin/subscriptions', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setStats(await response.json());
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="admin-subscriptions loading">Loading...</div>;
  }

  if (!stats) {
    return <div className="admin-subscriptions error">Failed to load subscription data</div>;
  }

  const conversionFree = ((stats.pro_tier + stats.enterprise_tier) / stats.total_subscriptions * 100).toFixed(1);
  const activeRate = (stats.active_subscriptions / stats.total_subscriptions * 100).toFixed(1);
  const churnRate = (stats.canceled_subscriptions / stats.total_subscriptions * 100).toFixed(1);

  return (
    <div className="admin-subscriptions">
      <div className="admin-header">
        <h1>Subscription Analytics</h1>
        <p>Complete subscription and revenue overview</p>
      </div>

      {/* Key Metrics */}
      <section className="metrics-grid">
        <div className="metric-card">
          <h3>Total Subscriptions</h3>
          <div className="metric-value">{stats.total_subscriptions}</div>
        </div>

        <div className="metric-card">
          <h3>Monthly Recurring Revenue</h3>
          <div className="metric-value">${stats.monthly_recurring_revenue.toFixed(2)}</div>
        </div>

        <div className="metric-card">
          <h3>Active Rate</h3>
          <div className="metric-value">{activeRate}%</div>
        </div>

        <div className="metric-card">
          <h3>Churn Rate</h3>
          <div className="metric-value">{churnRate}%</div>
        </div>
      </section>

      {/* Tier Breakdown */}
      <section className="tier-breakdown">
        <h2>Subscription Tiers</h2>
        <div className="tier-cards">
          <div className="tier-card">
            <h3>Free Tier</h3>
            <div className="tier-stats">
              <div className="stat">
                <span className="stat-label">Users</span>
                <span className="stat-value">{stats.free_tier}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Percentage</span>
                <span className="stat-value">{((stats.free_tier / stats.total_subscriptions) * 100).toFixed(1)}%</span>
              </div>
              <div className="stat">
                <span className="stat-label">Revenue</span>
                <span className="stat-value">$0</span>
              </div>
            </div>
          </div>

          <div className="tier-card">
            <h3>Pro Tier</h3>
            <div className="tier-stats">
              <div className="stat">
                <span className="stat-label">Users</span>
                <span className="stat-value">{stats.pro_tier}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Percentage</span>
                <span className="stat-value">{((stats.pro_tier / stats.total_subscriptions) * 100).toFixed(1)}%</span>
              </div>
              <div className="stat">
                <span className="stat-label">MRR</span>
                <span className="stat-value">${(stats.pro_tier * 29).toFixed(2)}</span>
              </div>
            </div>
          </div>

          <div className="tier-card">
            <h3>Enterprise</h3>
            <div className="tier-stats">
              <div className="stat">
                <span className="stat-label">Users</span>
                <span className="stat-value">{stats.enterprise_tier}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Percentage</span>
                <span className="stat-value">{((stats.enterprise_tier / stats.total_subscriptions) * 100).toFixed(1)}%</span>
              </div>
              <div className="stat">
                <span className="stat-label">Custom</span>
                <span className="stat-value">Varies</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Status Breakdown */}
      <section className="status-breakdown">
        <h2>Subscription Status</h2>
        <div className="status-cards">
          <div className="status-card">
            <h3>Active</h3>
            <div className="status-value">{stats.active_subscriptions}</div>
            <div className="status-percentage">{activeRate}% of total</div>
          </div>

          <div className="status-card">
            <h3>Canceled</h3>
            <div className="status-value">{stats.canceled_subscriptions}</div>
            <div className="status-percentage">{churnRate}% churn</div>
          </div>

          <div className="status-card">
            <h3>Conversion Rate</h3>
            <div className="status-value">{conversionFree}%</div>
            <div className="status-percentage">Free to Paid</div>
          </div>
        </div>
      </section>

      {/* Revenue Projection */}
      <section className="revenue-projection">
        <h2>Revenue Projection</h2>
        <div className="projection-grid">
          <div className="projection-card">
            <h4>Current MRR</h4>
            <p>${stats.monthly_recurring_revenue.toFixed(2)}</p>
          </div>

          <div className="projection-card">
            <h4>MRR Growth (10% increase)</h4>
            <p>${(stats.monthly_recurring_revenue * 1.1).toFixed(2)}</p>
          </div>

          <div className="projection-card">
            <h4>Annual Recurring Revenue</h4>
            <p>${(stats.monthly_recurring_revenue * 12).toFixed(2)}</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AdminSubscriptions;
