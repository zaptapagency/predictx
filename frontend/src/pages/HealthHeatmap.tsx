import React, { useState, useEffect } from 'react';
import '../styles/health-heatmap.css';

interface Customer {
  customer_id: string;
  health: number;
  health_status: string;
  churn_risk: string;
  expansion_potential: string;
  support_urgency: string;
  trend: string;
  red_flags: number;
  yellow_flags: number;
  green_flags: number;
}

interface Summary {
  critical_count: number;
  warning_count: number;
  healthy_count: number;
  total_customers: number;
}

export default function HealthHeatmap() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('health');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHeatmap();
  }, [sortBy]);

  async function fetchHeatmap() {
    setLoading(true);
    try {
      const response = await fetch(`/api/heatmap/overview?sort_by=${sortBy}`);
      const data = await response.json();
      setSummary(data.summary);
      setCustomers(data.customers || []);
    } catch (error) {
      console.error('Error fetching heatmap:', error);
    } finally {
      setLoading(false);
    }
  }

  const getHealthColor = (health: number): string => {
    if (health < 30) return '#ef4444';
    if (health < 70) return '#fbbf24';
    return '#10b981';
  };

  const getHealthLabel = (status: string): string => {
    if (status === 'critical') return '🔴 Critical';
    if (status === 'warning') return '🟡 Warning';
    return '🟢 Healthy';
  };

  if (loading) return <div className="heatmap"><div className="loading">Analyzing customer health...</div></div>;

  return (
    <div className="heatmap">
      {/* HEADER */}
      <div className="heatmap-header">
        <h1>🔥 Customer Health Heatmap</h1>
        <p>Visual overview of customer health, risk, and opportunities</p>
      </div>

      {/* SUMMARY CARDS */}
      {summary && (
        <div className="summary-cards">
          <div className="summary-card critical">
            <div className="icon">🔴</div>
            <div className="content">
              <div className="label">Critical</div>
              <div className="value">{summary.critical_count}</div>
              <div className="subtext">Immediate action needed</div>
            </div>
          </div>

          <div className="summary-card warning">
            <div className="icon">🟡</div>
            <div className="content">
              <div className="label">Warning</div>
              <div className="value">{summary.warning_count}</div>
              <div className="subtext">Monitor closely</div>
            </div>
          </div>

          <div className="summary-card healthy">
            <div className="icon">🟢</div>
            <div className="content">
              <div className="label">Healthy</div>
              <div className="value">{summary.healthy_count}</div>
              <div className="subtext">Growth opportunity</div>
            </div>
          </div>

          <div className="summary-card total">
            <div className="icon">📊</div>
            <div className="content">
              <div className="label">Total Customers</div>
              <div className="value">{summary.total_customers}</div>
              <div className="subtext">Monitored</div>
            </div>
          </div>
        </div>
      )}

      {/* SORT CONTROLS */}
      <div className="sort-controls">
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="sort-select"
        >
          <option value="health">Sort by Health Score</option>
          <option value="urgency">Sort by Urgency</option>
          <option value="churn_risk">Sort by Churn Risk</option>
        </select>
      </div>

      {/* HEATMAP GRID */}
      <div className="heatmap-grid">
        {customers.map((customer) => (
          <div
            key={customer.customer_id}
            className={`heatmap-cell ${customer.health_status}`}
            style={{ backgroundColor: getHealthColor(customer.health) }}
            onClick={() => setSelectedCustomer(customer.customer_id)}
          >
            <div className="cell-content">
              <div className="cell-id">{customer.customer_id}</div>
              <div className="cell-score">{customer.health.toFixed(0)}</div>
            </div>
          </div>
        ))}
      </div>

      {/* DETAILED VIEW */}
      {selectedCustomer && (
        <div className="detail-modal">
          <div className="modal-content">
            <button className="btn-close" onClick={() => setSelectedCustomer(null)}>✕</button>

            {(() => {
              const customer = customers.find(c => c.customer_id === selectedCustomer);
              return customer ? (
                <>
                  <h2>{customer.customer_id}</h2>

                  <div className="detail-metrics">
                    <div className="metric-card">
                      <div className="metric-label">Overall Health</div>
                      <div className="metric-value" style={{ color: getHealthColor(customer.health) }}>
                        {customer.health.toFixed(0)}/100
                      </div>
                      <div className="metric-status">{getHealthLabel(customer.health_status)}</div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-label">Churn Risk</div>
                      <div className="metric-value">{customer.churn_risk}</div>
                      <div className="metric-bar">
                        <div
                          className="bar-fill"
                          style={{
                            width: customer.churn_risk,
                            backgroundColor: customer.churn_risk > '50%' ? '#ef4444' : '#fbbf24'
                          }}
                        />
                      </div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-label">Expansion Potential</div>
                      <div className="metric-value">{customer.expansion_potential}</div>
                      <div className="metric-bar">
                        <div
                          className="bar-fill"
                          style={{
                            width: customer.expansion_potential,
                            backgroundColor: '#10b981'
                          }}
                        />
                      </div>
                    </div>

                    <div className="metric-card">
                      <div className="metric-label">Support Urgency</div>
                      <div className="metric-value">{customer.support_urgency}</div>
                      <div className="metric-bar">
                        <div
                          className="bar-fill"
                          style={{
                            width: customer.support_urgency,
                            backgroundColor: customer.support_urgency > '50%' ? '#fb923c' : '#60a5fa'
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="detail-flags">
                    <h3>Health Indicators</h3>
                    <div className="flags-summary">
                      <div className="flag red">🔴 {customer.red_flags} Critical Issues</div>
                      <div className="flag yellow">🟡 {customer.yellow_flags} Warnings</div>
                      <div className="flag green">🟢 {customer.green_flags} Positives</div>
                    </div>
                  </div>

                  <div className="detail-actions">
                    <button className="btn-action">📞 Schedule Call</button>
                    <button className="btn-action">💬 Send Email</button>
                    <button className="btn-action">📋 Create Task</button>
                  </div>
                </>
              ) : null;
            })()}
          </div>
        </div>
      )}

      {/* LEGEND */}
      <div className="heatmap-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#10b981' }}></div>
          <span>Healthy (70+)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#fbbf24' }}></div>
          <span>Warning (30-70)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ef4444' }}></div>
          <span>Critical (&lt;30)</span>
        </div>
      </div>

      {/* CTA */}
      <div className="heatmap-cta">
        <h2>🎯 Take action on critical customers</h2>
        <p>Address the red flags before they become churn</p>
        <a href="/dashboard/actions" className="cta-button">
          View Critical Customers →
        </a>
      </div>
    </div>
  );
}
