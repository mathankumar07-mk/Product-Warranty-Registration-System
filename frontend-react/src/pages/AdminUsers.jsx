import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, page_size: 20 };
      if (q.trim()) params.q = q.trim();
      if (statusFilter === 'active') params.is_active = true;
      if (statusFilter === 'inactive') params.is_active = false;
      const res = await adminApi.searchUsers(params);
      setUsers(res.data);
    } catch {
      setError('Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

  const viewDetail = async (id) => {
    setNotice('');
    try {
      const res = await adminApi.getUser(id);
      setSelected(res.data);
    } catch {
      setNotice('Failed to load customer details');
    }
  };

  const setActive = async (id, isActive) => {
    try {
      await adminApi.setUserActive(id, isActive);
      setNotice(`Customer ${isActive ? 'activated' : 'deactivated'}`);
      await load();
      if (selected?.id === id) await viewDetail(id);
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Status update failed');
    }
  };

  const remove = async (id, email) => {
    if (!window.confirm(`Delete customer ${email}? Only allowed when no orders/warranties exist. Deactivation is preferred.`)) return;
    try {
      await adminApi.deleteUser(id);
      setNotice('Customer deleted');
      setSelected(null);
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
          <h1>Users</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Search name, email, phone…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load())}
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <button className="btn btn-primary" onClick={() => { setPage(1); load(); }}>Search</button>
      </div>

      {loading ? (
        <div className="loading">Loading customers…</div>
      ) : users.length === 0 ? (
        <div className="detail-section-card"><p>No customers found.</p></div>
      ) : (
        <div className="orders-list">
          {users.map((u) => (
            <div key={u.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{u.name} · #{u.id}</h3>
                  <p className="order-date">{u.email}{u.phone ? ` · ${u.phone}` : ''}</p>
                </div>
                <span className="order-status">{u.is_active ? 'active' : 'inactive'}</span>
              </div>
              <div className="order-actions">
                <button className="btn btn-outline order-action-btn" onClick={() => viewDetail(u.id)}>View</button>
                <button className="btn btn-outline order-action-btn" onClick={() => setActive(u.id, !u.is_active)}>
                  {u.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button className="btn btn-outline order-action-btn" onClick={() => remove(u.id, u.email)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="admin-pagination">
        <button className="btn btn-outline btn-small" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</button>
        <span>Page {page}</span>
        <button className="btn btn-outline btn-small" disabled={users.length < 20} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>

      {selected && (
        <div className="detail-section-card">
          <h2>Customer #{selected.id} — {selected.name}</h2>
          <p>{selected.email} · {selected.is_active ? 'Active' : 'Inactive'}</p>
          <h3>Orders ({selected.orders?.length || 0})</h3>
          {selected.orders?.length === 0 ? <p>No orders.</p> : (
            <ul>{selected.orders.map((o) => <li key={o.id}>#{o.id} {o.order_number || ''} · {o.status} · ${o.total_amount}</li>)}</ul>
          )}
          <h3>Invoices ({selected.invoices?.length || 0})</h3>
          {selected.invoices?.length === 0 ? <p>No invoices.</p> : (
            <ul>{selected.invoices.map((i) => <li key={i.id}>{i.invoice_number} · order #{i.order_id} · ${i.total_amount}</li>)}</ul>
          )}
          <h3>Warranties ({selected.warranties?.length || 0})</h3>
          {selected.warranties?.length === 0 ? <p>No warranties.</p> : (
            <ul>{selected.warranties.map((w) => <li key={w.id}>{w.warranty_number || `#${w.id}`} · {w.status}</li>)}</ul>
          )}
        </div>
      )}
    </div>
  );
}
