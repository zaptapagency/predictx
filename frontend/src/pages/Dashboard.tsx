import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import '../styles/dashboard.css';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
}

interface Usage {
  tier: string;
  predictions: { used: number; limit: number };
  api_calls: { used: number; limit: number };
  cost: number;
  period_start: string;
  period_end: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const userResponse = await fetch('/api/users/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const usageResponse = await fetch('/api/subscriptions/usage', {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (userResponse.ok && usageResponse.ok) {
          setUser(await userResponse.json());
          setUsage(await usageResponse.json());
        } else {
          navigate('/login');
        }
      } catch (err) {
        console.error(err);
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  if (loading) {
    return <div className="dashboard loading">Loading...</div>;
  }

  if (!user || !usage) {
    return <div className="dashboard error">Failed to load dashboard</div>;
  }

  const predictionsUsagePercent = (usage.predictions.used / usage.predictions.limit) * 100;
  const apiCallsUsagePercent = (usage.api_calls.used / usage.api_calls.limit) * 100;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="dashboard-title">
          <h1>Welcome, {user.full_name}!</h1>
          <p>Your PredictX Dashboard</p>
        </div>
        <div className="dashboard-actions">
          <Link to="/settings/profile" className="btn-secondary">
            Settings
          </Link>
          <button onClick={handleLogout} className="btn-outline">
            Logout
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Usage Card */}
        <div className="dashboard-card large">
          <h2>Current Usage</h2>
          <div className="usage-section">
            <div className="usage-item">
              <div className="usage-header">
                <span className="usage-label">Predictions</span>
                <span className="usage-count">
                  {usage.predictions.used} / {usage.predictions.limit}
                </span>
              </div>
              <div className="usage-bar">
                <div
                  className="usage-bar-fill"
                  style={{ width: `${Math.min(predictionsUsagePercent, 100)}%` }}
                ></div>
              </div>
            </div>

            <div className="usage-item">
              <div className="usage-header">
                <span className="usage-label">API Calls</span>
                <span className="usage-count">
                  {usage.api_calls.used} / {usage.api_calls.limit}
                </span>
              </div>
              <div className="usage-bar">
                <div
                  className="usage-bar-fill"
                  style={{ width: `${Math.min(apiCallsUsagePercent, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Subscription Card */}
        <div className="dashboard-card">
          <h2>Subscription</h2>
          <div className="subscription-info">
            <div className="subscription-tier">
              <span className="tier-badge">{usage.tier.toUpperCase()}</span>
            </div>
            <p className="subscription-period">
              Current period: {new Date(usage.period_start).toLocaleDateString()} -{' '}
              {new Date(usage.period_end).toLocaleDateString()}
            </p>
            <p className="subscription-cost">Cost this month: ${usage.cost.toFixed(2)}</p>
          </div>
          <Link to="/settings/billing" className="btn-secondary">
            Manage Subscription
          </Link>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <Link to="/predictions" className="action-link">
              → Make Predictions
            </Link>
            <Link to="/settings/api-keys" className="action-link">
              → API Keys
            </Link>
            <Link to="/settings/usage" className="action-link">
              → View Analytics
            </Link>
          </div>
        </div>

        {/* Get Started */}
        {usage.predictions.used === 0 && (
          <div className="dashboard-card">
            <h2>Get Started</h2>
            <p>Make your first prediction now!</p>
            <Link to="/predictions" className="btn-primary">
              Start Predicting
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
