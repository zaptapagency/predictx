import React, { useState } from 'react';
import '../styles/publish-playbook.css';

export default function PublishPlaybook() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    use_case: '',
    industry: '',
    price_monthly: 49,
    price_yearly: 499,
    free: false,
    success_rate: 0.78,
    typical_roi: 5.6,
    setup_time_minutes: 15,
  });

  const [configuration, setConfiguration] = useState({
    trigger: 'score > 0.8',
    actions: ['send_email', 'slack_alert'],
    schedule: 'daily',
  });

  const [submitting, setSubmitting] = useState(false);

  const categories = [
    'churn', 'expansion', 'fraud', 'forecasting', 'lead-scoring',
    'pricing', 'upsell', 'support', 'product', 'retention'
  ];

  const useCases = [
    'churn-prediction', 'lead-scoring', 'fraud-detection', 'demand-forecasting',
    'price-optimization', 'expansion-opportunity', 'customer-health', 'support-escalation'
  ];

  const industries = [
    'SaaS', 'E-commerce', 'Fintech', 'Healthcare', 'Telecom',
    'Insurance', 'Retail', 'Manufacturing', 'Subscription', 'Enterprise'
  ];

  function handleInputChange(field: string, value: any) {
    setFormData(prev => ({ ...prev, [field]: value }));
  }

  async function handlePublish() {
    if (!formData.name || !formData.description || !formData.category) {
      alert('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch('/api/marketplace/playbooks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          configuration,
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert('✅ Playbook published! Check your creator dashboard.');
        window.location.href = '/creator-dashboard';
      }
    } catch (error) {
      console.error('Error publishing playbook:', error);
      alert('Failed to publish playbook');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="publish-playbook-container">
      <div className="publish-header">
        <h1>📤 Publish Your Playbook</h1>
        <p>Share your winning playbook and start earning 70% revenue share</p>
      </div>

      {/* STEPS INDICATOR */}
      <div className="steps-indicator">
        {[1, 2, 3, 4].map((s) => (
          <div
            key={s}
            className={`step-indicator ${step === s ? 'active' : ''} ${step > s ? 'completed' : ''}`}
            onClick={() => setStep(s)}
          >
            <div className="step-number">{s}</div>
            <div className="step-label">
              {s === 1 && 'Basic Info'}
              {s === 2 && 'Configuration'}
              {s === 3 && 'Pricing'}
              {s === 4 && 'Review'}
            </div>
          </div>
        ))}
      </div>

      <div className="publish-form">
        {/* STEP 1: BASIC INFO */}
        {step === 1 && (
          <div className="form-step">
            <h2>📋 Basic Information</h2>

            <div className="form-group">
              <label>Playbook Name *</label>
              <input
                type="text"
                placeholder="e.g., High-Value Customer Churn Prevention"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Description *</label>
              <textarea
                placeholder="Describe what your playbook does and how it helps customers..."
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={5}
                className="form-input"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Category *</label>
                <select
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="form-input"
                >
                  <option value="">Select category...</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Use Case *</label>
                <select
                  value={formData.use_case}
                  onChange={(e) => handleInputChange('use_case', e.target.value)}
                  className="form-input"
                >
                  <option value="">Select use case...</option>
                  {useCases.map(uc => (
                    <option key={uc} value={uc}>{uc}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Industry (Optional)</label>
              <select
                value={formData.industry}
                onChange={(e) => handleInputChange('industry', e.target.value)}
                className="form-input"
              >
                <option value="">Select industry...</option>
                {industries.map(ind => (
                  <option key={ind} value={ind}>{ind}</option>
                ))}
              </select>
            </div>

            <div className="form-actions">
              <button onClick={() => setStep(2)} className="btn btn-primary">
                Next: Configuration →
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: CONFIGURATION */}
        {step === 2 && (
          <div className="form-step">
            <h2>⚙️ Playbook Configuration</h2>

            <div className="form-group">
              <label>Trigger Condition</label>
              <input
                type="text"
                placeholder="e.g., score > 0.8 (high churn risk)"
                value={configuration.trigger}
                onChange={(e) => setConfiguration(prev => ({ ...prev, trigger: e.target.value }))}
                className="form-input"
              />
              <small>What triggers this playbook to run?</small>
            </div>

            <div className="form-group">
              <label>Actions</label>
              <div className="checkbox-group">
                {['send_email', 'slack_alert', 'create_task', 'webhook'].map(action => (
                  <label key={action}>
                    <input
                      type="checkbox"
                      checked={configuration.actions.includes(action)}
                      onChange={(e) => {
                        const updated = e.target.checked
                          ? [...configuration.actions, action]
                          : configuration.actions.filter(a => a !== action);
                        setConfiguration(prev => ({ ...prev, actions: updated }));
                      }}
                    />
                    {action.replace('_', ' ').toUpperCase()}
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Schedule</label>
              <select
                value={configuration.schedule}
                onChange={(e) => setConfiguration(prev => ({ ...prev, schedule: e.target.value }))}
                className="form-input"
              >
                <option value="daily">Daily</option>
                <option value="hourly">Hourly</option>
                <option value="weekly">Weekly</option>
                <option value="realtime">Real-time</option>
              </select>
            </div>

            <div className="form-actions">
              <button onClick={() => setStep(1)} className="btn btn-secondary">
                ← Back
              </button>
              <button onClick={() => setStep(3)} className="btn btn-primary">
                Next: Pricing →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: PRICING & METRICS */}
        {step === 3 && (
          <div className="form-step">
            <h2>💰 Pricing & Performance Metrics</h2>

            <div className="pricing-section">
              <h3>Pricing Model</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.free}
                      onChange={(e) => handleInputChange('free', e.target.checked)}
                    />
                    Make this playbook free
                  </label>
                </div>
              </div>

              {!formData.free && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Monthly Price ($)</label>
                      <input
                        type="number"
                        value={formData.price_monthly}
                        onChange={(e) => handleInputChange('price_monthly', parseFloat(e.target.value))}
                        className="form-input"
                      />
                      <small>Recommended: $49 - $99/month</small>
                    </div>

                    <div className="form-group">
                      <label>Yearly Price ($)</label>
                      <input
                        type="number"
                        value={formData.price_yearly}
                        onChange={(e) => handleInputChange('price_yearly', parseFloat(e.target.value))}
                        className="form-input"
                      />
                      <small>Usually 20% discount (e.g., $499/year)</small>
                    </div>
                  </div>

                  <div className="price-preview">
                    Monthly: ${formData.price_monthly}/month
                    {formData.price_yearly && ` • Yearly: ${(formData.price_yearly / 12).toFixed(0)}/month when paid yearly`}
                  </div>
                </>
              )}
            </div>

            <div className="metrics-section">
              <h3>Performance Metrics</h3>
              <p className="section-note">Help customers understand expected results</p>

              <div className="form-row">
                <div className="form-group">
                  <label>Success Rate (0-1)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formData.success_rate}
                    onChange={(e) => handleInputChange('success_rate', parseFloat(e.target.value))}
                    className="form-input"
                  />
                  <small>% of executed actions that succeed (e.g., 0.78 = 78%)</small>
                </div>

                <div className="form-group">
                  <label>Typical ROI Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.typical_roi}
                    onChange={(e) => handleInputChange('typical_roi', parseFloat(e.target.value))}
                    className="form-input"
                  />
                  <small>e.g., 5.6 = 560% ROI (revenue saved ÷ subscription cost)</small>
                </div>

                <div className="form-group">
                  <label>Setup Time (minutes)</label>
                  <input
                    type="number"
                    value={formData.setup_time_minutes}
                    onChange={(e) => handleInputChange('setup_time_minutes', parseInt(e.target.value))}
                    className="form-input"
                  />
                  <small>How long to setup and start using</small>
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button onClick={() => setStep(2)} className="btn btn-secondary">
                ← Back
              </button>
              <button onClick={() => setStep(4)} className="btn btn-primary">
                Next: Review →
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: REVIEW */}
        {step === 4 && (
          <div className="form-step">
            <h2>✅ Review & Publish</h2>

            <div className="review-card">
              <div className="review-section">
                <h3>Basic Information</h3>
                <p><strong>Name:</strong> {formData.name}</p>
                <p><strong>Description:</strong> {formData.description}</p>
                <p><strong>Category:</strong> {formData.category}</p>
                <p><strong>Use Case:</strong> {formData.use_case}</p>
                {formData.industry && <p><strong>Industry:</strong> {formData.industry}</p>}
              </div>

              <div className="review-section">
                <h3>Pricing</h3>
                {formData.free ? (
                  <p>🎁 <strong>Free playbook</strong> - No payment required</p>
                ) : (
                  <>
                    <p>💳 <strong>Monthly:</strong> ${formData.price_monthly}/month</p>
                    {formData.price_yearly && <p>📅 <strong>Yearly:</strong> ${formData.price_yearly}/year</p>}
                    <p className="revenue-note">
                      You'll earn 70%: ${(formData.price_monthly * 0.7).toFixed(0)}/month per customer
                    </p>
                  </>
                )}
              </div>

              <div className="review-section">
                <h3>Metrics</h3>
                <p>✅ <strong>Success Rate:</strong> {(formData.success_rate * 100).toFixed(0)}%</p>
                <p>📈 <strong>Typical ROI:</strong> {formData.typical_roi.toFixed(1)}x</p>
                <p>⏱️ <strong>Setup Time:</strong> {formData.setup_time_minutes} minutes</p>
              </div>

              <div className="review-checklist">
                <h3>Before Publishing</h3>
                <label>
                  <input type="checkbox" /> My playbook provides real value to customers
                </label>
                <label>
                  <input type="checkbox" /> I've tested it thoroughly
                </label>
                <label>
                  <input type="checkbox" /> I agree to ForecastX terms and revenue sharing (70/30 split)
                </label>
              </div>
            </div>

            <div className="form-actions">
              <button onClick={() => setStep(3)} className="btn btn-secondary">
                ← Back
              </button>
              <button
                onClick={handlePublish}
                disabled={submitting}
                className="btn btn-primary btn-lg"
              >
                {submitting ? '⏳ Publishing...' : '🚀 Publish Playbook'}
              </button>
            </div>

            <p className="publish-note">
              Your playbook will be submitted for review. We'll publish it within 24 hours.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
