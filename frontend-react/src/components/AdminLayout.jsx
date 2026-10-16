import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

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
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login', { replace: true });
  };

  return (
    <div className={`admin-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <span className="admin-brand">Warranty Desk · Admin</span>
          <button
            type="button"
            className="btn btn-outline btn-small"
            onClick={() => setCollapsed((v) => !v)}
            aria-label="Toggle sidebar"
          >
            {collapsed ? '»' : '«'}
          </button>
        </div>
        <nav className="admin-nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
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
            >
              {user?.name || user?.email || 'Admin'} ▾
            </button>
            {menuOpen && (
              <div className="admin-profile-menu">
                <div className="admin-profile-meta">
                  <strong>{user?.name}</strong>
                  <span>{user?.email}</span>
                </div>
                <button type="button" className="btn btn-outline btn-small" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </header>
        <main className="admin-content">{children}</main>
      </div>
    </div>
  );
}
