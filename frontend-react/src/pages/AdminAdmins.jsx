import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

export default function AdminAdmins() {
  const [admins, setAdmins] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  const load = async () => {
    setError('');
    try {
      const res = await adminApi.listAdmins();
      setAdmins(res.data);
    } catch {
      setError('Failed to load administrators');
    }
  };

  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setNotice('');
    try {
      await adminApi.createAdmin(form);
      setNotice('Administrator created');
      setForm({ name: '', email: '', password: '' });
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Create failed');
    }
  };

  const setActive = async (id, isActive, email) => {
    if (!isActive && !window.confirm(`Deactivate admin ${email}?`)) return;
    try {
      await adminApi.setAdminActive(id, isActive);
      setNotice(`Admin ${isActive ? 'activated' : 'deactivated'}`);
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Update failed');
    }
  };

  const remove = async (id, email) => {
    if (!window.confirm(`Delete admin ${email}? The last active administrator is protected.`)) return;
    try {
      await adminApi.deleteAdmin(id);
      setNotice('Admin deleted');
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Delete failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Admin Accounts</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="detail-section-card">
        <h2>Create administrator</h2>
        <p className="muted-link">Only signed-in admins can create admins. No public registration exists.</p>
        <form onSubmit={create} className="auth-form">
          <div className="form-group">
            <label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Password (min 8 chars)</label>
            <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
          </div>
          <button type="submit" className="btn btn-primary">Create admin</button>
        </form>
      </div>

      <div className="orders-list">
        {admins.map((a) => (
          <div key={a.id} className="order-card">
            <div className="order-header">
              <div>
                <h3>{a.name} · #{a.id}</h3>
                <p className="order-date">{a.email}</p>
              </div>
              <span className="order-status">{a.is_active ? 'active' : 'inactive'}</span>
            </div>
            <div className="order-actions">
              <button className="btn btn-outline order-action-btn" onClick={() => setActive(a.id, !a.is_active, a.email)}>
                {a.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button className="btn btn-outline order-action-btn" onClick={() => remove(a.id, a.email)}>Delete</button>
            </div>
          </div>
        ))}
      </div>
      {admins.length === 0 && <div className="detail-section-card"><p>No administrators found.</p></div>}
    </div>
  );
}
