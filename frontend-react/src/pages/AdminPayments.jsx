import { useEffect, useMemo, useState } from 'react';
import { adminApi, paymentApi } from '../services/api';

export default function AdminPayments() {
  const [payments, setPayments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [q, setQ] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = async () => {
    setError('');
    try {
      const res = await adminApi.payments(1, 100);
      setPayments(res.data);
    } catch {
      setError('Failed to load payments');
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    return payments.filter((p) => {
      if (statusFilter && p.status !== statusFilter) return false;
      if (q.trim()) {
        const needle = q.trim().toLowerCase();
        return String(p.order_id).includes(needle)
          || String(p.transaction_id || '').toLowerCase().includes(needle)
          || String(p.id).includes(needle);
      }
      return true;
    });
  }, [payments, statusFilter, q]);

  const refund = async (id) => {
    if (!window.confirm(`Refund payment #${id}? Only completed payments can be refunded.`)) return;
    try {
      await paymentApi.refund(id);
      setNotice(`Payment #${id} refunded`);
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Refund failed for this payment state');
    }
    await load();
  };

  const totals = useMemo(() => {
    const byStatus = {};
    for (const p of filtered) {
      byStatus[p.status] = (byStatus[p.status] || 0) + Number(p.amount || 0);
    }
    return byStatus;
  }, [filtered]);

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Payments</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="detail-section-card">
        <h2>Payment handling</h2>
        <p className="muted-link">
          Simulated/manual payments only — no live gateway charges. Amounts of verified payments
          cannot be edited manually; refunds go through the verified refund flow.
          Full card details are never stored or displayed.
        </p>
        <p>Totals in view: {Object.entries(totals).map(([s, a]) => `${s}: $${a.toFixed(2)}`).join(' · ') || '—'}</p>
      </div>

      <div className="admin-toolbar">
        <input type="search" placeholder="Search order #, payment #, transaction…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="pending">pending</option>
          <option value="completed">completed</option>
          <option value="failed">failed</option>
          <option value="refunded">refunded</option>
        </select>
        <button className="btn btn-primary" onClick={load}>Refresh</button>
      </div>

      {filtered.length === 0 ? (
        <div className="detail-section-card"><p>No payments found.</p></div>
      ) : (
        <div className="orders-list">
          {filtered.map((p) => (
            <div key={p.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>Payment #{p.id} · Order #{p.order_id}</h3>
                  <p className="order-date">{p.method} · {p.transaction_id || 'no transaction ref'} · {new Date(p.created_at).toLocaleString()}</p>
                </div>
                <span className="order-status">{p.status}</span>
              </div>
              <div className="order-details">
                <div><span>Amount</span><strong>${p.amount}</strong></div>
              </div>
              <div className="order-actions">
                <button className="btn btn-outline order-action-btn" onClick={() => refund(p.id)}>Refund</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
