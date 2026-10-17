import { useEffect, useState } from 'react';
import { adminApi, warrantyApi } from '../services/api';

const STATUSES = ['PENDING', 'PENDING_REVIEW', 'ACTIVE', 'EXPIRED', 'CANCELLED'];

export default function AdminRegistrations() {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = async () => {
    setError('');
    try {
      const params = {};
      if (status) params.status = status;
      const res = await adminApi.searchWarranties(params);
      let data = res.data;
      if (q.trim()) {
        const needle = q.trim().toLowerCase();
        data = data.filter((r) =>
          String(r.warranty_number || '').toLowerCase().includes(needle)
          || String(r.serial_number || '').toLowerCase().includes(needle)
          || String(r.id).includes(needle)
          || String(r.product_id).includes(needle)
          || String(r.user_id).includes(needle));
      }
      setRows(data);
    } catch {
      setError('Failed to load warranty registrations');
    }
  };

  useEffect(() => { load(); }, [status]);

  const setRegistrationStatus = async (id, next) => {
    try {
      await warrantyApi.updateRegistration(id, { warranty_status: next });
      setNotice(`Registration #${id} → ${next}`);
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Status update failed');
    }
  };

  const exportCsv = async () => {
    try {
      const params = status ? { status } : {};
      const response = await adminApi.exportRegistrationsCsv(params);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'warranty-registrations.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Export failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Warranty Registrations</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="admin-toolbar">
        <input type="search" placeholder="Search number, serial, customer, product…" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && load()} />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="btn btn-primary" onClick={load}>Search</button>
        <button className="btn btn-outline" onClick={exportCsv}>Export CSV</button>
        <span className="muted-link">{rows.length} result(s)</span>
      </div>

      {rows.length === 0 ? (
        <div className="detail-section-card"><p>No registrations found.</p></div>
      ) : (
        <div className="orders-list">
          {rows.map((r) => (
            <div key={r.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{r.warranty_number || `Registration #${r.id}`}</h3>
                  <p className="order-date">
                    Customer #{r.user_id} · Product #{r.product_id} · SN {r.serial_number} ·
                    purchase {new Date(r.purchase_date).toLocaleDateString()} ·
                    {new Date(r.warranty_start_date).toLocaleDateString()} → {new Date(r.warranty_end_date).toLocaleDateString()}
                  </p>
                </div>
                <span className="order-status">{r.warranty_status}</span>
              </div>
              <div className="order-actions">
                <select value="" onChange={(e) => e.target.value && setRegistrationStatus(r.id, e.target.value)}>
                  <option value="">Set status…</option>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
