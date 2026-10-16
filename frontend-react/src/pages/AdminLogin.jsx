import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function AdminLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { adminLogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await adminLogin(email, password);
      navigate('/admin/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || err.response?.data?.detail || 'Admin login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <div className="auth-shell">
        <aside className="auth-visual">
          <div className="brand-pill">Warranty Desk · Admin</div>
          <div className="auth-visual-copy">
            <p className="eyebrow">Restricted area</p>
            <h1>Admin console access.</h1>
            <p className="visual-text">
              Authorized administrators only. All admin activity is authenticated
              with JWT access tokens and recorded in audit logs.
            </p>
          </div>
          <ul className="feature-list">
            <li>✔ JWT-verified admin sessions</li>
            <li>✔ Customer accounts cannot access this area</li>
            <li>✔ Audited admin actions</li>
          </ul>
        </aside>

        <div className="auth-panel">
          <div className="auth-container">
            <div className="auth-header">
              <p className="eyebrow dark">Admin login</p>
              <h2>Sign in as administrator</h2>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="admin-email">Admin email</label>
                <input
                  type="email"
                  id="admin-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@example.com"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="admin-password">Password</label>
                <input
                  type="password"
                  id="admin-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  required
                  disabled={loading}
                />
              </div>
              <button type="submit" className="btn btn-primary btn-block btn-large" disabled={loading}>
                {loading ? 'Verifying…' : 'Login to admin console'}
              </button>
            </form>

            <p className="auth-footer">
              Customer account? <Link to="/login">Sign in here</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
