import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/integrations.css'

interface ConnectorOption {
  id: string
  name: string
  description: string
  icon: string
  difficulty: 'easy' | 'medium'
  time: string
  setupInstructions: string
}

const CONNECTORS: ConnectorOption[] = [
  {
    id: 'csv',
    name: 'CSV Upload',
    description: 'Upload your customer data as CSV. Fastest way to get started.',
    icon: '📊',
    difficulty: 'easy',
    time: '2 minutes',
    setupInstructions: 'Upload your customer data CSV with columns: name, email, monthly_value, last_login_date, support_tickets'
  },
  {
    id: 'salesforce',
    name: 'Salesforce',
    description: 'Auto-sync customer data from Salesforce. Real-time updates.',
    icon: '☁️',
    difficulty: 'medium',
    time: '5 minutes',
    setupInstructions: 'Connect your Salesforce account via OAuth. ForecastX will sync Account and Contact data automatically.'
  },
  {
    id: 'stripe',
    name: 'Stripe',
    description: 'Sync billing and payment data from Stripe. Identify churn risk automatically.',
    icon: '💳',
    difficulty: 'medium',
    time: '3 minutes',
    setupInstructions: 'Enter your Stripe API key. ForecastX will sync customer and subscription data.'
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    description: 'Connect HubSpot CRM. See churn risk scores in your deals.',
    icon: '🎯',
    difficulty: 'medium',
    time: '5 minutes',
    setupInstructions: 'Connect your HubSpot account. Risk scores sync to contact records.'
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    description: 'Direct database connection. Query your customer data automatically.',
    icon: '🗄️',
    difficulty: 'medium',
    time: '10 minutes',
    setupInstructions: 'Provide PostgreSQL connection string. We\'ll query your database securely.'
  },
  {
    id: 'zapier',
    name: 'Zapier',
    description: 'Connect via Zapier to 5,000+ apps.',
    icon: '⚡',
    difficulty: 'medium',
    time: '5 minutes',
    setupInstructions: 'Search "ForecastX" in Zapier. Set up automation in minutes.'
  },
]

const DataConnectors: React.FC = () => {
  const navigate = useNavigate()
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null)
  const [connected, setConnected] = useState<Set<string>>(new Set())

  const handleConnect = (connectorId: string) => {
    setSelectedConnector(connectorId)
  }

  const handleConnected = (connectorId: string) => {
    setConnected(new Set(connected).add(connectorId))
    setSelectedConnector(null)

    // If they've connected at least one source, show next steps
    if (connected.size === 0) {
      setTimeout(() => {
        navigate('/onboarding/team-setup')
      }, 1000)
    }
  }

  const activeConnector = CONNECTORS.find(c => c.id === selectedConnector)

  return (
    <div className="integrations-container">
      {/* HEADER */}
      <div className="integrations-header">
        <h1>Connect Your Data</h1>
        <p>Import your customer data from any source. ForecastX works best with real data.</p>
      </div>

      {/* QUICK STATS */}
      <div className="quick-stats">
        <div className="stat">
          <div className="stat-number">{connected.size}</div>
          <div className="stat-label">Connected</div>
        </div>
        <div className="stat">
          <div className="stat-number">6</div>
          <div className="stat-label">Available Integrations</div>
        </div>
        <div className="stat">
          <div className="stat-number">2-10</div>
          <div className="stat-label">Min to Setup</div>
        </div>
      </div>

      {/* CONNECTOR GRID */}
      <div className="connectors-grid">
        {CONNECTORS.map((connector) => (
          <div
            key={connector.id}
            className={`connector-card ${selectedConnector === connector.id ? 'active' : ''} ${connected.has(connector.id) ? 'connected' : ''}`}
            onClick={() => handleConnect(connector.id)}
          >
            <div className="connector-header">
              <span className="connector-icon">{connector.icon}</span>
              {connected.has(connector.id) && <span className="connected-badge">✓ Connected</span>}
            </div>

            <h3>{connector.name}</h3>
            <p>{connector.description}</p>

            <div className="connector-meta">
              <span className="difficulty" data-level={connector.difficulty}>
                {connector.difficulty === 'easy' ? '✨ Easy' : '⚙️ Standard'}
              </span>
              <span className="time">⏱️ {connector.time}</span>
            </div>

            {selectedConnector !== connector.id && (
              <button className="connect-btn">
                {connected.has(connector.id) ? 'Reconnect' : 'Connect'}
              </button>
            )}
          </div>
        ))}
      </div>

      {/* SETUP MODAL */}
      {activeConnector && (
        <div className="modal-overlay" onClick={() => setSelectedConnector(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{activeConnector.name}</h2>
              <button className="close-btn" onClick={() => setSelectedConnector(null)}>✕</button>
            </div>

            <div className="modal-body">
              <div className="setup-instructions">
                <h3>How to Connect</h3>
                <p>{activeConnector.setupInstructions}</p>

                {activeConnector.id === 'csv' && (
                  <div className="csv-upload">
                    <div className="upload-area">
                      <div className="upload-icon">📁</div>
                      <h4>Drag and drop your CSV here</h4>
                      <p>or <button className="link-btn">browse files</button></p>
                      <p className="file-requirements">CSV format • 50MB max • Columns: name, email, monthly_value</p>
                    </div>
                  </div>
                )}

                {activeConnector.id === 'salesforce' && (
                  <div className="oauth-setup">
                    <button className="oauth-button salesforce-button" onClick={() => handleConnected('salesforce')}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0z" />
                      </svg>
                      Connect with Salesforce
                    </button>
                    <p className="note">We'll never store your Salesforce password. OAuth is secure.</p>
                  </div>
                )}

                {activeConnector.id === 'stripe' && (
                  <div className="api-key-setup">
                    <label>Stripe API Key</label>
                    <input
                      type="password"
                      placeholder="sk_live_..."
                      className="api-input"
                    />
                    <button
                      className="submit-btn"
                      onClick={() => handleConnected('stripe')}
                    >
                      Verify & Connect
                    </button>
                    <p className="note">Your API key is encrypted and never shared.</p>
                  </div>
                )}

                {activeConnector.id === 'hubspot' && (
                  <div className="oauth-setup">
                    <button className="oauth-button hubspot-button" onClick={() => handleConnected('hubspot')}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <circle cx="12" cy="12" r="12" />
                      </svg>
                      Connect with HubSpot
                    </button>
                  </div>
                )}

                {activeConnector.id === 'postgresql' && (
                  <div className="api-key-setup">
                    <label>PostgreSQL Connection String</label>
                    <input
                      type="password"
                      placeholder="postgresql://user:password@host:5432/dbname"
                      className="api-input"
                    />
                    <button
                      className="submit-btn"
                      onClick={() => handleConnected('postgresql')}
                    >
                      Test Connection
                    </button>
                  </div>
                )}

                {activeConnector.id === 'zapier' && (
                  <div className="external-link">
                    <a href="https://zapier.com/apps/forecastx" target="_blank" rel="noopener noreferrer" className="external-btn">
                      Open Zapier →
                    </a>
                    <p className="note">You'll be redirected to Zapier to set up the integration.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <div className="integrations-footer">
        <div className="footer-content">
          <h3>Need help?</h3>
          <p>Check out our <a href="/docs/integrations">integration guides</a> or <a href="mailto:support@forecastx.io">email support</a></p>
        </div>

        <div className="footer-actions">
          {connected.size > 0 ? (
            <button className="button primary" onClick={() => navigate('/onboarding/team-setup')}>
              Next: Invite Your Team →
            </button>
          ) : (
            <p className="notice">Connect at least one data source to continue</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default DataConnectors
