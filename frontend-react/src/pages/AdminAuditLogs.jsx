import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';
import AdminPagination from '../components/AdminPagination';

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [action, setAction] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    try {
      const params = { page, page_size: 20 };
      if (action.trim()) params.action = action.trim();
      const res = await adminApi.auditLogs(params);
      setLogs(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load audit logs');
    }
  };

  useEffect(() => { load(); }, [page]);

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Audit Logs</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="admin-toolbar">
        <input type="search" placeholder="Filter by action (e.g. admin.create)…" value={action} onChange={(e) => setAction(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load())} />
        <button className="btn btn-primary" onClick={() => { setPage(1); load(); }}>Filter</button>
      </div>

      {logs.length === 0 ? (
        <div className="detail-section-card"><p>No audit entries yet. Admin creations, activations, and deletions are recorded here.</p></div>
      ) : (
        <div className="orders-list">
          {logs.map((l) => (
            <div key={l.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{l.action} {l.entity_type ? `· ${l.entity_type} #${l.entity_id || ''}` : ''}</h3>
                  <p className="order-date">Admin #{l.admin_id ?? '—'} · {new Date(l.created_at).toLocaleString()}</p>
                  <p>{l.details}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <AdminPagination
        page={page}
        onPrev={() => setPage((p) => Math.max(1, p - 1))}
        onNext={() => setPage((p) => p + 1)}
        hasNext={logs.length >= 20}
      />
    </div>
  );
}
