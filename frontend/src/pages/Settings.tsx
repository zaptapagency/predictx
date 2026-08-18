import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/settings.css';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
}

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [tab, setTab] = useState('profile');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchUser();
  }, [navigate]);

  const fetchUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch('/api/users/me', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setUser(await response.json());
      } else {
        navigate('/login');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="settings loading">Loading...</div>;
  }

  if (!user) {
    return <div className="settings error">Failed to load settings</div>;
  }

  return (
    <div className="settings">
      <h1>Settings</h1>

      <div className="settings-tabs">
        <button className={`tab-btn ${tab === 'profile' ? 'active' : ''}`} onClick={() => setTab('profile')}>
          Profile
        </button>
        <button className={`tab-btn ${tab === 'password' ? 'active' : ''}`} onClick={() => setTab('password')}>
          Password
        </button>
        <button className={`tab-btn ${tab === 'preferences' ? 'active' : ''}`} onClick={() => setTab('preferences')}>
          Preferences
        </button>
      </div>

      {tab === 'profile' && <ProfileTab user={user} onUpdate={fetchUser} />}
      {tab === 'password' && <PasswordTab />}
      {tab === 'preferences' && <PreferencesTab />}
    </div>
  );
};

interface ProfileTabProps {
  user: User;
  onUpdate: () => void;
}

const ProfileTab: React.FC<ProfileTabProps> = ({ user, onUpdate }) => {
  const [fullName, setFullName] = useState(user.full_name);
  const [username, setUsername] = useState(user.username);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch('/api/users/me', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: fullName,
          username: username,
        }),
      });

      if (response.ok) {
        setMessage('Profile updated successfully');
        onUpdate();
        setTimeout(() => setMessage(''), 3000);
      } else {
        const data = await response.json();
        setMessage(data.detail || 'Update failed');
      }
    } catch (err) {
      setMessage('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-section">
      <h2>Profile Information</h2>
      {message && <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>{message}</div>}

      <form onSubmit={handleSubmit} className="settings-form">
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={user.email} disabled className="input-disabled" />
          <small>Email cannot be changed</small>
        </div>

        <div className="form-group">
          <label>Full Name</label>
          <input
            type="text"
            value={fullName}
            onChange={e => setFullName(e.target.value)}
            placeholder="John Doe"
            required
          />
        </div>

        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="johndoe"
            required
          />
        </div>

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </button>
      </form>
    </div>
  );
};

const PasswordTab: React.FC = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

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

    const token = localStorage.getItem('access_token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch('/api/users/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        setMessage('Password changed successfully');
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => setMessage(''), 3000);
      } else {
        const data = await response.json();
        setMessage(data.detail || 'Failed to change password');
      }
    } catch (err) {
      setMessage('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-section">
      <h2>Change Password</h2>
      {message && <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>{message}</div>}

      <form onSubmit={handleSubmit} className="settings-form">
        <div className="form-group">
          <label>Current Password</label>
          <input
            type="password"
            value={oldPassword}
            onChange={e => setOldPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>

        <div className="form-group">
          <label>New Password</label>
          <input
            type="password"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
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

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Updating...' : 'Change Password'}
        </button>
      </form>
    </div>
  );
};

const PreferencesTab: React.FC = () => {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [usageAlerts, setUsageAlerts] = useState(true);
  const [message, setMessage] = useState('');

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage('Preferences saved successfully');
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <div className="settings-section">
      <h2>Preferences</h2>
      {message && <div className="message success">{message}</div>}

      <form onSubmit={handleSave} className="settings-form">
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={emailNotifications}
              onChange={e => setEmailNotifications(e.target.checked)}
            />
            <span>Receive email notifications</span>
          </label>
          <small>Get notified about important account events</small>
        </div>

        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={usageAlerts}
              onChange={e => setUsageAlerts(e.target.checked)}
            />
            <span>Usage limit alerts</span>
          </label>
          <small>Alert me when I'm near my plan limits</small>
        </div>

        <button type="submit" className="btn-primary">
          Save Preferences
        </button>
      </form>
    </div>
  );
};

export default Settings;
