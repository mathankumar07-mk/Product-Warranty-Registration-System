import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminApi } from '../services/api';

const NAV = [
  { to: '/admin/dashboard', label: 'Dashboard' },
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/admins', label: 'Admin Accounts' },
  { to: '/admin/products', label: 'Products' },
  { to: '/admin/categories', label: 'Categories' },
  { to: '/admin/orders', label: 'Orders' },
  { to: '/admin/payments', label: 'Payments' },
  { to: '/admin/invoices', label: 'Purchase Invoices' },
  { to: '/admin/policies', label: 'Warranty Policies' },
  { to: '/admin/registrations', label: 'Warranty Registrations' },
  { to: '/admin/notifications', label: 'Notifications' },
  { to: '/admin/reports', label: 'Reports & Analytics' },
  { to: '/admin/audit-logs', label: 'Audit Logs' },
  { to: '/admin/settings', label: 'Settings' },
];

export default function AdminLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [pwOpen, setPwOpen] = useState(false);
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [pwNotice, setPwNotice] = useState('');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login', { replace: true });
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setPwNotice('');
    if (pwForm.new_password !== pwForm.confirm) {
      setPwNotice('New passwords do not match');
      return;
    }
    try {
      await adminApi.changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password });
      setPwNotice('Password changed');
      setPwForm({ old_password: '', new_password: '', confirm: '' });
    } catch (err) {
      setPwNotice(err.response?.data?.detail || 'Password change failed');
    }
  };

  return (
    <div className={`admin-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <a href="#admin-content" className="skip-link">
        Skip to admin content
      </a>
      <aside className="admin-sidebar" aria-label="Admin section navigation">
        <div className="admin-sidebar-header">
          <span className="admin-brand">Warranty Desk · Admin</span>
          <button
            type="button"
            className="btn btn-outline btn-small"
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
          >
            {collapsed ? '»' : '«'}
          </button>
        </div>
        <nav className="admin-nav" aria-label="Admin pages">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              aria-label={item.label}
              className={({ isActive }) => `admin-nav-link${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
          <button type="button" className="admin-nav-link admin-nav-logout" onClick={handleLogout}>
            Logout
          </button>
        </nav>
      </aside>

      <div className="admin-main">
        <header className="admin-topbar">
          <div className="admin-topbar-title">Admin Console</div>
          <div className="admin-profile">
            <button
              type="button"
              className="admin-profile-btn"
              onClick={() => setMenuOpen((v) => !v)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              {user?.name || user?.email || 'Admin'} ▾
            </button>
            {menuOpen && (
              <div className="admin-profile-menu" role="menu" aria-label="Admin profile menu">
                <div className="admin-profile-meta">
                  <strong>{user?.name}</strong>
                  <span>{user?.email}</span>
                </div>
                <button
                  type="button"
                  className="btn btn-outline btn-small"
                  onClick={() => { setPwOpen((v) => !v); setPwNotice(''); }}
                >
                  {pwOpen ? 'Hide password form' : 'Change password'}
                </button>
                {pwOpen && (
                  <form onSubmit={handlePasswordChange} className="auth-form">
                    {pwNotice && <div className="alert alert-success">{pwNotice}</div>}
                    <div className="form-group">
                      <label htmlFor="admin-old-password">Current password</label>
                      <input
                        id="admin-old-password"
                        type="password"
                        value={pwForm.old_password}
                        onChange={(e) => setPwForm({ ...pwForm, old_password: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="admin-new-password">New password (min 8 chars)</label>
                      <input
                        id="admin-new-password"
                        type="password"
                        value={pwForm.new_password}
                        onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })}
                        required
                        minLength={8}
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="admin-confirm-password">Confirm new password</label>
                      <input
                        id="admin-confirm-password"
                        type="password"
                        value={pwForm.confirm}
                        onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
                        required
                        minLength={8}
                      />
                    </div>
                    <button type="submit" className="btn btn-primary btn-small">Update password</button>
                  </form>
                )}
                <button type="button" className="btn btn-outline btn-small" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </header>
        <main className="admin-content" id="admin-content" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
