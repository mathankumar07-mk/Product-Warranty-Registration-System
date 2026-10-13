import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminApi, orderApi } from '../services/api';

const STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const params = status ? { status } : {};
      const response = await adminApi.orders(params);
      setOrders(response.data);
    } catch (err) {
      setError('Failed to load orders');
    }
  };

  useEffect(() => {
    load();
  }, [status]);

  const handleStatus = async (id, next) => {
    try {
      await orderApi.update(id, { status: next });
      await load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Status update failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Orders</h1>
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="orders-list">
        {orders.map((order) => (
          <div key={order.id} className="order-card">
            <div className="order-header">
              <div>
                <h3>Order #{order.id}{order.order_number ? ` · ${order.order_number}` : ''}</h3>
                <p className="order-date">User #{order.user_id} · {new Date(order.created_at).toLocaleString()}</p>
              </div>
              <span className="order-status">{order.status}</span>
            </div>
            <div className="order-details">
              <div>
                <span>Total</span>
                <strong>${order.total_amount}</strong>
              </div>
              <div>
                <span>Items</span>
                <strong>{order.items?.length || 0}</strong>
              </div>
            </div>
            <div className="order-actions">
              <Link to={`/orders/${order.id}`} className="btn btn-outline order-action-btn">
                View Details
              </Link>
              <select
                value=""
                onChange={(e) => e.target.value && handleStatus(order.id, e.target.value)}
              >
                <option value="">Set status…</option>
                {STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
