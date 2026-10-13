import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authApi } from '../services/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState('');

  const handleForgot = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      const response = await authApi.forgotPassword({ email });
      if (response.data.email_sent) {
        setMessage('Reset instructions were sent to your email.');
      } else if (response.data.reset_token) {
        setResetToken(response.data.reset_token);
        setMessage('Use the token below to set a new password.');
      } else {
        setMessage('If the account exists, reset instructions were sent.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);
    try {
      await authApi.resetPassword({ token: token || resetToken, new_password: newPassword });
      setMessage('Password reset successfully. You can now login.');
      setToken('');
      setResetToken('');
      setNewPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed');
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
            <p className="eyebrow">Account recovery</p>
            <h1>Reset your password.</h1>
            <p className="visual-text">Enter your email to get a reset token, then set a new password.</p>
          </div>
        </aside>

        <div className="auth-panel">
          <div className="auth-container">
            <div className="auth-header">
              <p className="eyebrow dark">Forgot password</p>
              <h2>Recover access</h2>
            </div>

            {error && <div className="alert alert-error">{error}</div>}
            {message && <div className="alert alert-success">{message}</div>}

            <form onSubmit={handleForgot} className="auth-form">
              <div className="form-group">
                <label htmlFor="fp-email">Email</label>
                <input
                  type="email"
                  id="fp-email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  disabled={loading}
                />
              </div>
              <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                {loading ? 'Sending...' : 'Send reset token'}
              </button>
            </form>

            <form onSubmit={handleReset} className="auth-form">
              <div className="form-group">
                <label htmlFor="fp-token">Reset token</label>
                <input
                  type="text"
                  id="fp-token"
                  value={token || resetToken}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste reset token"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="fp-password">New password</label>
                <input
                  type="password"
                  id="fp-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>
              <button type="submit" className="btn btn-outline btn-block" disabled={loading}>
                {loading ? 'Resetting...' : 'Set new password'}
              </button>
            </form>

            <p className="auth-footer">
              Remembered it? <Link to="/login">Back to login</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
