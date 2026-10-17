import { useEffect, useState } from 'react';
import { adminApi, downloadInvoiceFile } from '../services/api';
import AdminPagination from '../components/AdminPagination';

export default function AdminInvoices() {
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [selected, setSelected] = useState(null);

  const load = async () => {
    setError('');
    try {
      const params = { page, page_size: 20 };
      if (q.trim()) params.q = q.trim();
      const res = await adminApi.invoices(params);
      setInvoices(res.data.items);
      setTotal(res.data.total);
    } catch {
      setError('Failed to load invoices');
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const view = async (id) => {
    try {
      const res = await adminApi.getInvoice(id);
      setSelected(res.data);
    } catch {
      setNotice('Failed to load invoice details');
    }
  };

  const download = async (id, number) => {
    try {
      const res = await adminApi.downloadAdminInvoice(id);
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${number || `invoice-${id}`}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      // Fall back to the customer download helper (same file when permitted).
      try {
        await downloadInvoiceFile(id, number);
      } catch {
        setNotice('Invoice file not available');
      }
    }
  };

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Purchase Invoices</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="admin-toolbar">
        <input
          type="search"
          placeholder="Search invoice number…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load())}
        />
        <button className="btn btn-primary" onClick={() => { setPage(1); load(); }}>Search</button>
        <span className="muted-link">{total} invoice(s)</span>
      </div>

      {invoices.length === 0 ? (
        <div className="detail-section-card"><p>No invoices found.</p></div>
      ) : (
        <div className="orders-list">
          {invoices.map((inv) => (
            <div key={inv.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>{inv.invoice_number} · #{inv.id}</h3>
                  <p className="order-date">Order #{inv.order_id} · {inv.customer_email || `user #${inv.user_id}`}</p>
                </div>
                <span className="order-status">${inv.total_amount}</span>
              </div>
              <div className="order-actions">
                <button className="btn btn-outline order-action-btn" onClick={() => view(inv.id)}>View</button>
                <button className="btn btn-outline order-action-btn" onClick={() => download(inv.id, inv.invoice_number)}>Download</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <AdminPagination
        page={page}
        onPrev={() => setPage((p) => Math.max(1, p - 1))}
        onNext={() => setPage((p) => p + 1)}
        hasNext={invoices.length >= 20}
      />

      {selected && (
        <div className="detail-section-card">
          <h2>{selected.invoice_number}</h2>
          <p>Order #{selected.order_id} · Total ${selected.total_amount} · Tax ${selected.tax_amount}</p>
          {selected.order && (
            <>
              <h3>Order items</h3>
              <ul>
                {selected.order.items.map((it, idx) => (
                  <li key={idx}>Product #{it.product_id} × {it.quantity} @ ${it.unit_price}</li>
                ))}
              </ul>
            </>
          )}
          <div className="order-actions">
            <button className="btn btn-outline" onClick={() => download(selected.id, selected.invoice_number)}>Download / Print</button>
          </div>
        </div>
      )}
    </div>
  );
}
