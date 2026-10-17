import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';
import AdminPagination from '../components/AdminPagination';

export default function AdminNotifications() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [readFilter, setReadFilter] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [broadcast, setBroadcast] = useState({ title: '', message: '' });

  const load = async () => {
    setError('');
    try {
      const params = { page, page_size: 20 };
      if (typeFilter) params.type = typeFilter;
      if (readFilter === 'read') params.is_read = true;
      if (readFilter === 'unread') params.is_read = false;
      const res = await adminApi.adminNotifications(params);
      setItems(res.data.items);
      setTotal(res.data.total);
    } catch {
      setError('Failed to load notifications');
    }
  };

  useEffect(() => { load(); }, [page, typeFilter, readFilter]);

  const send = async (e) => {
    e.preventDefault();
    try {
      const res = await adminApi.broadcast(broadcast);
      setNotice(`Broadcast sent to ${res.data.recipients} users`);
      setBroadcast({ title: '', message: '' });
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Broadcast failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Notifications</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="detail-section-card">
        <h2>Broadcast to all active users</h2>
        <form onSubmit={send} className="auth-form">
          <div className="form-group">
            <label>Title</label>
            <input value={broadcast.title} onChange={(e) => setBroadcast({ ...broadcast, title: e.target.value })} required maxLength={120} />
          </div>
          <div className="form-group">
            <label>Message</label>
            <input value={broadcast.message} onChange={(e) => setBroadcast({ ...broadcast, message: e.target.value })} required maxLength={1000} />
          </div>
          <button type="submit" className="btn btn-primary">Send broadcast</button>
        </form>
      </div>

      <div className="admin-toolbar">
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}>
          <option value="">All types</option>
          <option value="order">order</option>
          <option value="payment">payment</option>
          <option value="warranty">warranty</option>
          <option value="general">general</option>
        </select>
        <select value={readFilter} onChange={(e) => { setReadFilter(e.target.value); setPage(1); }}>
          <option value="">Read + unread</option>
          <option value="unread">Unread</option>
          <option value="read">Read</option>
        </select>
        <span className="muted-link">{total} notification(s)</span>
      </div>

      {items.length === 0 ? (
        <div className="detail-section-card"><p>No notifications found.</p></div>
      ) : (
        <div className="orders-list">
          {items.map((n) => (
            <div key={n.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{n.title}</h3>
                  <p className="order-date">User #{n.user_id} · {n.type} · {new Date(n.created_at).toLocaleString()}</p>
                  <p>{n.message}</p>
                </div>
                <span className="order-status">{n.is_read ? 'read' : 'unread'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <AdminPagination
        page={page}
        onPrev={() => setPage((p) => Math.max(1, p - 1))}
        onNext={() => setPage((p) => p + 1)}
        hasNext={items.length >= 20}
      />
    </div>
  );
}
