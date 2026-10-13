import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password, phone);
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
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
            <p className="eyebrow">Create your account</p>
            <h1>Start protecting every purchase.</h1>
            <p className="visual-text">
              Join today to track orders, register warranties, and enjoy a smoother, smarter shopping experience.
            </p>
          </div>

          <ul className="feature-list">
            <li>✔ Secure account setup</li>
            <li>✔ Warranty registration in minutes</li>
            <li>✔ Personalized order tracking</li>
          </ul>
        </aside>

        <div className="auth-panel">
          <div className="auth-container">
            <div className="auth-header">
              <p className="eyebrow dark">New here</p>
              <h2>Create account</h2>
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit} className="auth-form">
              <div className="form-group">
                <label htmlFor="name">Full name</label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Smith"
                  required
                  disabled={loading}
                />
              </div>

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
                  placeholder="At least 8 characters"
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone (optional)</label>
                <input
                  type="tel"
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 (555) 123-4567"
                  disabled={loading}
                />
              </div>

              <button type="submit" className="btn btn-primary btn-block btn-large" disabled={loading}>
                {loading ? 'Registering...' : 'Register'}
              </button>
            </form>

            <p className="auth-footer">
              Already have an account? <Link to="/login">Login</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}