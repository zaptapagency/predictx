import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import '../styles/verify.css';

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'form' | 'success' | 'error'>('form');
  const [message, setMessage] = useState('');

  const token = searchParams.get('token');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setMessage('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/auth/password-reset/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: token,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        setStatus('success');
        setMessage('Password reset successfully! Redirecting to login...');
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        const data = await response.json();
        setStatus('error');
        setMessage(data.detail || 'Password reset failed');
      }
    } catch (err) {
      setStatus('error');
      setMessage('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verify-page">
      <div className="verify-container">
        <div className="verify-card">
          {status === 'form' && (
            <>
              <h1>Reset Password</h1>
              <p>Enter your new password below</p>

              <form onSubmit={handleSubmit} className="reset-form">
                <div className="form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                  <small>Minimum 8 characters</small>
                </div>

                <div className="form-group">
                  <label>Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>

                {message && <div className="error-message">{message}</div>}

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </button>
              </form>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="success-icon">✓</div>
              <h1>Password Reset!</h1>
              <p className="success-message">{message}</p>
              <p className="redirect-text">Redirecting to login...</p>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="error-icon">✕</div>
              <h1>Reset Failed</h1>
              <p className="error-message">{message}</p>
              <div className="error-actions">
                <button onClick={() => navigate('/forgot-password')} className="btn-primary">
                  Request New Reset Link
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
