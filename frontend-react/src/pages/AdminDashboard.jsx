import { useState, useEffect } from 'react';
import { adminApi } from '../services/api';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState('');
  const [broadcast, setBroadcast] = useState({ title: '', message: '' });
  const [broadcastResult, setBroadcastResult] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await adminApi.dashboard();
        setMetrics(response.data);
      } catch (err) {
        setError('Failed to load dashboard metrics');
      }
    };
    load();
  }, []);

  const handleBroadcast = async (e) => {
    e.preventDefault();
    setBroadcastResult('');
    try {
      const response = await adminApi.broadcast(broadcast);
      setBroadcastResult(`Sent to ${response.data.recipients} users.`);
      setBroadcast({ title: '', message: '' });
    } catch (err) {
      setBroadcastResult(err.response?.data?.detail || 'Broadcast failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Dashboard</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {metrics && (
        <div className="detail-section-card">
          <h2>Metrics</h2>
          <div className="detail-meta-list">
            <div>
              <span>Users</span>
              <strong>{metrics.users}</strong>
            </div>
            <div>
              <span>Orders</span>
              <strong>{metrics.orders}</strong>
            </div>
            <div>
              <span>Revenue (paid)</span>
              <strong>${metrics.revenue}</strong>
            </div>
            <div>
              <span>Pending warranties</span>
              <strong>{metrics.pending_warranties}</strong>
            </div>
            <div>
              <span>Low-stock products</span>
              <strong>{metrics.low_stock_products}</strong>
            </div>
          </div>
        </div>
      )}

      <div className="detail-section-card">
        <h2>Broadcast notification</h2>
        {broadcastResult && <div className="alert alert-success">{broadcastResult}</div>}
        <form onSubmit={handleBroadcast} className="auth-form">
          <div className="form-group">
            <label>Title</label>
            <input
              type="text"
              value={broadcast.title}
              onChange={(e) => setBroadcast({ ...broadcast, title: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Message</label>
            <input
              type="text"
              value={broadcast.message}
              onChange={(e) => setBroadcast({ ...broadcast, message: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn btn-primary">Send to all users</button>
        </form>
      </div>
    </div>
  );
}
