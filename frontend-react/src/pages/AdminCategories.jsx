import { useEffect, useMemo, useState } from 'react';
import { categoryApi } from '../services/api';

export default function AdminCategories() {
  const [categories, setCategories] = useState([]);
  const [q, setQ] = useState('');
  const [sort, setSort] = useState('name');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ name: '', description: '' });
  const [editing, setEditing] = useState(null);
  const pageSize = 20;

  const load = async () => {
    setError('');
    try {
      const res = await categoryApi.list();
      setCategories(res.data);
    } catch {
      setError('Failed to load categories');
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    let rows = [...categories];
    if (q.trim()) {
      const needle = q.trim().toLowerCase();
      rows = rows.filter((c) => c.name?.toLowerCase().includes(needle) || c.description?.toLowerCase().includes(needle));
    }
    rows.sort((a, b) => sort === 'name'
      ? String(a.name).localeCompare(String(b.name))
      : new Date(b.created_at || 0) - new Date(a.created_at || 0));
    return rows;
  }, [categories, q, sort]);

  const pageRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  const submit = async (e) => {
    e.preventDefault();
    setNotice('');
    try {
      if (editing) {
        await categoryApi.update(editing.id, { name: form.name, description: form.description });
        setNotice('Category updated');
      } else {
        await categoryApi.create({ name: form.name, description: form.description });
        setNotice('Category created');
      }
      setForm({ name: '', description: '' });
      setEditing(null);
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Save failed (names must be unique)');
    }
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Delete category "${name}"? Products linked to it are preserved and the delete will be rejected if in use.`)) return;
    try {
      await categoryApi.delete(id);
      setNotice('Category deleted');
      await load();
    } catch (err) {
      setNotice(err.response?.data?.detail || 'Delete failed: category may have products');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Categories</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="detail-section-card">
        <h2>{editing ? `Edit #${editing.id}` : 'Create category'}</h2>
        <form onSubmit={submit} className="auth-form">
          <div className="form-group">
            <label>Name (unique)</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div className="order-actions">
            <button type="submit" className="btn btn-primary">{editing ? 'Save' : 'Create'}</button>
            {editing && <button type="button" className="btn btn-outline" onClick={() => { setEditing(null); setForm({ name: '', description: '' }); }}>Cancel</button>}
          </div>
        </form>
      </div>

      <div className="admin-toolbar">
        <input type="search" placeholder="Search categories…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} />
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="name">Sort: name</option>
          <option value="recent">Sort: recent</option>
        </select>
      </div>

      {pageRows.length === 0 ? (
        <div className="detail-section-card"><p>No categories found.</p></div>
      ) : (
        <div className="orders-list">
          {pageRows.map((c) => (
            <div key={c.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{c.name} · #{c.id}</h3>
                  <p className="order-date">{c.description || 'No description'}</p>
                </div>
                <span className="order-status">{c.is_active ? 'active' : 'inactive'}</span>
              </div>
              <div className="order-actions">
                <button className="btn btn-outline order-action-btn" onClick={() => { setEditing(c); setForm({ name: c.name, description: c.description || '' }); }}>Edit</button>
                <button className="btn btn-outline order-action-btn" onClick={() => remove(c.id, c.name)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="admin-pagination">
        <button className="btn btn-outline btn-small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Prev</button>
        <span>Page {page} of {Math.max(1, Math.ceil(filtered.length / pageSize))}</span>
        <button className="btn btn-outline btn-small" disabled={page * pageSize >= filtered.length} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </div>
  );
}
