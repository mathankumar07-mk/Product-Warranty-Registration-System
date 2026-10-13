import { useState } from 'react';
import { authApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Account() {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      await authApi.changePassword({ old_password: oldPassword, new_password: newPassword });
      setMessage('Password changed. Other sessions were signed out.');
      setOldPassword('');
      setNewPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Password change failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page account-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Account</p>
          <h1>My profile</h1>
        </div>
      </div>

      <div className="detail-section-card">
        <h2>Profile</h2>
        <div className="detail-meta-list">
          <div>
            <span>Name</span>
            <strong>{user?.name}</strong>
          </div>
          <div>
            <span>Email</span>
            <strong>{user?.email}</strong>
          </div>
          <div>
            <span>Role</span>
            <strong>{user?.role === 'admin' ? 'Administrator' : 'Customer'}</strong>
          </div>
        </div>
      </div>

      {user?.role !== 'admin' && (
        <div className="detail-section-card">
          <h2>Change password</h2>
          {error && <div className="alert alert-error">{error}</div>}
          {message && <div className="alert alert-success">{message}</div>}
          <form onSubmit={handleChangePassword} className="auth-form">
            <div className="form-group">
              <label>Current password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>New password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                disabled={loading}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Change password'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
