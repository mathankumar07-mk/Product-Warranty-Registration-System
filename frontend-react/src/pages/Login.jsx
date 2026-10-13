import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <div className="auth-shell">
        <aside className="auth-visual">
          <div className="brand-pill">Warranty Desk</div>

          <div className="auth-visual-copy">
            <p className="eyebrow">Secure access</p>
            <h1>Welcome back to smarter shopping.</h1>
            <p className="visual-text">
              Track orders, manage warranties, and protect every purchase with a simpler, safer experience.
            </p>
          </div>

          <ul className="feature-list">
            <li>✔ Secure checkout & account protection</li>
            <li>✔ Instant warranty tracking</li>
            <li>✔ Smart order notifications</li>
          </ul>
        </aside>

        <div className="auth-panel">
          <div className="auth-container">
            <div className="auth-header">
              <p className="eyebrow dark">Hello again</p>
              <h2>Sign in</h2>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  disabled={loading}
                />
              </div>

              <div className="auth-row">
                <label className="check-row">
                  <input type="checkbox" />
                  <span>Remember me</span>
                </label>
                <Link to="/forgot-password" className="muted-link">Forgot password?</Link>
              </div>

              <button type="submit" className="btn btn-primary btn-block btn-large" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </button>
            </form>

            <p className="auth-footer">
              Don&apos;t have an account? <Link to="/register">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}