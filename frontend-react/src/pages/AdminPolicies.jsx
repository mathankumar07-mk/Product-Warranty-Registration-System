import { useEffect, useState } from 'react';
import { warrantyApi, productApi, categoryApi } from '../services/api';

export default function AdminPolicies() {
  const [policies, setPolicies] = useState([]);
  const [showInactive, setShowInactive] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ product_id: '', category_id: '', warranty_period_months: 12, terms: '', is_active: true });
  const [editing, setEditing] = useState(null);

  const load = async () => {
    setError('');
    try {
      const params = showInactive ? {} : { is_active: true };
      const res = await warrantyApi.listPolicies(params);
      setPolicies(res.data);
    } catch {
      setError('Failed to load warranty policies');
    }
  };

  useEffect(() => { load(); }, [showInactive]);

  const submit = async (e) => {
    e.preventDefault();
    setNotice('');
    const payload = {
      warranty_period_months: Number(form.warranty_period_months),
      terms: form.terms,
      is_active: form.is_active,
      product_id: form.product_id ? Number(form.product_id) : null,
      category_id: form.category_id ? Number(form.category_id) : null,
    };
    try {
      if (editing) {
        await warrantyApi.updatePolicy(editing.id, {
          warranty_period_months: payload.warranty_period_months,
          terms: payload.terms,
          is_active: payload.is_active,
        });
        setNotice('Policy updated (existing registrations keep their original terms)');
      } else {
        if (!payload.product_id && !payload.category_id) {
          setNotice('Exactly one of product or category must be set');
          return;
        }
        await warrantyApi.createPolicy(payload);
        setNotice('Policy created');
      }
      setForm({ product_id: '', category_id: '', warranty_period_months: 12, terms: '', is_active: true });
      setEditing(null);
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Save failed');
    }
  };

  const toggle = async (p) => {
    try {
      await warrantyApi.updatePolicy(p.id, { is_active: !p.is_active });
      setNotice(`Policy ${!p.is_active ? 'activated' : 'deactivated'}`);
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Update failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Warranty Policies</h1>
        </div>
        <label className="check-row">
          <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
          <span>Show inactive</span>
        </label>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="detail-section-card">
        <h2>{editing ? `Edit policy #${editing.id}` : 'Create policy'}</h2>
        <p className="muted-link">Exactly one of product or category. Edits never rewrite existing customer registrations.</p>
        <form onSubmit={submit} className="auth-form">
          {!editing && (
            <>
              <div className="form-group">
                <label>Product ID (or leave blank for category policy)</label>
                <input type="number" value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Category ID (or leave blank for product policy)</label>
                <input type="number" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} />
              </div>
            </>
          )}
          <div className="form-group">
            <label>Duration (months)</label>
            <input type="number" min={1} value={form.warranty_period_months} onChange={(e) => setForm({ ...form, warranty_period_months: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Terms</label>
            <input value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })} required />
          </div>
          <div className="order-actions">
            <button type="submit" className="btn btn-primary">{editing ? 'Save' : 'Create'}</button>
            {editing && <button type="button" className="btn btn-outline" onClick={() => { setEditing(null); setForm({ product_id: '', category_id: '', warranty_period_months: 12, terms: '', is_active: true }); }}>Cancel</button>}
          </div>
        </form>
      </div>

      {policies.length === 0 ? (
        <div className="detail-section-card"><p>No policies found.</p></div>
      ) : (
        <div className="orders-list">
          {policies.map((p) => (
            <div key={p.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>Policy #{p.id} · {p.warranty_period_months} months</h3>
                  <p className="order-date">
                    {p.product_id ? `Product #${p.product_id}` : `Category #${p.category_id}`} · {p.terms?.slice(0, 80)}
                  </p>
                </div>
                <span className="order-status">{p.is_active ? 'active' : 'inactive'}</span>
              </div>
              <div className="order-actions">
                <button className="btn btn-outline order-action-btn" onClick={() => { setEditing(p); setForm({ product_id: '', category_id: '', warranty_period_months: p.warranty_period_months, terms: p.terms, is_active: p.is_active }); }}>Edit</button>
                <button className="btn btn-outline order-action-btn" onClick={() => toggle(p)}>{p.is_active ? 'Deactivate' : 'Activate'}</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
