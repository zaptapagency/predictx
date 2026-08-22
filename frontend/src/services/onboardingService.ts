/**
 * Onboarding Service
 * Handles all API calls for onboarding flow
 */

import { api } from './api';

export interface OnboardingProgress {
  current_step: number;
  completed_steps: string[];
  selected_goal?: string;
  selected_template?: string;
  salesforce_connected: boolean;
  first_playbook_created: boolean;
  first_prediction_seen: boolean;
  is_completed: boolean;
}

export interface OnboardingEvent {
  event_type: string;
  step_id?: string;
  action?: string;
  created_at: string;
}

export interface OnboardingStats {
  total_users: number;
  completed_users: number;
  completion_rate: number;
  salesforce_connected: number;
  first_playbook_created: number;
}

class OnboardingService {
  // ===== PROGRESS TRACKING =====

  /**
   * Get user's current onboarding progress
   */
  async getProgress(): Promise<OnboardingProgress> {
    try {
      const response = await api.get('/api/onboarding/progress');
      return response.data;
    } catch (error) {
      console.error('Failed to get onboarding progress:', error);
      // Return default progress if error
      return {
        current_step: 0,
        completed_steps: [],
        salesforce_connected: false,
        first_playbook_created: false,
        first_prediction_seen: false,
        is_completed: false
      };
    }
  }

  /**
   * Mark a step as complete
   */
  async completeStep(
    stepId: string,
    action?: string,
    metadata?: Record<string, any>
  ): Promise<{ step_id: string; completed: boolean; progress: number; total_steps: number }> {
    try {
      const response = await api.post(`/api/onboarding/steps/${stepId}/complete`, {
        step_id: stepId,
        action,
        metadata
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to complete step ${stepId}:`, error);
      throw error;
    }
  }

  // ===== SELECTIONS =====

  /**
   * Save user's goal selection
   */
  async selectGoal(goal: string): Promise<{ goal: string; selected: boolean }> {
    try {
      const response = await api.post('/api/onboarding/goal', { goal });
      return response.data;
    } catch (error) {
      console.error('Failed to select goal:', error);
      throw error;
    }
  }

  /**
   * Save user's template selection
   */
  async selectTemplate(template: string): Promise<{ template: string; selected: boolean }> {
    try {
      const response = await api.post('/api/onboarding/template', { template });
      return response.data;
    } catch (error) {
      console.error('Failed to select template:', error);
      throw error;
    }
  }

  // ===== MILESTONES =====

  /**
   * Mark Salesforce as connected
   */
  async markSalesforceConnected(): Promise<{ salesforce_connected: boolean; connected_at: string }> {
    try {
      const response = await api.post('/api/onboarding/salesforce/connected');
      return response.data;
    } catch (error) {
      console.error('Failed to mark Salesforce connected:', error);
      throw error;
    }
  }

  /**
   * Mark first playbook as created
   */
  async markFirstPlaybookCreated(): Promise<{ playbook_created: boolean; created_at: string }> {
    try {
      const response = await api.post('/api/onboarding/first-playbook-created');
      return response.data;
    } catch (error) {
      console.error('Failed to mark playbook created:', error);
      throw error;
    }
  }

  /**
   * Mark first prediction as seen
   */
  async markFirstPredictionSeen(): Promise<{
    prediction_seen: boolean;
    seen_at: string;
    onboarding_complete: boolean;
  }> {
    try {
      const response = await api.post('/api/onboarding/first-prediction-seen');
      return response.data;
    } catch (error) {
      console.error('Failed to mark prediction seen:', error);
      throw error;
    }
  }

  // ===== ANALYTICS =====

  /**
   * Get onboarding events for user
   */
  async getEvents(): Promise<OnboardingEvent[]> {
    try {
      const response = await api.get('/api/onboarding/events');
      return response.data.events || [];
    } catch (error) {
      console.error('Failed to get onboarding events:', error);
      return [];
    }
  }

  /**
   * Get org-wide onboarding stats
   */
  async getStats(): Promise<OnboardingStats> {
    try {
      const response = await api.get('/api/onboarding/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get onboarding stats:', error);
      return {
        total_users: 0,
        completed_users: 0,
        completion_rate: 0,
        salesforce_connected: 0,
        first_playbook_created: 0
      };
    }
  }

  /**
   * Check if user should see onboarding
   */
  async shouldShowOnboarding(): Promise<boolean> {
    try {
      const progress = await this.getProgress();
      // Show onboarding if not completed
      return !progress.is_completed;
    } catch {
      // Show onboarding if we can't determine
      return true;
    }
  }

  /**
   * Initiate Salesforce OAuth flow
   */
  initiateSalesforceOAuth(): void {
    // This will be called from DataConnectionStep
    const clientId = process.env.REACT_APP_SALESFORCE_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/salesforce/callback`;
    const state = Math.random().toString(36).substring(7);

    // Store state in sessionStorage for validation
    sessionStorage.setItem('salesforce_oauth_state', state);

    // Build Salesforce OAuth URL
    const oauthUrl = new URL('https://login.salesforce.com/services/oauth2/authorize');
    oauthUrl.searchParams.append('client_id', clientId || '');
    oauthUrl.searchParams.append('redirect_uri', redirectUri);
    oauthUrl.searchParams.append('response_type', 'code');
    oauthUrl.searchParams.append('state', state);
    oauthUrl.searchParams.append('prompt', 'login');

    window.location.href = oauthUrl.toString();
  }

  /**
   * Handle Salesforce OAuth callback
   */
  async handleSalesforceCallback(code: string, state: string): Promise<boolean> {
    try {
      // Verify state
      const savedState = sessionStorage.getItem('salesforce_oauth_state');
      if (savedState !== state) {
        console.error('State mismatch in OAuth callback');
        return false;
      }

      // Exchange code for token (backend handles this)
      const response = await api.post('/auth/salesforce/callback', { code });

      if (response.status === 200) {
        // Mark Salesforce as connected in onboarding
        await this.markSalesforceConnected();
        return true;
      }

      return false;
    } catch (error) {
      console.error('Failed to handle Salesforce callback:', error);
      return false;
    }
  }

  /**
   * Get mock prediction data for first-win step
   * (In production, this would come from real predictions)
   */
  getMockPredictions() {
    return {
      customers_found: 23,
      revenue_at_risk: 427000,
      playbooks_running: 3,
      next_steps: [
        {
          num: 1,
          title: 'Email notifications sent',
          description: 'Your team gets alerted about at-risk customers'
        },
        {
          num: 2,
          title: 'Tasks created in Slack',
          description: 'Follow-up actions appear in your workflow'
        },
        {
          num: 3,
          title: 'You take action',
          description: 'Reach out to customers and prevent churn'
        },
        {
          num: 4,
          title: 'ForecastX learns',
          description: 'Model improves with real outcomes'
        }
      ]
    };
  }
}

export const onboardingService = new OnboardingService();
