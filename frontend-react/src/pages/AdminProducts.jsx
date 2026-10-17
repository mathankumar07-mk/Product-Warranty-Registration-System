import { useState, useEffect } from 'react';
import { productApi, categoryApi, adminApi } from '../services/api';

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [form, setForm] = useState({
    category_id: '',
    name: '',
    description: '',
    price: '',
    stock_quantity: '0',
    brand: '',
    model_number: '',
  });
  const [categoryName, setCategoryName] = useState('');
  const [importFile, setImportFile] = useState(null);

  const load = async () => {
    try {
      const [productRes, categoryRes] = await Promise.all([
        productApi.list(),
        categoryApi.list(),
      ]);
      const data = productRes.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
      setCategories(Array.isArray(categoryRes.data) ? categoryRes.data : []);
    } catch {
      setError('Failed to load catalogue');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    try {
      await productApi.create({
        category_id: Number(form.category_id),
        name: form.name,
        description: form.description || null,
        price: Number(form.price),
        stock_quantity: Number(form.stock_quantity),
        brand: form.brand,
        model_number: form.model_number,
      });
      setInfo('Product created.');
      setForm({ category_id: '', name: '', description: '', price: '', stock_quantity: '0', brand: '', model_number: '' });
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Create failed');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Deactivate this product?')) return;
    try {
      await productApi.delete(id);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed');
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    try {
      await categoryApi.create({ name: categoryName });
      setCategoryName('');
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Category create failed');
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    if (!importFile) return;
    setError('');
    setInfo('');
    try {
      const response = await adminApi.importProducts(importFile);
      const { created, skipped, errors } = response.data;
      setInfo(`Imported: ${created} created, ${skipped} skipped, ${errors.length} errors.`);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Import failed');
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Products & categories</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {info && <div className="alert alert-success">{info}</div>}

      <div className="detail-section-card">
        <h2>Add product</h2>
        <form onSubmit={handleCreate} className="auth-form">
          <div className="form-group">
            <label>Category</label>
            <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} required>
              <option value="">Select…</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Name</label>
            <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Model number</label>
            <input type="text" value={form.model_number} onChange={(e) => setForm({ ...form, model_number: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Brand</label>
            <input type="text" value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Price</label>
            <input type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Stock</label>
            <input type="number" min="0" value={form.stock_quantity} onChange={(e) => setForm({ ...form, stock_quantity: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input type="text" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary">Create product</button>
        </form>
      </div>

      <div className="detail-section-card">
        <h2>Add category</h2>
        <form onSubmit={handleCreateCategory} className="auth-form">
          <div className="form-group">
            <label>Name</label>
            <input type="text" value={categoryName} onChange={(e) => setCategoryName(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-outline">Create category</button>
        </form>
      </div>

      <div className="detail-section-card">
        <h2>CSV import</h2>
        <form onSubmit={handleImport} className="auth-form">
          <div className="form-group">
            <label>Columns: name, model_number, price, stock_quantity, brand, category_id</label>
            <input type="file" accept=".csv" onChange={(e) => setImportFile(e.target.files?.[0] || null)} />
          </div>
          <button type="submit" className="btn btn-outline">Import CSV</button>
        </form>
      </div>

      <div className="detail-section-card">
        <h2>Products ({products.length})</h2>
        <div className="checkout-item-list">
          {products.map((p) => (
            <div key={p.id} className="checkout-item">
              <div>
                <strong>{p.name}</strong>
                <span>{p.brand} · {p.model_number} · stock {p.stock_quantity} · ${p.price}</span>
              </div>
              <button onClick={() => handleDelete(p.id)} className="btn btn-outline btn-sm">
                Deactivate
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
