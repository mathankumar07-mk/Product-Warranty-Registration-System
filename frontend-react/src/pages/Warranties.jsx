import { useState, useEffect } from 'react';
import { warrantyApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Warranties() {
  const { isAuthenticated } = useAuth();
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    policy_id: '',
    product_id: '',
    serial_number: '',
    purchase_invoice_id: '',
  });

  useEffect(() => {
    if (isAuthenticated) {
      loadRegistrations();
    }
  }, [isAuthenticated]);

  const loadRegistrations = async () => {
    try {
      const response = await warrantyApi.listRegistrations();
      setRegistrations(response.data);
    } catch (err) {
      setError('Failed to load registrations');
    } finally {
      setLoading(false);
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
      };
      if (registerForm.purchase_invoice_id.trim()) {
        payload.purchase_invoice_id = Number(registerForm.purchase_invoice_id);
      }
      await warrantyApi.register(payload);
      setShowRegister(false);
      setRegisterForm({ policy_id: '', product_id: '', serial_number: '', purchase_invoice_id: '' });
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
      pending: 'status-pending',
      approved: 'status-approved',
      rejected: 'status-rejected',
    };
    return statuses[status] || '';
  };

  return (
    <div className="page warranties-page">
      <div className="page-header">
        <h1>My Warranty Registrations</h1>
        <button onClick={() => setShowRegister(true)} className="btn btn-primary">
          Register New Warranty
        </button>
      </div>

      {showRegister && (
        <div className="modal-overlay" onClick={() => setShowRegister(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Register Warranty</h3>
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label>Policy ID</label>
                <input
                  type="number"
                  value={registerForm.policy_id}
                  onChange={(e) => setRegisterForm({ ...registerForm, policy_id: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Product ID</label>
                <input
                  type="number"
                  value={registerForm.product_id}
                  onChange={(e) => setRegisterForm({ ...registerForm, product_id: e.target.value })}
                  required
                />
              </div>
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
                <label>Purchase Invoice ID (optional)</label>
                <input
                  type="number"
                  value={registerForm.purchase_invoice_id}
                  onChange={(e) => setRegisterForm({ ...registerForm, purchase_invoice_id: e.target.value })}
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
          <button onClick={() => setShowRegister(true)} className="btn btn-primary">
            Register Your First Product
          </button>
        </div>
      ) : (
        <div className="warranties-list">
          {registrations.map((reg) => (
            <div key={reg.id} className="warranty-card">
              <div className="warranty-header">
                <h3>Product #{reg.product_id}</h3>
                <span className={`warranty-status ${getStatusClass(reg.status)}`}>
                  {reg.status}
                </span>
              </div>
              <div className="warranty-details">
                <p>Serial: {reg.serial_number}</p>
                <p>Policy: #{reg.policy_id}</p>
                <p>Registered: {new Date(reg.created_at).toLocaleDateString()}</p>
              </div>
              <div className="warranty-actions">
                <button
                  onClick={async () => {
                    try {
                      const response = await warrantyApi.checkValidity(reg.id);
                      alert(`Valid: ${response.data.valid}\nExpires: ${response.data.expires_at}`);
                    } catch (err) {
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