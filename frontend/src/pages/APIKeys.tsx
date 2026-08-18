import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/api-keys.css';

interface APIKey {
  id: number;
  name: string;
  prefix: string;
  permissions: Record<string, boolean>;
  last_used_at: string | null;
  usage_count: number;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
}

interface CreatedKey extends APIKey {
  secret: string;
}

const APIKeys: React.FC = () => {
  const navigate = useNavigate();
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createdKey, setCreatedKey] = useState<CreatedKey | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchKeys();
  }, [navigate]);

  const fetchKeys = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch('/api/api-keys', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setKeys(await response.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      alert('Please enter a key name');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) return;

    setCreating(true);
    try {
      const response = await fetch('/api/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: newKeyName,
          permissions: { read: true, write: true },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCreatedKey(data);
        setNewKeyName('');
        setShowCreateForm(false);
        await fetchKeys();
      } else {
        alert('Failed to create API key');
      }
    } catch (err) {
      alert('An error occurred');
    } finally {
      setCreating(false);
    }
  };

  const handleRevokeKey = async (keyId: number) => {
    if (!window.confirm('Are you sure you want to revoke this key?')) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`/api/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        await fetchKeys();
      } else {
        alert('Failed to revoke key');
      }
    } catch (err) {
      alert('An error occurred');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard');
  };

  if (loading) {
    return <div className="api-keys loading">Loading...</div>;
  }

  return (
    <div className="api-keys">
      <div className="api-keys-header">
        <h1>API Keys</h1>
        <button onClick={() => setShowCreateForm(!showCreateForm)} className="btn-primary">
          + Create New Key
        </button>
      </div>

      {/* Create Key Form */}
      {showCreateForm && (
        <div className="create-key-form">
          <h2>Create New API Key</h2>
          <div className="form-group">
            <label>Key Name</label>
            <input
              type="text"
              value={newKeyName}
              onChange={e => setNewKeyName(e.target.value)}
              placeholder="e.g., Production API Key"
            />
          </div>
          <div className="form-actions">
            <button onClick={handleCreateKey} className="btn-primary" disabled={creating}>
              {creating ? 'Creating...' : 'Create Key'}
            </button>
            <button onClick={() => setShowCreateForm(false)} className="btn-outline">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Created Key Display */}
      {createdKey && (
        <div className="created-key-alert">
          <h3>API Key Created Successfully!</h3>
          <p className="warning">Save this key securely. You won't be able to see it again.</p>
          <div className="key-display">
            <div className="key-row">
              <span className="key-label">API Key:</span>
              <code className="key-value">{createdKey.secret}</code>
              <button onClick={() => copyToClipboard(createdKey.secret)} className="copy-btn">
                Copy
              </button>
            </div>
          </div>
          <button onClick={() => setCreatedKey(null)} className="btn-secondary">
            Done
          </button>
        </div>
      )}

      {/* API Keys List */}
      <section className="keys-list">
        <h2>Your API Keys</h2>
        {keys.length > 0 ? (
          <table className="keys-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th>Created</th>
                <th>Last Used</th>
                <th>Usage Count</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {keys.map(key => (
                <tr key={key.id}>
                  <td>{key.name}</td>
                  <td>
                    <code>{key.prefix}...</code>
                  </td>
                  <td>{new Date(key.created_at).toLocaleDateString()}</td>
                  <td>{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'Never'}</td>
                  <td>{key.usage_count}</td>
                  <td>
                    <span className={`status-badge ${key.is_active ? 'active' : 'inactive'}`}>
                      {key.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleRevokeKey(key.id)}
                      className="btn-danger-small"
                      disabled={!key.is_active}
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No API keys yet. Create one to get started.</p>
        )}
      </section>

      {/* API Usage Guide */}
      <section className="api-guide">
        <h2>API Usage Example</h2>
        <pre>
          <code>{`
curl https://predictx.com/api/predictions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "model_name",
    "data": {
      "feature1": 1.0,
      "feature2": 2.0
    }
  }'
          `}</code>
        </pre>
      </section>
    </div>
  );
};

export default APIKeys;
