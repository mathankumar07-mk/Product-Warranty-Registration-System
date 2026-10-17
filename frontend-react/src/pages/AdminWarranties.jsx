import { useState, useEffect } from 'react';
import { adminApi, warrantyApi } from '../services/api';

const REG_STATUSES = ['PENDING', 'PENDING_REVIEW', 'ACTIVE', 'EXPIRED', 'CANCELLED'];

export default function AdminWarranties() {
  const [registrations, setRegistrations] = useState([]);
  const [status, setStatus] = useState('');
  const [policies, setPolicies] = useState([]);
  const [error, setError] = useState('');
  const [policyForm, setPolicyForm] = useState({ product_id: '', category_id: '', warranty_period_months: '12', terms: '' });

  const load = async () => {
    try {
      const [regRes, polRes] = await Promise.all([
        adminApi.searchWarranties(status ? { status } : {}),
        adminApi.listPolicies(),
      ]);
      setRegistrations(regRes.data);
      setPolicies(polRes.data);
    } catch {
      setError('Failed to load warranties');
    }
  };

  useEffect(() => {
    load();
  }, [status]);

  const handleStatus = async (id, next) => {
    try {
      await warrantyApi.updateRegistration(id, { warranty_status: next });
      await load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Update failed');
    }
  };

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    try {
      await warrantyApi.createPolicy({
        product_id: policyForm.product_id ? Number(policyForm.product_id) : null,
        category_id: policyForm.category_id ? Number(policyForm.category_id) : null,
        warranty_period_months: Number(policyForm.warranty_period_months),
        terms: policyForm.terms,
      });
      setPolicyForm({ product_id: '', category_id: '', warranty_period_months: '12', terms: '' });
      await load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Policy create failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Warranties</h1>
        </div>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {REG_STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="detail-section-card">
        <h2>Registrations ({registrations.length})</h2>
        <div className="checkout-item-list">
          {registrations.map((r) => (
            <div key={r.id} className="checkout-item">
              <div>
                <strong>#{r.id} {r.warranty_number || ''}</strong>
                <span>Product #{r.product_id} · {r.serial_number} · {r.warranty_status}</span>
              </div>
              <select value="" onChange={(e) => e.target.value && handleStatus(r.id, e.target.value)}>
                <option value="">Set status…</option>
                {REG_STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-section-card">
        <h2>Create policy (product- or category-scoped)</h2>
        <form onSubmit={handleCreatePolicy} className="auth-form">
          <div className="form-group">
            <label>Product ID (or category below, not both)</label>
            <input type="number" value={policyForm.product_id} onChange={(e) => setPolicyForm({ ...policyForm, product_id: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Category ID</label>
            <input type="number" value={policyForm.category_id} onChange={(e) => setPolicyForm({ ...policyForm, category_id: e.target.value })} />
          </div>
          <div className="form-group">
            <label>Months</label>
            <input type="number" min="1" value={policyForm.warranty_period_months} onChange={(e) => setPolicyForm({ ...policyForm, warranty_period_months: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Terms</label>
            <input type="text" value={policyForm.terms} onChange={(e) => setPolicyForm({ ...policyForm, terms: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary">Create policy</button>
        </form>
      </div>

      <div className="detail-section-card">
        <h2>Policies ({policies.length})</h2>
        <div className="checkout-item-list">
          {policies.map((p) => (
            <div key={p.id} className="checkout-item">
              <div>
                <strong>Policy #{p.id}</strong>
                <span>
                  {p.product_id ? `Product #${p.product_id}` : `Category #${p.category_id}`} · {p.warranty_period_months} months · {p.is_active ? 'active' : 'inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
