import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/admin.css';

interface Analytics {
  total_predictions: number;
  total_api_calls: number;
  total_revenue: number;
  predictions_this_month: number;
  api_calls_this_month: number;
  revenue_this_month: number;
  average_predictions_per_user: number;
  average_revenue_per_user: number;
}

interface SubscriptionStats {
  total_subscriptions: number;
  free_tier: number;
  pro_tier: number;
  enterprise_tier: number;
  active_subscriptions: number;
  canceled_subscriptions: number;
  monthly_recurring_revenue: number;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [subscriptionStats, setSubscriptionStats] = useState<SubscriptionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const analyticsRes = await fetch('/api/admin/analytics', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const subscriptionsRes = await fetch('/api/admin/subscriptions', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (analyticsRes.ok && subscriptionsRes.ok) {
        setAnalytics(await analyticsRes.json());
        setSubscriptionStats(await subscriptionsRes.json());
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
    return <div className="admin-dashboard loading">Loading...</div>;
  }

  if (!analytics || !subscriptionStats) {
    return <div className="admin-dashboard error">Failed to load analytics</div>;
  }

  return (
    <div className="admin-dashboard">
      <div className="admin-header">
        <h1>Admin Dashboard</h1>
        <div className="admin-nav">
          <Link to="/admin/users" className="admin-link">
            Users
          </Link>
          <Link to="/admin/subscriptions" className="admin-link">
            Subscriptions
          </Link>
        </div>
      </div>

      {/* Key Metrics */}
      <section className="metrics-grid">
        <div className="metric-card">
          <h3>Total Users</h3>
          <div className="metric-value">
            {(
              subscriptionStats.free_tier +
              subscriptionStats.pro_tier +
              subscriptionStats.enterprise_tier
            ).toLocaleString()}
          </div>
        </div>

        <div className="metric-card">
          <h3>Total Revenue</h3>
          <div className="metric-value">${analytics.total_revenue.toFixed(2)}</div>
        </div>

        <div className="metric-card">
          <h3>MRR (Monthly Recurring)</h3>
          <div className="metric-value">${subscriptionStats.monthly_recurring_revenue.toFixed(2)}</div>
        </div>

        <div className="metric-card">
          <h3>Active Subscriptions</h3>
          <div className="metric-value">{subscriptionStats.active_subscriptions}</div>
        </div>
      </section>

      {/* This Month Stats */}
      <section className="stats-section">
        <h2>This Month</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <h4>Predictions</h4>
            <p>{analytics.predictions_this_month.toLocaleString()}</p>
            <small>Avg per user: {analytics.average_predictions_per_user.toFixed(2)}</small>
          </div>

          <div className="stat-card">
            <h4>API Calls</h4>
            <p>{analytics.api_calls_this_month.toLocaleString()}</p>
            <small>Total usage this month</small>
          </div>

          <div className="stat-card">
            <h4>Revenue</h4>
            <p>${analytics.revenue_this_month.toFixed(2)}</p>
            <small>Avg per user: ${analytics.average_revenue_per_user.toFixed(2)}</small>
          </div>
        </div>
      </section>

      {/* Subscription Breakdown */}
      <section className="subscriptions-section">
        <h2>Subscription Breakdown</h2>
        <div className="subscription-breakdown">
          <div className="tier-card">
            <h3>Free</h3>
            <div className="tier-count">{subscriptionStats.free_tier}</div>
            <p>{((subscriptionStats.free_tier / subscriptionStats.total_subscriptions) * 100).toFixed(1)}% of users</p>
          </div>

          <div className="tier-card">
            <h3>Pro</h3>
            <div className="tier-count">{subscriptionStats.pro_tier}</div>
            <p>$29/month</p>
          </div>

          <div className="tier-card">
            <h3>Enterprise</h3>
            <div className="tier-count">{subscriptionStats.enterprise_tier}</div>
            <p>Custom pricing</p>
          </div>

          <div className="tier-card">
            <h3>Canceled</h3>
            <div className="tier-count">{subscriptionStats.canceled_subscriptions}</div>
            <p>Inactive</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default AdminDashboard;
