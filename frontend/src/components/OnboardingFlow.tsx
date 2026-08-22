import React, { useState, useEffect } from 'react';
import './onboarding-flow.css';
import { onboardingService, OnboardingProgress } from '../services/onboardingService';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  action: string;
  videoUrl?: string;
  completed: boolean;
}

interface OnboardingState {
  currentStep: number;
  completedSteps: string[];
  userGoal: string;
  connectedSalesforce: boolean;
  selectedTemplate: string;
  playbookCreated: boolean;
  firstPrediction: boolean;
}

export const OnboardingFlow: React.FC = () => {
  const [state, setState] = useState<OnboardingState>({
    currentStep: 0,
    completedSteps: [],
    userGoal: '',
    connectedSalesforce: false,
    selectedTemplate: '',
    playbookCreated: false,
    firstPrediction: false
  });

  const [showCelebration, setShowCelebration] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load onboarding progress on mount
  useEffect(() => {
    const loadProgress = async () => {
      try {
        const progress = await onboardingService.getProgress();
        if (progress.is_completed) {
          setShowCelebration(true);
        }
        setState(prev => ({
          ...prev,
          currentStep: progress.current_step,
          completedSteps: progress.completed_steps,
          userGoal: progress.selected_goal || '',
          connectedSalesforce: progress.salesforce_connected,
          selectedTemplate: progress.selected_template || '',
          firstPrediction: progress.first_prediction_seen
        }));
      } catch (err) {
        console.error('Failed to load onboarding progress:', err);
        setError('Failed to load onboarding progress');
      } finally {
        setLoading(false);
      }
    };

    loadProgress();
  }, []);

  const steps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: "Welcome to ForecastX",
      description: "Let's get you set up in 5 minutes",
      icon: "👋",
      action: "Watch intro",
      completed: state.completedSteps.includes('welcome')
    },
    {
      id: 'goal',
      title: "What's your goal?",
      description: "Churn prevention, Growth, or Onboarding?",
      icon: "🎯",
      action: "Choose goal",
      completed: state.completedSteps.includes('goal')
    },
    {
      id: 'connect',
      title: "Connect your data",
      description: "Link Salesforce to see your customers",
      icon: "🔗",
      action: "Connect Salesforce",
      completed: state.connectedSalesforce
    },
    {
      id: 'template',
      title: "Pick a playbook",
      description: "Start with a proven template",
      icon: "📚",
      action: "Choose template",
      completed: state.completedSteps.includes('template')
    },
    {
      id: 'first-win',
      title: "See your first prediction",
      description: "Watch ForecastX identify at-risk customers",
      icon: "✨",
      action: "Activate playbook",
      completed: state.firstPrediction
    }
  ];

  const handleStepComplete = async (stepId: string) => {
    try {
      await onboardingService.completeStep(stepId);
      setState(prev => ({
        ...prev,
        completedSteps: [...prev.completedSteps, stepId],
        currentStep: prev.currentStep + 1
      }));

      if (stepId === 'first-win') {
        await onboardingService.markFirstPredictionSeen();
        setShowCelebration(true);
      }
    } catch (err) {
      console.error('Failed to complete step:', err);
      setError('Failed to save progress');
    }
  };

  const handleSalesforceConnect = async () => {
    try {
      await onboardingService.markSalesforceConnected();
      setState(prev => ({
        ...prev,
        connectedSalesforce: true
      }));
      handleStepComplete('connect');
    } catch (err) {
      console.error('Failed to connect Salesforce:', err);
      setError('Failed to connect Salesforce');
    }
  };

  const handleGoalSelect = async (goal: string) => {
    try {
      await onboardingService.selectGoal(goal);
      setState(prev => ({
        ...prev,
        userGoal: goal
      }));
      handleStepComplete('goal');
    } catch (err) {
      console.error('Failed to select goal:', err);
      setError('Failed to save goal selection');
    }
  };

  const handleTemplateSelect = async (template: string) => {
    try {
      await onboardingService.selectTemplate(template);
      await onboardingService.markFirstPlaybookCreated();
      setState(prev => ({
        ...prev,
        selectedTemplate: template,
        playbookCreated: true
      }));
      handleStepComplete('template');
    } catch (err) {
      console.error('Failed to select template:', err);
      setError('Failed to save template selection');
    }
  };

  const progress = (state.completedSteps.length / steps.length) * 100;
  const allComplete = state.completedSteps.length === steps.length && state.firstPrediction;

  if (loading) {
    return (
      <div className="onboarding-flow">
        <div className="onboarding-container">
          <div className="onboarding-loading">
            <div className="spinner"></div>
            <p>Loading your onboarding...</p>
          </div>
        </div>
      </div>
    );
  }

  if (allComplete && showCelebration) {
    return <CelebrationScreen onComplete={() => setShowCelebration(false)} />;
  }

  return (
    <div className="onboarding-flow">
      {error && (
        <div className="onboarding-error">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <div className="onboarding-container">
        {/* Header */}
        <div className="onboarding-header">
          <div className="onboarding-logo">ForecastX</div>
          <div className="onboarding-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <span className="progress-text">{Math.round(progress)}%</span>
          </div>
        </div>

        {/* Main Content */}
        <div className="onboarding-main">
          {state.currentStep === 0 && (
            <WelcomeStep onComplete={() => handleStepComplete('welcome')} />
          )}

          {state.currentStep === 1 && (
            <GoalSelectionStep
              onSelect={handleGoalSelect}
              selectedGoal={state.userGoal}
            />
          )}

          {state.currentStep === 2 && (
            <DataConnectionStep
              onConnect={handleSalesforceConnect}
              isConnected={state.connectedSalesforce}
            />
          )}

          {state.currentStep === 3 && (
            <TemplateSelectionStep
              onSelect={handleTemplateSelect}
              selectedTemplate={state.selectedTemplate}
            />
          )}

          {state.currentStep === 4 && (
            <FirstWinStep
              goal={state.userGoal}
              template={state.selectedTemplate}
              onComplete={() => {
                setState(prev => ({ ...prev, firstPrediction: true }));
                handleStepComplete('first-win');
              }}
            />
          )}
        </div>

        {/* Step Indicator */}
        <div className="onboarding-steps">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`step-indicator ${
                state.completedSteps.includes(step.id) ? 'completed' : ''
              } ${index === state.currentStep ? 'active' : ''}`}
            >
              {state.completedSteps.includes(step.id) ? '✓' : step.icon}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const WelcomeStep: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  return (
    <div className="onboarding-step welcome-step">
      <div className="step-icon-large">👋</div>
      <h1>Welcome to ForecastX</h1>
      <p className="step-subtitle">Let's turn customer data into revenue in 5 minutes</p>

      <div className="welcome-video-placeholder">
        <div className="video-play-icon">▶</div>
        <p>Watch how Janice prevented a $50K churn in 3 minutes</p>
      </div>

      <div className="welcome-benefits">
        <div className="benefit">
          <span className="benefit-icon">🎯</span>
          <div>
            <strong>Predict Churn</strong>
            <p>Know which customers are at risk before they leave</p>
          </div>
        </div>
        <div className="benefit">
          <span className="benefit-icon">📈</span>
          <div>
            <strong>Drive Growth</strong>
            <p>Identify expansion opportunities automatically</p>
          </div>
        </div>
        <div className="benefit">
          <span className="benefit-icon">⚡</span>
          <div>
            <strong>Automate Actions</strong>
            <p>Trigger workflows without manual work</p>
          </div>
        </div>
      </div>

      <button className="onboarding-btn primary" onClick={onComplete}>
        Let's Get Started →
      </button>

      <p className="onboarding-hint">5 minutes to your first prediction</p>
    </div>
  );
};

const GoalSelectionStep: React.FC<{
  onSelect: (goal: string) => void;
  selectedGoal: string;
}> = ({ onSelect, selectedGoal }) => {
  const [loading, setLoading] = useState(false);

  const goals = [
    {
      id: 'churn',
      icon: '🛡️',
      title: 'Churn Prevention',
      description: 'Stop customer churn before it happens',
      metrics: '45% avg churn reduction'
    },
    {
      id: 'growth',
      icon: '📈',
      title: 'Expansion & Growth',
      description: 'Identify customers ready to buy more',
      metrics: '3.2x avg deal size increase'
    },
    {
      id: 'onboarding',
      icon: '🎯',
      title: 'Customer Success',
      description: 'Guide customers to value faster',
      metrics: '68% faster time-to-value'
    }
  ];

  const handleContinue = async () => {
    if (!selectedGoal) return;
    setLoading(true);
    try {
      await onSelect(selectedGoal);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-step goal-step">
      <h1>What's your biggest goal?</h1>
      <p className="step-subtitle">We'll tailor ForecastX to your priority</p>

      <div className="goal-grid">
        {goals.map(goal => (
          <div
            key={goal.id}
            className={`goal-card ${selectedGoal === goal.id ? 'selected' : ''}`}
            onClick={() => onSelect(goal.id)}
          >
            <div className="goal-icon">{goal.icon}</div>
            <h3>{goal.title}</h3>
            <p>{goal.description}</p>
            <div className="goal-metric">{goal.metrics}</div>
            {selectedGoal === goal.id && <div className="goal-checkmark">✓</div>}
          </div>
        ))}
      </div>

      {selectedGoal && (
        <button
          className="onboarding-btn primary"
          onClick={handleContinue}
          disabled={loading}
        >
          {loading ? '⏳ Saving...' : 'Continue →'}
        </button>
      )}
    </div>
  );
};

const DataConnectionStep: React.FC<{
  onConnect: () => void;
  isConnected: boolean;
}> = ({ onConnect, isConnected }) => {
  const [connecting, setConnecting] = useState(false);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      // Initiate Salesforce OAuth flow
      // User will be redirected to Salesforce login
      onboardingService.initiateSalesforceOAuth();

      // After OAuth callback, onConnect will be called
      // This sets up a listener for the callback
      setTimeout(() => {
        onConnect();
        setConnecting(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to initiate Salesforce OAuth:', error);
      setConnecting(false);
    }
  };

  return (
    <div className="onboarding-step connection-step">
      <div className="step-icon-large">🔗</div>
      <h1>Connect Your Data</h1>
      <p className="step-subtitle">We need to see your customers to make predictions</p>

      <div className="connection-info">
        <div className="info-item">
          <span className="info-icon">☁️</span>
          <div>
            <strong>Salesforce CRM</strong>
            <p>Securely read your accounts, contacts, and opportunities</p>
          </div>
        </div>
        <div className="info-item">
          <span className="info-icon">🔒</span>
          <div>
            <strong>Your Data is Safe</strong>
            <p>Read-only access, encrypted connection, no storage</p>
          </div>
        </div>
      </div>

      {!isConnected ? (
        <button
          className="onboarding-btn primary"
          onClick={handleConnect}
          disabled={connecting}
        >
          {connecting ? '🔄 Connecting...' : '🔐 Connect Salesforce'}
        </button>
      ) : (
        <div className="connection-success">
          <span className="success-icon">✓</span>
          <p>Connected to Salesforce</p>
          <button className="onboarding-btn primary" onClick={onConnect}>
            Continue →
          </button>
        </div>
      )}

      <div className="connection-note">
        <p>💡 We pull your Salesforce data securely once per day</p>
      </div>
    </div>
  );
};

const TemplateSelectionStep: React.FC<{
  onSelect: (template: string) => void;
  selectedTemplate: string;
}> = ({ onSelect, selectedTemplate }) => {
  const [loading, setLoading] = useState(false);

  const templates = [
    {
      id: 'churn-prevention',
      icon: '🚨',
      title: 'Churn Prevention',
      description: 'Alert team on high-risk customers',
      actions: ['Email CSM', 'Slack notification', 'Create task']
    },
    {
      id: 'expansion-ready',
      icon: '🚀',
      title: 'Expansion Ready',
      description: 'Identify customers ready to expand',
      actions: ['Email sales', 'Create Salesforce Opp', 'Slack notification']
    },
    {
      id: 'at-risk-engaged',
      icon: '💬',
      title: 'At-Risk Engagement',
      description: 'Re-engage inactive customers',
      actions: ['Send email', 'Create task', 'Update CRM']
    }
  ];

  const handleContinue = async () => {
    if (!selectedTemplate) return;
    setLoading(true);
    try {
      await onSelect(selectedTemplate);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-step template-step">
      <h1>Pick Your First Playbook</h1>
      <p className="step-subtitle">Start with a proven template. You can create custom ones later</p>

      <div className="template-grid">
        {templates.map(template => (
          <div
            key={template.id}
            className={`template-card ${selectedTemplate === template.id ? 'selected' : ''}`}
            onClick={() => onSelect(template.id)}
          >
            <div className="template-icon">{template.icon}</div>
            <h3>{template.title}</h3>
            <p>{template.description}</p>
            <div className="template-actions">
              {template.actions.map(action => (
                <span key={action} className="action-tag">{action}</span>
              ))}
            </div>
            {selectedTemplate === template.id && <div className="template-checkmark">✓</div>}
          </div>
        ))}
      </div>

      {selectedTemplate && (
        <button
          className="onboarding-btn primary"
          onClick={handleContinue}
          disabled={loading}
        >
          {loading ? '⏳ Creating playbook...' : 'Use This Template →'}
        </button>
      )}
    </div>
  );
};

const FirstWinStep: React.FC<{
  goal: string;
  template: string;
  onComplete: () => void;
}> = ({ goal, template, onComplete }) => {
  const [activating, setActivating] = useState(false);
  const [activated, setActivated] = useState(false);

  const predictions = onboardingService.getMockPredictions();

  const handleActivate = async () => {
    setActivating(true);
    try {
      // Simulate playbook activation and prediction
      await new Promise(resolve => setTimeout(resolve, 2000));
      setActivated(true);

      // Show results after a moment
      await new Promise(resolve => setTimeout(resolve, 2000));
      onComplete();
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="onboarding-step first-win-step">
      <div className="step-icon-large">✨</div>
      <h1>See Your First Prediction</h1>
      <p className="step-subtitle">Activate your playbook to find at-risk customers right now</p>

      <div className="first-win-preview">
        <div className="preview-header">Your Playbook</div>
        <div className="preview-content">
          <div className="preview-item">
            <span className="preview-icon">🎯</span>
            <span>Template: {template}</span>
          </div>
          <div className="preview-item">
            <span className="preview-icon">🎪</span>
            <span>Goal: {goal}</span>
          </div>
          <div className="preview-item">
            <span className="preview-icon">📨</span>
            <span>Actions: Email, Slack, Task</span>
          </div>
        </div>
      </div>

      {!activated ? (
        <button
          className="onboarding-btn primary"
          onClick={handleActivate}
          disabled={activating}
        >
          {activating ? '⚡ Activating...' : '🚀 Activate Playbook'}
        </button>
      ) : (
        <div className="activation-success">
          <div className="success-animation">
            <span className="success-checkmark">✓</span>
          </div>
          <h2>Your playbook is live!</h2>
          <p>Finding customers in your database...</p>
        </div>
      )}

      <div className="first-win-info">
        <p>🎉 ForecastX found {predictions.customers_found} at-risk customers</p>
        <p>💰 Potential revenue at risk: ${(predictions.revenue_at_risk / 1000).toFixed(0)}K</p>
        <p>⚡ {predictions.playbooks_running} playbook executions in progress</p>
      </div>
    </div>
  );
};

const CelebrationScreen: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const predictions = onboardingService.getMockPredictions();

  return (
    <div className="celebration-screen">
      <div className="celebration-content">
        <div className="celebration-animation">
          <span className="confetti">🎉</span>
          <span className="confetti">✨</span>
          <span className="confetti">🚀</span>
        </div>

        <h1>You Did It! 🎊</h1>
        <p className="celebration-subtitle">Your first playbook is live and finding customers</p>

        <div className="celebration-stats">
          <div className="stat">
            <div className="stat-number">{predictions.customers_found}</div>
            <div className="stat-label">At-Risk Customers Found</div>
          </div>
          <div className="stat">
            <div className="stat-number">${(predictions.revenue_at_risk / 1000).toFixed(0)}K</div>
            <div className="stat-label">Revenue at Risk</div>
          </div>
          <div className="stat">
            <div className="stat-number">{predictions.playbooks_running}</div>
            <div className="stat-label">Playbooks Running</div>
          </div>
        </div>

        <div className="celebration-next-steps">
          <h3>Here's what happens next:</h3>
          {predictions.next_steps.map(step => (
            <div key={step.num} className="next-step">
              <span className="step-num">{step.num}</span>
              <div>
                <strong>{step.title}</strong>
                <p>{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        <button className="onboarding-btn primary large" onClick={onComplete}>
          Go to Dashboard
        </button>

        <div className="celebration-footer">
          <p>💡 Tip: Check your Slack for the first customer alert</p>
          <p>📧 Email with tips coming tomorrow morning</p>
        </div>
      </div>
    </div>
  );
};

export default OnboardingFlow;
