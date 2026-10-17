import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminApi } from '../services/api';

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await adminApi.overview();
        setData(response.data);
      } catch {
        setError('Failed to load dashboard metrics');
      }
    };
    load();
  }, []);

  if (error) {
    return (
      <div className="page admin-page">
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page admin-page">
        <div className="loading">Loading dashboard…</div>
      </div>
    );
  }

  const t = data.totals;
  const trendMax = Math.max(1, ...data.sales_trend.slice(-7).map((x) => x.orders));

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Dashboard</h1>
        </div>
        <Link to="/admin/reports" className="btn btn-outline">Reports & analytics</Link>
      </div>

      <div className="admin-cards">
        <div className="admin-stat-card"><span>Customers</span><strong>{t.customers}</strong></div>
        <div className="admin-stat-card"><span>Active products</span><strong>{t.active_products}</strong></div>
        <div className="admin-stat-card"><span>Categories</span><strong>{t.categories}</strong></div>
        <div className="admin-stat-card"><span>Orders</span><strong>{t.orders}</strong></div>
        <div className="admin-stat-card"><span>Total paid</span><strong>${t.total_paid}</strong></div>
        <div className="admin-stat-card"><span>Warranties</span><strong>{t.warranty_registrations}</strong></div>
        <div className="admin-stat-card"><span>Expiring soon</span><strong>{data.expiring_soon_warranties}</strong></div>
      </div>

      <div className="admin-grid-2">
        <div className="detail-section-card">
          <h2>Recent orders</h2>
          {data.recent_orders.length === 0 ? <p>No orders yet.</p> : (
            <ul>
              {data.recent_orders.map((o) => (
                <li key={o.id}>#{o.id} {o.order_number || ''} · {o.status} · ${o.total_amount}</li>
              ))}
            </ul>
          )}
          <Link to="/admin/orders" className="muted-link">Manage orders →</Link>
        </div>
        <div className="detail-section-card">
          <h2>Recent customers</h2>
          {data.recent_users.length === 0 ? <p>No customers yet.</p> : (
            <ul>
              {data.recent_users.map((u) => <li key={u.id}>{u.name} · {u.email}</li>)}
            </ul>
          )}
          <Link to="/admin/users" className="muted-link">Manage users →</Link>
        </div>
      </div>

      <div className="admin-grid-2">
        <div className="detail-section-card">
          <h2>Recent warranties</h2>
          {data.recent_warranties.length === 0 ? <p>No registrations yet.</p> : (
            <ul>
              {data.recent_warranties.map((w) => <li key={w.id}>{w.warranty_number || `#${w.id}`} · {w.status}</li>)}
            </ul>
          )}
          <Link to="/admin/registrations" className="muted-link">Manage warranties →</Link>
        </div>
        <div className="detail-section-card">
          <h2>Sales — last 7 days</h2>
          {data.sales_trend.slice(-7).map((d) => (
            <div key={d.date} className="report-bar-row">
              <span className="report-bar-label">{d.date}</span>
              <div className="report-bar-track">
                <div className="report-bar-fill" style={{ width: `${Math.round((d.orders / trendMax) * 100)}%` }} />
              </div>
              <span className="report-bar-value">{d.orders}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-section-card">
        <h2>Top products</h2>
        {data.top_products.length === 0 ? <p>No sales yet.</p> : (
          <ul>
            {data.top_products.map((p) => <li key={p.product_id}>{p.name}: {p.units_sold} sold · ${p.revenue}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
}
