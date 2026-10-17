import { useState, useEffect } from 'react';
import { adminApi, orderApi } from '../services/api';

const STATUSES = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);

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
      if (detail?.id === id) await viewDetail(id);
    } catch (err) {
      alert(err.response?.data?.detail || 'Status update failed');
    }
  };

  const viewDetail = async (id) => {
    try {
      const response = await adminApi.getOrder(id);
      setDetail(response.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load order details');
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
              <button className="btn btn-outline order-action-btn" onClick={() => viewDetail(order.id)}>
                View Details
              </button>
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

      {detail && (
        <div className="detail-section-card">
          <h2>Order #{detail.id} {detail.order_number || ''}</h2>
          <p>
            {detail.customer ? `${detail.customer.name} · ${detail.customer.email}` : `User #${orders.find((o) => o.id === detail.id)?.user_id}`} · {detail.status} · ${detail.total_amount}
          </p>
          <h3>Items</h3>
          <ul>
            {detail.items.map((it) => (
              <li key={it.id}>{it.product_name || `Product #${it.product_id}`} × {it.quantity} @ ${it.unit_price}</li>
            ))}
          </ul>
          <h3>Payments</h3>
          {detail.payments.length === 0 ? <p>No payments recorded.</p> : (
            <ul>
              {detail.payments.map((p) => (
                <li key={p.id}>#{p.id} · {p.method} · {p.status} · ${p.amount}</li>
              ))}
            </ul>
          )}
          <h3>Invoice</h3>
          <p>{detail.invoice ? `${detail.invoice.invoice_number} · $${detail.invoice.total_amount}` : 'No invoice yet.'}</p>
          <button className="btn btn-outline btn-small" onClick={() => setDetail(null)}>Close details</button>
        </div>
      )}
    </div>
  );
}
