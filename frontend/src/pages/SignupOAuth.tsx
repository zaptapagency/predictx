import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGoogleLogin } from '@react-oauth/google'
import '../styles/auth.css'

interface SignupState {
  loading: boolean
  error: string
  step: 'choice' | 'processing' | 'success'
}

const SignupOAuth: React.FC = () => {
  const navigate = useNavigate()
  const [state, setState] = useState<SignupState>({
    loading: false,
    error: '',
    step: 'choice',
  })

  // ============================================================================
  // GOOGLE OAUTH LOGIN
  // ============================================================================
  const googleLogin = useGoogleLogin({
    onSuccess: async (codeResponse) => {
      setState(prev => ({ ...prev, loading: true, step: 'processing' }))
      try {
        const response = await fetch('/api/auth/oauth/google', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ credential: (codeResponse as any).credential }),
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || 'OAuth failed')
        }

        const data = await response.json()

        // Store tokens
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        localStorage.setItem('organization', JSON.stringify(data.organization))

        setState(prev => ({ ...prev, step: 'success' }))

        // Redirect to onboarding dashboard
        setTimeout(() => {
          navigate('/onboarding/sample-prediction')
        }, 500)
      } catch (err: any) {
        setState(prev => ({
          ...prev,
          error: err.message || 'Sign up failed. Please try again.',
          loading: false,
        }))
      }
    },
    onError: () => {
      setState(prev => ({
        ...prev,
        error: 'Google sign-in failed. Please try again.',
        loading: false,
      }))
    },
    flow: 'implicit',
  })

  // ============================================================================
  // MICROSOFT OAUTH LOGIN
  // ============================================================================
  const handleMicrosoftLogin = async () => {
    setState(prev => ({ ...prev, loading: true, step: 'processing' }))
    try {
      // Microsoft OAuth flow (simplified)
      const clientId = process.env.REACT_APP_MICROSOFT_CLIENT_ID
      const redirectUri = `${window.location.origin}/auth/callback/microsoft`
      const scope = 'openid profile email'

      const authUrl = new URL('https://login.microsoftonline.com/common/oauth2/v2.0/authorize')
      authUrl.searchParams.append('client_id', clientId || '')
      authUrl.searchParams.append('redirect_uri', redirectUri)
      authUrl.searchParams.append('response_type', 'code')
      authParams.append('scope', scope)

      window.location.href = authUrl.toString()
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: 'Microsoft sign-in setup failed.',
        loading: false,
      }))
    }
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  if (state.step === 'success') {
    return (
      <div className="auth-container">
        <div className="auth-box auth-success">
          <div className="success-animation">
            <div className="spinner"></div>
          </div>
          <h2>Welcome! 🎉</h2>
          <p>Setting up your dashboard...</p>
          <p className="meta">Redirecting to your first prediction</p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-container">
      <div className="auth-box signup-box">
        {/* HEADER */}
        <div className="auth-header">
          <h1>ForecastX</h1>
          <h2>Predict Customer Churn in 2 Minutes</h2>
          <p className="tagline">See which customers you're about to lose</p>
        </div>

        {/* ERROR MESSAGE */}
        {state.error && (
          <div className="error-message" role="alert">
            <span className="error-icon">⚠️</span>
            <span>{state.error}</span>
          </div>
        )}

        {/* OAUTH BUTTONS */}
        <div className="oauth-section">
          <button
            className="oauth-button google-button"
            onClick={() => googleLogin()}
            disabled={state.loading}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 11c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm0-2c-.551 0-1-.449-1-1s.449-1 1-1 1 .449 1 1-.449 1-1 1z" />
            </svg>
            <span>
              {state.loading ? 'Signing in...' : 'Sign in with Google'}
            </span>
          </button>

          <button
            className="oauth-button microsoft-button"
            onClick={handleMicrosoftLogin}
            disabled={state.loading}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M3 3h9v9H3V3zm10 0h9v9h-9V3zM3 14h9v9H3v-9zm10 0h9v9h-9v-9z" />
            </svg>
            <span>
              {state.loading ? 'Signing in...' : 'Sign in with Microsoft'}
            </span>
          </button>
        </div>

        {/* DIVIDER */}
        <div className="auth-divider">
          <span>or</span>
        </div>

        {/* REGULAR SIGNUP FORM (fallback) */}
        <div className="email-signup">
          <a href="/auth/signup-email" className="link-button">
            Sign up with email
          </a>
        </div>

        {/* FEATURES */}
        <div className="auth-features">
          <div className="feature">
            <div className="feature-icon">⚡</div>
            <div>
              <h4>Instant Setup</h4>
              <p>No password needed. Sign in with your work email.</p>
            </div>
          </div>
          <div className="feature">
            <div className="feature-icon">📊</div>
            <div>
              <h4>See Results Now</h4>
              <p>Analyze sample data in seconds. No upload required.</p>
            </div>
          </div>
          <div className="feature">
            <div className="feature-icon">🔗</div>
            <div>
              <h4>Connect Real Data</h4>
              <p>Link Salesforce, Stripe, or upload CSV when ready.</p>
            </div>
          </div>
        </div>

        {/* LOGIN LINK */}
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <a href="/login" className="link">
              Sign in
            </a>
          </p>
        </div>
      </div>

      {/* SOCIAL PROOF */}
      <div className="auth-social-proof">
        <p>✨ Join 500+ SaaS companies predicting churn</p>
        <div className="companies">
          <span className="company">Acme Corp</span>
          <span className="company">TechCorp</span>
          <span className="company">StartupXYZ</span>
          <span className="company">+497 more</span>
        </div>
      </div>
    </div>
  )
}

export default SignupOAuth
