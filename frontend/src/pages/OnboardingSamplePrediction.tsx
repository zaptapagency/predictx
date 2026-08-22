import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/onboarding.css'

interface Prediction {
  high_risk_count: number
  revenue_at_risk: number
  avg_risk_score: number
  top_10_customers: any[]
}

const OnboardingSamplePrediction: React.FC = () => {
  const navigate = useNavigate()
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // ============================================================================
  // LOAD SAMPLE PREDICTION ON MOUNT
  // ============================================================================
  useEffect(() => {
    const loadSamplePrediction = async () => {
      try {
        const token = localStorage.getItem('access_token')

        const response = await fetch('/api/predictions/sample', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        })

        if (!response.ok) {
          throw new Error('Failed to load sample prediction')
        }

        const data = await response.json()
        setPrediction(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load prediction')
      } finally {
        setLoading(false)
      }
    }

    loadSamplePrediction()
  }, [])

  // ============================================================================
  // LOADING STATE
  // ============================================================================
  if (loading) {
    return (
      <div className="onboarding-container">
        <div className="onboarding-loading">
          <div className="loader"></div>
          <h2>Analyzing your data...</h2>
          <p>Running churn prediction model</p>
        </div>
      </div>
    )
  }

  // ============================================================================
  // ERROR STATE
  // ============================================================================
  if (error) {
    return (
      <div className="onboarding-container">
        <div className="onboarding-error">
          <h2>⚠️ Something went wrong</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!prediction) {
    return null
  }

  // ============================================================================
  // SUCCESS STATE: SHOW RESULTS
  // ============================================================================
  return (
    <div className="onboarding-container">
      {/* HEADER */}
      <div className="onboarding-header">
        <h1>🎉 Your Churn Analysis is Ready!</h1>
        <p>Here's what we found in your sample data:</p>
      </div>

      {/* KPI CARDS */}
      <div className="kpi-grid">
        <div className="kpi-card danger">
          <div className="kpi-number">{prediction.high_risk_count}</div>
          <div className="kpi-label">Customers at High Risk</div>
          <div className="kpi-subtext">Need immediate attention</div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-number">${(prediction.revenue_at_risk / 1000).toFixed(0)}K</div>
          <div className="kpi-label">Revenue at Risk</div>
          <div className="kpi-subtext">Potential monthly loss</div>
        </div>

        <div className="kpi-card info">
          <div className="kpi-number">{(prediction.avg_risk_score * 100).toFixed(0)}%</div>
          <div className="kpi-label">Average Risk Score</div>
          <div className="kpi-subtext">Out of 100</div>
        </div>
      </div>

      {/* TOP RISKY CUSTOMERS */}
      <div className="section">
        <h2>Top Customers at Risk</h2>
        <p className="section-subtext">
          These customers have the highest probability of churning. Take action now.
        </p>

        <div className="customer-table">
          <div className="table-header">
            <div className="col-customer">Customer</div>
            <div className="col-risk">Risk Score</div>
            <div className="col-mrr">Monthly Value</div>
            <div className="col-why">Why at Risk</div>
          </div>

          {prediction.top_10_customers.slice(0, 5).map((customer, idx) => (
            <div key={idx} className="table-row">
              <div className="col-customer">
                <div className="customer-name">{customer.name}</div>
                <div className="customer-email">{customer.email}</div>
              </div>
              <div className="col-risk">
                <div className="risk-badge" style={{
                  backgroundColor: customer.churn_risk > 0.7 ? '#ef4444' : customer.churn_risk > 0.5 ? '#f97316' : '#eab308'
                }}>
                  {(customer.churn_risk * 100).toFixed(0)}%
                </div>
              </div>
              <div className="col-mrr">
                <strong>${customer.mrr?.toFixed(0) || 'N/A'}</strong>
              </div>
              <div className="col-why">
                <span className="reason">{customer.reason || 'Declining usage'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* INSIGHTS */}
      <div className="section">
        <h2>Key Insights</h2>
        <div className="insights-grid">
          <div className="insight-card">
            <div className="insight-icon">📉</div>
            <div className="insight-content">
              <h3>Usage Decline</h3>
              <p>
                {prediction.high_risk_count} customers have reduced API usage by &gt;50% this month
              </p>
            </div>
          </div>

          <div className="insight-card">
            <div className="insight-icon">🔄</div>
            <div className="insight-content">
              <h3>Support Tickets</h3>
              <p>
                High-risk customers have 3x more support issues (usually before leaving)
              </p>
            </div>
          </div>

          <div className="insight-card">
            <div className="insight-icon">💳</div>
            <div className="insight-content">
              <h3>Payment Issues</h3>
              <p>
                {Math.round(prediction.high_risk_count * 0.3)} customers have failed payments
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CALL TO ACTION */}
      <div className="section cta-section">
        <h2>Next Steps</h2>

        <div className="action-grid">
          <div className="action-card">
            <div className="action-number">1</div>
            <div className="action-content">
              <h3>Connect Your Real Data</h3>
              <p>
                This analysis used sample data. Connect Salesforce, Stripe, or upload your CSV
                to get real churn predictions for your customers.
              </p>
              <button
                className="button secondary"
                onClick={() => navigate('/integrations')}
              >
                Connect Data Source
              </button>
            </div>
          </div>

          <div className="action-card">
            <div className="action-number">2</div>
            <div className="action-content">
              <h3>Invite Your Team</h3>
              <p>
                Let your CS team see churn predictions. Share insights and collaborate
                on retention strategies.
              </p>
              <button
                className="button secondary"
                onClick={() => navigate('/settings/team')}
              >
                Invite Team Members
              </button>
            </div>
          </div>

          <div className="action-card">
            <div className="action-number">3</div>
            <div className="action-content">
              <h3>Take Action</h3>
              <p>
                For each at-risk customer, reach out, understand their issues,
                and work on retention.
              </p>
              <button
                className="button secondary"
                onClick={() => navigate('/predictions')}
              >
                See Full Analysis
              </button>
            </div>
          </div>
        </div>

        <div className="primary-cta">
          <h3>Ready to get started?</h3>
          <button
            className="button primary large"
            onClick={() => navigate('/integrations')}
          >
            Connect Your Data Now →
          </button>
          <p className="cta-subtext">
            Takes 2 minutes. Sync Salesforce, Stripe, or upload CSV.
          </p>
        </div>
      </div>

      {/* FEATURES */}
      <div className="features-section">
        <h2>What You Get With ForecastX</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Real-Time Predictions</h3>
            <p>Updated every hour with latest customer data</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎯</div>
            <h3>Actionable Insights</h3>
            <p>Know exactly why customers are at risk</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>Track Results</h3>
            <p>See how many customers you've saved</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔗</div>
            <h3>Integrations</h3>
            <p>Works with Salesforce, Stripe, HubSpot, and more</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">👥</div>
            <h3>Team Collaboration</h3>
            <p>Invite CS team and share predictions</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>Scale Fast</h3>
            <p>Handle millions of customer records</p>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <div className="onboarding-footer">
        <p>
          Have questions? <a href="mailto:support@forecastx.io">Email support</a> or
          <a href="https://calendly.com/forecastx"> schedule a demo</a>
        </p>
      </div>
    </div>
  )
}

export default OnboardingSamplePrediction
