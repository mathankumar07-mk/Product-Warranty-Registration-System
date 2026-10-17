import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { warrantyApi, invoiceApi, orderApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Warranties() {
  const { isAuthenticated, isAdmin } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [policiesLoading, setPoliciesLoading] = useState(false);
  // User's own invoices with the product IDs each order contains.
  const [invoices, setInvoices] = useState([]);
  const [invoicesLoading, setInvoicesLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    policy_id: '',
    product_id: '',
    serial_number: '',
    purchase_invoice_id: '',
    purchase_source: 'Company Website',
    proof_reference: '',
    purchase_date: new Date().toISOString().slice(0, 16),
  });

  useEffect(() => {
    if (isAuthenticated) {
      loadRegistrations();
    }
  }, [isAuthenticated]);

  const [statusFilter, setStatusFilter] = useState('');

  const loadRegistrations = async (status = statusFilter) => {
    try {
      const params = status ? { status } : {};
      const response = await warrantyApi.listRegistrations(params);
      setRegistrations(response.data);
    } catch {
      setError('Failed to load registrations');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusFilter = (value) => {
    setStatusFilter(value);
    setLoading(true);
    loadRegistrations(value);
  };

  const loadPolicies = async () => {
    setPoliciesLoading(true);
    try {
      const response = await warrantyApi.listPolicies();
      setPolicies(response.data);
    } catch {
      setError('Failed to load warranty policies');
    } finally {
      setPoliciesLoading(false);
    }
  };

  const openRegister = () => {
    setShowRegister(true);
    loadPolicies();
    loadInvoices();
  };

  const loadInvoices = async () => {
    setInvoicesLoading(true);
    try {
      const response = await invoiceApi.list();
      const withItems = await Promise.all(
        response.data.map(async (inv) => {
          try {
            const order = await orderApi.get(inv.order_id);
            const items = order.data.items || [];
            return {
              ...inv,
              productIds: items.map((item) => item.product_id),
              productNames: [...new Set(items.map((item) => item.product?.name || `Product #${item.product_id}`))],
            };
          } catch {
            return { ...inv, productIds: [], productNames: [] };
          }
        })
      );
      setInvoices(withItems);
    } catch {
      setError('Failed to load your invoices');
    } finally {
      setInvoicesLoading(false);
    }
  };

  // Invoices shown for the currently selected product. Picking from this list
  // makes "invoice does not contain the product" impossible by construction.
  const matchingInvoices = registerForm.product_id
    ? invoices.filter((inv) => inv.productIds.includes(Number(registerForm.product_id)))
    : invoices;

  const invoiceLabel = (inv) =>
    `${inv.invoice_number} · ${(inv.productNames || []).join(', ') || `Order #${inv.order_id}`}`;

  const handlePolicyChange = (policyId) => {
    const policy = policies.find((p) => String(p.id) === String(policyId));
    setRegisterForm((prev) => ({
      ...prev,
      policy_id: policyId,
      // A policy covers exactly one product (or one category); prefill it so
      // the registration can never mismatch the policy.
      product_id: policy?.product_id ? String(policy.product_id) : prev.product_id,
    }));
  };

  const policyLabel = (policy) => {
    const scope = policy.product_id
      ? `Product #${policy.product_id}`
      : `Category #${policy.category_id}`;
    return `#${policy.id} · ${scope} · ${policy.warranty_period_months} months`;
  };

  // Invoices have text numbers (INV-…) but the API links by internal integer
  // ID. Accept either: digits go through as an ID, anything else is resolved
  // via GET /invoices/by-number/ before submitting.
  const resolveInvoiceId = async (raw) => {
    const value = raw.trim();
    if (!value) return null;
    if (/^\d+$/.test(value)) return Number(value);
    try {
      const response = await invoiceApi.getByNumber(value);
      return response.data.id;
    } catch {
      throw new Error(`Invoice "${value}" was not found on your orders.`);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const payload = {
        policy_id: Number(registerForm.policy_id),
        product_id: Number(registerForm.product_id),
        serial_number: registerForm.serial_number.trim(),
        purchase_source: registerForm.purchase_source,
        purchase_date: new Date(registerForm.purchase_date).toISOString(),
      };
      const invoiceId = await resolveInvoiceId(registerForm.purchase_invoice_id);
      if (invoiceId !== null) {
        payload.purchase_invoice_id = invoiceId;
      }
      if (registerForm.proof_reference.trim()) {
        payload.proof_reference = registerForm.proof_reference.trim();
      }
      await warrantyApi.register(payload);
      setShowRegister(false);
      setRegisterForm({
        policy_id: '',
        product_id: '',
        serial_number: '',
        purchase_invoice_id: '',
        purchase_source: 'Company Website',
        proof_reference: '',
        purchase_date: new Date().toISOString().slice(0, 16),
      });
      await loadRegistrations();
      alert('Warranty registered successfully!');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail || 'Registration failed');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="page warranties-page">
        <div className="empty-state">
          <h2>Please login to view warranties</h2>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading warranties...</div>;

  const getStatusClass = (status) => {
    const statuses = {
      PENDING: 'status-pending',
      PENDING_REVIEW: 'status-pending',
      ACTIVE: 'status-approved',
      EXPIRED: 'status-rejected',
      CANCELLED: 'status-rejected',
    };
    return statuses[status] || '';
  };

  return (
    <div className="page warranties-page">
      <div className="page-header">
        <h1>My Warranty Registrations</h1>
        <div className="page-header-actions">
          <select value={statusFilter} onChange={(e) => handleStatusFilter(e.target.value)} aria-label="Filter by status">
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="PENDING_REVIEW">Pending review</option>
            <option value="ACTIVE">Active</option>
            <option value="EXPIRED">Expired</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
          <button onClick={openRegister} className="btn btn-primary">
            Register New Warranty
          </button>
        </div>
      </div>

      {showRegister && (
        <div className="modal-overlay" onClick={() => setShowRegister(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Register Warranty</h3>
            <form onSubmit={handleRegister}>
              {policiesLoading ? (
                <p>Loading policies…</p>
              ) : policies.length === 0 ? (
                <div className="alert alert-error">
                  No warranty policies exist yet, so nothing can be registered.
                  {isAdmin ? (
                    <> Create one in <Link to="/admin/warranties">Admin → Warranties</Link>.</>
                  ) : (
                    <> Please ask support or an administrator to add a policy first.</>
                  )}
                </div>
              ) : (
                <>
                  <div className="form-group">
                    <label>Warranty Policy</label>
                    <select
                      value={registerForm.policy_id}
                      onChange={(e) => handlePolicyChange(e.target.value)}
                      required
                    >
                      <option value="">Select a policy…</option>
                      {policies
                        .filter((p) => p.is_active !== false)
                        .map((p) => (
                          <option key={p.id} value={p.id}>
                            {policyLabel(p)}
                          </option>
                        ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Product ID (set by the selected policy)</label>
                    <input type="number" value={registerForm.product_id} readOnly required />
                  </div>
                </>
              )}
              <div className="form-group">
                <label>Serial Number</label>
                <input
                  type="text"
                  value={registerForm.serial_number}
                  onChange={(e) => setRegisterForm({ ...registerForm, serial_number: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Purchase Invoice (optional)</label>
                {invoicesLoading ? (
                  <p>Loading your invoices…</p>
                ) : (
                  <select
                    value={registerForm.purchase_invoice_id}
                    onChange={(e) => setRegisterForm({ ...registerForm, purchase_invoice_id: e.target.value })}
                  >
                    <option value="">No invoice (store purchase on file)</option>
                    {matchingInvoices.map((inv) => (
                      <option key={inv.id} value={inv.invoice_number}>
                        {invoiceLabel(inv)}
                      </option>
                    ))}
                  </select>
                )}
                {registerForm.policy_id && registerForm.product_id && !invoicesLoading && matchingInvoices.length === 0 && invoices.length > 0 && (
                  <p className="muted-text">
                    None of your invoices contain this product. Register without an invoice,
                    buy it first, or pick another policy.
                  </p>
                )}
              </div>
              <div className="form-group">
                <label>Purchase Source</label>
                <select
                  value={registerForm.purchase_source}
                  onChange={(e) => setRegisterForm({ ...registerForm, purchase_source: e.target.value })}
                >
                  <option value="Company Website">Company Website</option>
                  <option value="Amazon">Amazon</option>
                  <option value="Flipkart">Flipkart</option>
                  <option value="Croma">Croma</option>
                  <option value="Reliance Digital">Reliance Digital</option>
                  <option value="Offline Store">Offline Store</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Proof Reference (required for non-website purchases)</label>
                <input
                  type="text"
                  value={registerForm.proof_reference}
                  onChange={(e) => setRegisterForm({ ...registerForm, proof_reference: e.target.value })}
                  placeholder="Invoice / receipt number"
                />
              </div>
              <div className="form-group">
                <label>Purchase Date</label>
                <input
                  type="datetime-local"
                  value={registerForm.purchase_date}
                  onChange={(e) => setRegisterForm({ ...registerForm, purchase_date: e.target.value })}
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowRegister(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">Register</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {registrations.length === 0 ? (
        <div className="empty-state">
          <p>No warranty registrations yet</p>
          <button onClick={openRegister} className="btn btn-primary">
            Register Your First Product
          </button>
        </div>
      ) : (
        <div className="warranties-list">
          {registrations.map((reg) => (
            <div key={reg.id} className="warranty-card">
              <div className="warranty-header">
                <h3>Product #{reg.product_id}</h3>
                <span className={`warranty-status ${getStatusClass(reg.warranty_status)}`}>
                  {reg.warranty_status}
                </span>
              </div>
              <div className="warranty-details">
                <p>Serial: {reg.serial_number}</p>
                <p>Policy: #{reg.policy_id}</p>
                {reg.warranty_number && <p>Warranty No: {reg.warranty_number}</p>}
                <p>Registered: {new Date(reg.created_at).toLocaleDateString()}</p>
              </div>
              <div className="warranty-actions">
                <button
                  onClick={async () => {
                    try {
                      const response = await warrantyApi.checkValidity(reg.id);
                      const v = response.data;
                      alert(
                        `Status: ${v.warranty_status}\nValid: ${v.valid}\nExpires: ${new Date(v.warranty_end_date).toLocaleDateString()}\nDays remaining: ${v.days_remaining}`
                      );
                    } catch {
                      alert('Failed to check validity');
                    }
                  }}
                  className="btn btn-outline btn-sm"
                >
                  Check Validity
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}