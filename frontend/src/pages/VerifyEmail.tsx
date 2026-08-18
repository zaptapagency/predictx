import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import '../styles/verify.css';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const userId = searchParams.get('user_id');
      const token = searchParams.get('token');

      if (!userId || !token) {
        setStatus('error');
        setMessage('Invalid verification link');
        return;
      }

      try {
        const response = await fetch('/api/auth/verify-email', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: parseInt(userId),
            token: token,
          }),
        });

        if (response.ok) {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to dashboard...');
          setTimeout(() => {
            navigate('/dashboard');
          }, 3000);
        } else {
          const data = await response.json();
          setStatus('error');
          setMessage(data.detail || 'Verification failed');
        }
      } catch (err) {
        setStatus('error');
        setMessage('An error occurred during verification');
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  return (
    <div className="verify-page">
      <div className="verify-container">
        <div className="verify-card">
          {status === 'loading' && (
            <>
              <div className="loading-spinner"></div>
              <h1>Verifying your email...</h1>
              <p>Please wait while we confirm your email address</p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="success-icon">✓</div>
              <h1>Email Verified!</h1>
              <p className="success-message">{message}</p>
              <p className="redirect-text">Redirecting to dashboard...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="error-icon">✕</div>
              <h1>Verification Failed</h1>
              <p className="error-message">{message}</p>
              <div className="error-actions">
                <button onClick={() => navigate('/login')} className="btn-primary">
                  Back to Login
                </button>
                <p className="resend-text">
                  Didn't receive the email? <a href="#resend">Resend verification link</a>
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
