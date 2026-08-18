import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/billing.css';

interface Subscription {
  id: number;
  tier: string;
  status: string;
  monthly_predictions_limit: number;
  api_calls_limit: number;
  current_period_start: string;
  current_period_end: string;
}

interface Invoice {
  id: number;
  amount: number;
  currency: string;
  status: string;
  invoice_date: string;
  paid_at: string;
  invoice_pdf_url: string;
}

const Billing: React.FC = () => {
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const subResponse = await fetch('/api/subscriptions/current', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const invResponse = await fetch('/api/subscriptions/invoices', {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (subResponse.ok && invResponse.ok) {
          setSubscription(await subResponse.json());
          setInvoices(await invResponse.json());
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [navigate]);

  const handleUpgrade = async (tier: string) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    setUpgrading(true);
    try {
      const response = await fetch('/api/subscriptions/upgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ tier }),
      });

      if (response.ok) {
        const data = await response.json();
        setSubscription(data);
        alert('Subscription upgraded successfully!');
      } else {
        alert('Failed to upgrade subscription');
      }
    } catch (err) {
      alert('An error occurred');
    } finally {
      setUpgrading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription?')) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch('/api/subscriptions/cancel', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        alert('Subscription canceled');
        setSubscription(null);
      } else {
        alert('Failed to cancel subscription');
      }
    } catch (err) {
      alert('An error occurred');
    }
  };

  if (loading) {
    return <div className="billing loading">Loading...</div>;
  }

  return (
    <div className="billing">
      <h1>Billing & Subscription</h1>

      {/* Current Subscription */}
      <section className="subscription-section">
        <h2>Current Subscription</h2>
        {subscription ? (
          <div className="subscription-card">
            <div className="subscription-details">
              <h3>{subscription.tier.toUpperCase()}</h3>
              <p>
                Status: <strong>{subscription.status}</strong>
              </p>
              <p>
                Period: {new Date(subscription.current_period_start).toLocaleDateString()} -{' '}
                {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            </div>
            {subscription.tier !== 'free' && (
              <button onClick={handleCancel} className="btn-danger">
                Cancel Subscription
              </button>
            )}
          </div>
        ) : (
          <p>No active subscription. Choose a plan below.</p>
        )}
      </section>

      {/* Pricing Plans */}
      <section className="pricing-section">
        <h2>Upgrade Your Plan</h2>
        <div className="pricing-grid">
          {/* Free Tier */}
          <div className="pricing-card">
            <h3>Free</h3>
            <div className="price">$0/month</div>
            <ul className="features">
              <li>100 predictions/month</li>
              <li>1,000 API calls/month</li>
              <li>Community support</li>
            </ul>
            {subscription?.tier === 'free' && <button className="btn-secondary">Current Plan</button>}
          </div>

          {/* Pro Tier */}
          <div className="pricing-card featured">
            <h3>Pro</h3>
            <div className="price">$29/month</div>
            <ul className="features">
              <li>10,000 predictions/month</li>
              <li>100,000 API calls/month</li>
              <li>Email support</li>
              <li>Usage analytics</li>
            </ul>
            {subscription?.tier === 'pro' ? (
              <button className="btn-secondary">Current Plan</button>
            ) : (
              <button
                onClick={() => handleUpgrade('pro')}
                className="btn-primary"
                disabled={upgrading}
              >
                {upgrading ? 'Upgrading...' : 'Upgrade to Pro'}
              </button>
            )}
          </div>

          {/* Enterprise Tier */}
          <div className="pricing-card">
            <h3>Enterprise</h3>
            <div className="price">Custom</div>
            <ul className="features">
              <li>Unlimited predictions</li>
              <li>Unlimited API calls</li>
              <li>Priority support</li>
              <li>Custom SLA</li>
            </ul>
            <a href="mailto:sales@predictx.com" className="btn-outline">
              Contact Sales
            </a>
          </div>
        </div>
      </section>

      {/* Invoices */}
      <section className="invoices-section">
        <h2>Billing History</h2>
        {invoices.length > 0 ? (
          <table className="invoices-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Invoice ID</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(invoice => (
                <tr key={invoice.id}>
                  <td>{new Date(invoice.invoice_date).toLocaleDateString()}</td>
                  <td>{invoice.id}</td>
                  <td>
                    {invoice.currency.toUpperCase()} {invoice.amount.toFixed(2)}
                  </td>
                  <td>
                    <span className={`status-badge ${invoice.status}`}>{invoice.status}</span>
                  </td>
                  <td>
                    {invoice.invoice_pdf_url && (
                      <a href={invoice.invoice_pdf_url} target="_blank" rel="noopener noreferrer">
                        Download PDF
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No invoices yet.</p>
        )}
      </section>
    </div>
  );
};

export default Billing;
