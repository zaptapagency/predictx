/**
 * Analytics Tracking for ForecastX
 * Tracks: signup, login, predictions, features, churn
 * Sends to: Segment (aggregates to Mixpanel, Amplitude, etc)
 */

import { Analytics } from '@segment/analytics-next'

// Initialize Segment (free tier supports ~1M events/month)
const analytics = Analytics.load({ writeKey: 'SEGMENT_WRITE_KEY' })

// User traits (send once per user)
export const identifyUser = (userId: string, traits: any) => {
  analytics.identify(userId, {
    email: traits.email,
    name: traits.name,
    company: traits.company,
    plan: traits.plan, // free, pro, enterprise
    created_at: traits.created_at,
    vertical: traits.vertical, // churn, fraud, forecasting
  })
}

// EVENT: User signed up
export const trackSignup = (email: string, company: string) => {
  analytics.track('user_signed_up', {
    email,
    company,
    signup_source: 'web', // web, api, mobile
    timestamp: new Date(),
  })
}

// EVENT: User logged in
export const trackLogin = (userId: string, daysSinceSignup: number) => {
  analytics.track('user_logged_in', {
    user_id: userId,
    days_since_signup: daysSinceSignup,
    timestamp: new Date(),
  })
}

// EVENT: User generated first prediction (CRITICAL ACTIVATION)
export const trackFirstPrediction = (userId: string, useCase: string, accuracy: number) => {
  analytics.track('first_prediction_generated', {
    user_id: userId,
    use_case: useCase, // churn, fraud, demand, leads
    accuracy,
    time_to_first_prediction_minutes: 15, // Calculate actual time
    timestamp: new Date(),
  })
}

// EVENT: User generated prediction
export const trackPrediction = (userId: string, useCase: string, accuracy: number, rowsProcessed: number) => {
  analytics.track('prediction_generated', {
    user_id: userId,
    use_case: useCase,
    accuracy: accuracy,
    rows_processed: rowsProcessed,
    timestamp: new Date(),
  })
}

// EVENT: User exported data
export const trackExport = (userId: string, format: 'csv' | 'json', rowCount: number) => {
  analytics.track('data_exported', {
    user_id: userId,
    format,
    row_count: rowCount,
    timestamp: new Date(),
  })
}

// EVENT: User upgraded plan
export const trackUpgrade = (userId: string, fromPlan: string, toPlan: string, price: number) => {
  analytics.track('plan_upgraded', {
    user_id: userId,
    from_plan: fromPlan,
    to_plan: toPlan,
    price,
    revenue: price,
    timestamp: new Date(),
  })
}

// EVENT: User viewed page
export const trackPageView = (userId: string, page: string, properties?: any) => {
  analytics.page(page, {
    user_id: userId,
    ...properties,
    timestamp: new Date(),
  })
}

// EVENT: User performed action
export const trackEvent = (userId: string, event: string, properties?: any) => {
  analytics.track(event, {
    user_id: userId,
    ...properties,
    timestamp: new Date(),
  })
}

// RETENTION: Track daily active users (DAU)
export const trackDailyActive = (userId: string) => {
  analytics.track('daily_active_user', {
    user_id: userId,
    date: new Date().toISOString().split('T')[0],
  })
}

// CHURN: Track user inactive (no login in 7 days)
export const trackUserInactive = (userId: string, daysSinceLastLogin: number) => {
  analytics.track('user_inactive', {
    user_id: userId,
    days_since_last_login: daysSinceLastLogin,
  })
}

// CHURN: Track user cancelled
export const trackCancellation = (userId: string, reason: string, mrr: number) => {
  analytics.track('subscription_cancelled', {
    user_id: userId,
    cancellation_reason: reason,
    mrr_lost: mrr,
    timestamp: new Date(),
  })
}

// CHURN: Track user reactivated
export const trackReactivation = (userId: string, daysInactive: number) => {
  analytics.track('subscription_reactivated', {
    user_id: userId,
    days_inactive: daysInactive,
    timestamp: new Date(),
  })
}

export default analytics
