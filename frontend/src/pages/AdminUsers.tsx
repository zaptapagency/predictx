import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/admin.css';

interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  is_verified: boolean;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

const AdminUsers: React.FC = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);

  const PAGE_SIZE = 10;

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchUsers();
  }, [navigate, page]);

  const fetchUsers = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`/api/admin/users?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setUsers(data.items);
        setTotal(data.total);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (userId: number) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch(`/api/admin/users/${userId}/toggle-admin`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        fetchUsers();
      } else {
        alert('Failed to toggle admin status');
      }
    } catch (err) {
      alert('An error occurred');
    }
  };

  const filteredUsers = users.filter(
    u =>
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.full_name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return <div className="admin-users loading">Loading...</div>;
  }

  return (
    <div className="admin-users">
      <div className="admin-header">
        <h1>User Management</h1>
        <p>Total users: {total}</p>
      </div>

      <div className="search-box">
        <input
          type="text"
          placeholder="Search by email, username, or name..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="search-input"
        />
      </div>

      <table className="users-table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Username</th>
            <th>Full Name</th>
            <th>Verified</th>
            <th>Active</th>
            <th>Admin</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredUsers.map(user => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>
                <code>{user.username}</code>
              </td>
              <td>{user.full_name}</td>
              <td>
                <span className={`badge ${user.is_verified ? 'verified' : 'unverified'}`}>
                  {user.is_verified ? '✓ Yes' : '✗ No'}
                </span>
              </td>
              <td>
                <span className={`badge ${user.is_active ? 'active' : 'inactive'}`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td>
                <span className={`badge ${user.is_admin ? 'admin' : 'user'}`}>
                  {user.is_admin ? 'Admin' : 'User'}
                </span>
              </td>
              <td>{new Date(user.created_at).toLocaleDateString()}</td>
              <td>
                <button onClick={() => handleToggleAdmin(user.id)} className="btn-small">
                  {user.is_admin ? 'Remove Admin' : 'Make Admin'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button onClick={() => setPage(page - 1)} disabled={page === 0} className="btn-secondary">
          ← Previous
        </button>
        <span className="page-info">
          Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
        </span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={page >= Math.ceil(total / PAGE_SIZE) - 1}
          className="btn-secondary"
        >
          Next →
        </button>
      </div>
    </div>
  );
};

export default AdminUsers;
