import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

function Bar({ label, value, max }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="report-bar-row">
      <span className="report-bar-label">{label}</span>
      <div className="report-bar-track"><div className="report-bar-fill" style={{ width: `${pct}%` }} /></div>
      <span className="report-bar-value">{value}</span>
    </div>
  );
}

export default function AdminReports() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    adminApi.reports().then((res) => setData(res.data)).catch(() => setError('Failed to load reports'));
  }, []);

  if (error) return <div className="page admin-page"><div className="alert alert-error">{error}</div></div>;
  if (!data) return <div className="page admin-page"><div className="loading">Loading reports…</div></div>;

  const trendMax = Math.max(1, ...data.sales_trend.map((t) => t.orders));
  const topMax = Math.max(1, ...data.top_products.map((p) => p.units_sold));

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Reports & Analytics</h1>
        </div>
      </div>

      <div className="admin-cards">
        <div className="admin-stat-card"><span>Customers</span><strong>{data.overview.totals.customers}</strong></div>
        <div className="admin-stat-card"><span>Orders</span><strong>{data.overview.totals.orders}</strong></div>
        <div className="admin-stat-card"><span>Total paid</span><strong>${data.overview.totals.total_paid}</strong></div>
        <div className="admin-stat-card"><span>Warranties</span><strong>{data.overview.totals.warranty_registrations}</strong></div>
        <div className="admin-stat-card"><span>Policies</span><strong>{data.policy_count}</strong></div>
      </div>

      <div className="detail-section-card">
        <h2>Sales trend (last 15 days, orders)</h2>
        {data.sales_trend.map((t) => (
          <Bar key={t.date} label={`${t.date} ($${t.revenue})`} value={t.orders} max={trendMax} />
        ))}
        {data.sales_trend.every((t) => t.orders === 0) && <p className="muted-link">No orders in this period.</p>}
      </div>

      <div className="detail-section-card">
        <h2>Top products by units sold</h2>
        {data.top_products.length === 0 ? <p>No sales yet.</p> : data.top_products.map((p) => (
          <Bar key={p.product_id} label={`${p.name} ($${p.revenue})`} value={p.units_sold} max={topMax} />
        ))}
      </div>

      <div className="detail-section-card">
        <h2>Orders by status</h2>
        <ul>{Object.entries(data.overview.orders_by_status).map(([s, c]) => <li key={s}>{s}: {c}</li>)}</ul>
        <h2>Payments by status</h2>
        <ul>{Object.entries(data.overview.payments_by_status).map(([s, v]) => <li key={s}>{s}: {v.count} × ${v.amount}</li>)}</ul>
        <h2>Warranties by status</h2>
        <ul>{Object.entries(data.overview.warranties_by_status).map(([s, c]) => <li key={s}>{s}: {c}</li>)}</ul>
        <h2>Payment methods</h2>
        <ul>{data.payment_methods.map((m, i) => <li key={i}>{m.method}: {m.count} × ${m.amount}</li>)}</ul>
        <h2>Categories</h2>
        <ul>{data.categories.map((c) => <li key={c.id}>{c.name}: {c.products} products</li>)}</ul>
      </div>
    </div>
  );
}
