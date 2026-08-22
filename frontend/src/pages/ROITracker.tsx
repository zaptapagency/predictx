import React, { useState, useEffect } from 'react';
import '../styles/roi-tracker.css';

interface DashboardData {
  summary: {
    revenue_saved: number;
    revenue_created: number;
    efficiency_gain: number;
    total_impact: number;
    forecastx_cost: number;
    net_value: number;
    roi_multiplier: number;
    roi_percentage: number;
  };
  all_time: {
    total_impact: number;
    revenue_saved: number;
    revenue_created: number;
    customers_saved: number;
    expansions_closed: number;
    roi_multiplier: number;
  };
  top_playbooks: any[];
  top_customers: any[];
  forecast_next_month: any;
}

export default function ROITracker() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function fetchDashboard() {
    setLoading(true);
    try {
      const response = await fetch('/api/roi/dashboard');
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error('Error fetching ROI data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="roi-tracker"><div className="loading">Loading ROI data...</div></div>;
  if (!dashboard) return <div className="roi-tracker"><div className="error">Failed to load ROI data</div></div>;

  const summary = dashboard.summary;
  const allTime = dashboard.all_time;

  return (
    <div className="roi-tracker">
      {/* HEADER */}
      <div className="roi-header">
        <h1>💰 ROI Tracker</h1>
        <p>Proof of value from ForecastX</p>
      </div>

      {/* PRIMARY METRICS */}
      <div className="roi-hero">
        <div className="metric-large">
          <div className="label">TOTAL IMPACT (This Month)</div>
          <div className="value">${(summary.total_impact / 1000).toFixed(0)}K</div>
          <div className="breakdown">
            💰 Saved: ${(summary.revenue_saved / 1000).toFixed(0)}K
            <span className="separator">•</span>
            📈 Created: ${(summary.revenue_created / 1000).toFixed(0)}K
          </div>
        </div>

        <div className="metric-large highlight">
          <div className="label">NET ROI</div>
          <div className="value roi-value">${(summary.net_value / 1000).toFixed(0)}K</div>
          <div className="subtext">After ForecastX cost</div>
        </div>

        <div className="metric-large">
          <div className="label">ROI MULTIPLIER</div>
          <div className="value roi-multiplier">{summary.roi_multiplier.toFixed(1)}x</div>
          <div className="subtext">For every $1 spent, ${summary.roi_multiplier.toFixed(1)} returned</div>
        </div>
      </div>

      {/* KEY STATS */}
      <div className="roi-stats">
        <div className="stat-card">
          <div className="icon">🛡️</div>
          <div className="stat-content">
            <div className="label">Revenue Saved</div>
            <div className="value">${(summary.revenue_saved / 1000).toFixed(0)}K</div>
            <div className="note">Prevented churn</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="icon">📈</div>
          <div className="stat-content">
            <div className="label">Revenue Created</div>
            <div className="value">${(summary.revenue_created / 1000).toFixed(0)}K</div>
            <div className="note">Expansions & leads</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="icon">⚡</div>
          <div className="stat-content">
            <div className="label">Efficiency Gained</div>
            <div className="value">${(summary.efficiency_gain / 1000).toFixed(0)}K</div>
            <div className="note">Time saved</div>
          </div>
        </div>

        <div className="stat-card cost">
          <div className="icon">💳</div>
          <div className="stat-content">
            <div className="label">ForecastX Cost</div>
            <div className="value">${(summary.forecastx_cost / 1000).toFixed(0)}K</div>
            <div className="note">This month</div>
          </div>
        </div>
      </div>

      {/* COMPARISON */}
      <div className="roi-comparison">
        <h2>All-Time Impact</h2>
        <div className="comparison-grid">
          <div className="comparison-item">
            <div className="icon">💰</div>
            <div className="label">Total Value Created</div>
            <div className="value">${(allTime.total_impact / 1000000).toFixed(1)}M</div>
          </div>

          <div className="comparison-item">
            <div className="icon">👥</div>
            <div className="label">Customers Saved</div>
            <div className="value">{allTime.customers_saved.toLocaleString()}</div>
          </div>

          <div className="comparison-item">
            <div className="icon">🎯</div>
            <div className="label">Expansions Closed</div>
            <div className="value">{allTime.expansions_closed.toLocaleString()}</div>
          </div>

          <div className="comparison-item">
            <div className="icon">📊</div>
            <div className="label">Overall ROI Multiplier</div>
            <div className="value">{allTime.roi_multiplier.toFixed(1)}x</div>
          </div>
        </div>
      </div>

      {/* TABS */}
      <div className="roi-tabs">
        <button
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab-btn ${activeTab === 'playbooks' ? 'active' : ''}`}
          onClick={() => setActiveTab('playbooks')}
        >
          📋 By Playbook
        </button>
        <button
          className={`tab-btn ${activeTab === 'customers' ? 'active' : ''}`}
          onClick={() => setActiveTab('customers')}
        >
          👥 By Customer
        </button>
      </div>

      {/* TAB CONTENT */}
      <div className="roi-content">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <h3>💡 Your ROI Story</h3>

            <div className="roi-story">
              <div className="story-card">
                <div className="story-icon">🎯</div>
                <div className="story-content">
                  <h4>Revenue Saved (Churn Prevention)</h4>
                  <div className="story-value">${(summary.revenue_saved / 1000).toFixed(0)}K</div>
                  <p className="story-text">
                    Identified {Math.floor(summary.revenue_saved / 50000)} at-risk customers.
                    Took action before they left. Saved critical revenue.
                  </p>
                </div>
              </div>

              <div className="story-card">
                <div className="story-icon">📈</div>
                <div className="story-content">
                  <h4>Revenue Created (Expansion)</h4>
                  <div className="story-value">${(summary.revenue_created / 1000).toFixed(0)}K</div>
                  <p className="story-text">
                    Found {Math.floor(summary.revenue_created / 15000)} expansion opportunities.
                    Closed {Math.floor(summary.revenue_created / 25000)} new deals with existing customers.
                  </p>
                </div>
              </div>

              <div className="story-card">
                <div className="story-icon">⚡</div>
                <div className="story-content">
                  <h4>Efficiency Gained</h4>
                  <div className="story-value">
                    {Math.floor(summary.efficiency_gain / 250)} hrs saved
                  </div>
                  <p className="story-text">
                    Automated {Math.floor(summary.efficiency_gain / 250)} hours of manual work.
                    Team focused on strategy instead of data analysis.
                  </p>
                </div>
              </div>
            </div>

            {/* FORECAST */}
            {dashboard.forecast_next_month && (
              <div className="roi-forecast">
                <h3>🔮 Next Month's Forecast</h3>
                <div className="forecast-card">
                  <div className="forecast-value">
                    ${(dashboard.forecast_next_month.forecasted_impact / 1000).toFixed(0)}K
                  </div>
                  <div className="forecast-confidence">
                    {dashboard.forecast_next_month.confidence ?
                      `${(dashboard.forecast_next_month.confidence * 100).toFixed(0)}% confidence`
                      : 'Calculating...'}
                  </div>
                  <div className="forecast-trend">
                    Trend: {dashboard.forecast_next_month.trend || 'Growing'}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* PLAYBOOKS TAB */}
        {activeTab === 'playbooks' && (
          <div className="tab-pane">
            <h3>📊 Playbook Performance</h3>
            {dashboard.top_playbooks.length > 0 ? (
              <div className="performance-table">
                <div className="table-header">
                  <div className="col-rank">Rank</div>
                  <div className="col-playbook">Playbook</div>
                  <div className="col-value">Total Value</div>
                  <div className="col-success">Success Rate</div>
                  <div className="col-per-exec">Per Execution</div>
                </div>

                {dashboard.top_playbooks.map((pb, idx) => (
                  <div key={pb.playbook_id} className="table-row">
                    <div className="col-rank">
                      {idx === 0 && '🥇'}
                      {idx === 1 && '🥈'}
                      {idx === 2 && '🥉'}
                      {idx >= 3 && `#${idx + 1}`}
                    </div>
                    <div className="col-playbook">Playbook {pb.playbook_id}</div>
                    <div className="col-value">${(pb.total_value / 1000).toFixed(0)}K</div>
                    <div className="col-success">{pb.success_rate}</div>
                    <div className="col-per-exec">${(pb.value_per_execution / 1000).toFixed(0)}K</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No playbook data yet</div>
            )}
          </div>
        )}

        {/* CUSTOMERS TAB */}
        {activeTab === 'customers' && (
          <div className="tab-pane">
            <h3>👥 Top Customers by Impact</h3>
            {dashboard.top_customers.length > 0 ? (
              <div className="customer-list">
                {dashboard.top_customers.map((customer, idx) => (
                  <div key={customer.customer_id} className="customer-card">
                    <div className="customer-rank">
                      {idx === 0 && '🥇'}
                      {idx === 1 && '🥈'}
                      {idx === 2 && '🥉'}
                      {idx >= 3 && `#${idx + 1}`}
                    </div>
                    <div className="customer-info">
                      <div className="customer-name">{customer.customer_name}</div>
                      <div className="customer-details">
                        Playbooks: {customer.playbooks_used} • Actions: {customer.actions_taken}
                      </div>
                    </div>
                    <div className="customer-values">
                      <div className="value-item">
                        <span className="label">Saved:</span>
                        <span className="value">${(customer.revenue_saved / 1000).toFixed(0)}K</span>
                      </div>
                      <div className="value-item">
                        <span className="label">Created:</span>
                        <span className="value">${(customer.revenue_created / 1000).toFixed(0)}K</span>
                      </div>
                      <div className="value-item total">
                        <span className="label">Total:</span>
                        <span className="value">${(customer.total_impact / 1000).toFixed(0)}K</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No customer data yet</div>
            )}
          </div>
        )}
      </div>

      {/* CTA SECTION */}
      <div className="roi-cta">
        <h2>Ready to expand your impact?</h2>
        <p>
          You're generating ${(summary.total_impact / 1000).toFixed(0)}K in value this month.
          Imagine what you could do with more playbooks.
        </p>
        <a href="/marketplace" className="cta-button">
          Browse Playbooks →
        </a>
      </div>
    </div>
  );
}
