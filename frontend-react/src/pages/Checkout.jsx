import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { orderApi, paymentApi, userApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Checkout() {
  const { isAuthenticated } = useAuth();
  const { cart, total, itemCount, clearCart } = useCart();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: address, 2: payment
  const [address, setAddress] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [newAddress, setNewAddress] = useState({
    label: '',
    line1: '',
    line2: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    is_default: false,
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }
    if (!cart || !cart.items || cart.items.length === 0) {
      navigate('/cart');
      return;
    }
    loadAddresses();
  }, [isAuthenticated, cart, navigate]);

  const loadAddresses = async () => {
    try {
      const response = await userApi.getAddresses();
      setAddresses(response.data);
      if (response.data.length > 0) {
        setAddress(response.data.find((a) => a.is_default) || response.data[0]);
      }
    } catch (err) {
      console.error('Failed to load addresses:', err);
    }
  };

  const handleCreateOrder = async (selectedAddress = address) => {
    if (!selectedAddress?.id || selectedAddress.id === 'new') {
      setError('Please select or add a shipping address');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await orderApi.create({
        shipping_address_id: selectedAddress.id,
        billing_address_id: selectedAddress.id,
      });
      setStep(2);
      // Store order ID for payment step
      localStorage.setItem('pending_order_id', response.data.id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create order');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    const orderId = localStorage.getItem('pending_order_id');
    if (!orderId) {
      setError('Order not found');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const paymentResponse = await paymentApi.create({
        order_id: parseInt(orderId),
        amount: total,
        method: paymentMethod,
      });
      // Simulate payment success
      await paymentApi.simulate(paymentResponse.data.id, true);
      await clearCart();
      localStorage.removeItem('pending_order_id');
      navigate('/orders');
    } catch (err) {
      setError(err.response?.data?.detail || 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;
  if (!cart || !cart.items || cart.items.length === 0) return null;

  return (
    <div className="page checkout-page">
      <div className="checkout-container">
        <div className="checkout-steps">
          <div className={`step ${step >= 1 ? 'active' : ''}`}>1. Address</div>
          <div className={`step ${step >= 2 ? 'active' : ''}`}>2. Review & Pay</div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {step === 1 && (
          <div className="checkout-section">
            <h2>Shipping Address</h2>
            {addresses.length > 0 && (
              <div className="address-selection">
                <h4>Select Existing Address</h4>
                {addresses.map((addr) => (
                  <label key={addr.id} className={`address-option ${address?.id === addr.id ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name="address"
                      value={addr.id}
                      checked={address?.id === addr.id}
                      onChange={() => setAddress(addr)}
                    />
                    <div className="address-preview">
                      <strong>{addr.label}</strong>
                      <p>{addr.line1} {addr.line2 ? ', ' + addr.line2 : ''}</p>
                      <p>{addr.city}, {addr.state} {addr.postal_code}, {addr.country}</p>
                    </div>
                  </label>
                ))}
              </div>
            )}
            <div className="address-form">
              <h4>Or Add New Address</h4>
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  setLoading(true);
                  setError('');
                  try {
                    const response = await userApi.createAddress(newAddress);
                    setAddress(response.data);
                    await handleCreateOrder(response.data);
                  } catch (err) {
                    setError(err.response?.data?.detail || 'Failed to save address');
                  } finally {
                    setLoading(false);
                  }
                }}
              >
                <div className="form-row">
                  <div className="form-group">
                    <label>Label *</label>
                    <input
                      type="text"
                      value={newAddress.label}
                      onChange={(e) => setNewAddress({ ...newAddress, label: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Country *</label>
                    <input
                      type="text"
                      value={newAddress.country}
                      onChange={(e) => setNewAddress({ ...newAddress, country: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Line 1 *</label>
                    <input
                      type="text"
                      value={newAddress.line1}
                      onChange={(e) => setNewAddress({ ...newAddress, line1: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Line 2</label>
                    <input
                      type="text"
                      value={newAddress.line2}
                      onChange={(e) => setNewAddress({ ...newAddress, line2: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>City *</label>
                    <input
                      type="text"
                      value={newAddress.city}
                      onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>State *</label>
                    <input
                      type="text"
                      value={newAddress.state}
                      onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Postal Code *</label>
                    <input
                      type="text"
                      value={newAddress.postal_code}
                      onChange={(e) => setNewAddress({ ...newAddress, postal_code: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="form-group checkbox-inline">
                  <label>
                    <input
                      type="checkbox"
                      checked={newAddress.is_default}
                      onChange={(e) => setNewAddress({ ...newAddress, is_default: e.target.checked })}
                    />
                    Set as default
                  </label>
                </div>
                <button type="submit" className="btn btn-primary btn-block">Use This Address & Continue</button>
              </form>
            </div>
            {address?.id && address.id !== 'new' && (
              <button
                type="button"
                onClick={() => handleCreateOrder()}
                className="btn btn-primary btn-block"
                disabled={loading}
              >
                {loading ? 'Creating order...' : 'Continue with selected address'}
              </button>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="checkout-section">
            <h2>Review & Pay</h2>

            <div className="checkout-summary-panel">
              <div className="checkout-summary-card">
                <h4>Shipping to</h4>
                <div className="selected-address-box">
                  <strong>{address?.label || 'Shipping Address'}</strong>
                  <p>{address?.line1}</p>
                  <p>{address?.city}, {address?.state} {address?.postal_code}</p>
                  <p>{address?.country}</p>
                </div>
              </div>

              <div className="checkout-summary-card">
                <h4>Your items</h4>
                <div className="checkout-item-list">
                  {cart.items.map((item) => (
                    <div key={item.id} className="checkout-item">
                      <div>
                        <strong>{item.product.name}</strong>
                        <span>{item.quantity} × ${item.product.price}</span>
                      </div>
                      <span>${(item.product.price * item.quantity).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="payment-methods">
              {['card', 'upi', 'netbanking', 'wallet', 'cod'].map((method) => (
                <label key={method} className={`payment-option ${paymentMethod === method ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="payment"
                    value={method}
                    checked={paymentMethod === method}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                  />
                  <span className="payment-label">
                    {method.charAt(0).toUpperCase() + method.slice(1)}
                  </span>
                </label>
              ))}
            </div>

            <div className="checkout-summary">
              <h4>Order Summary</h4>
              <div className="summary-line">
                <span>Subtotal ({itemCount} items)</span>
                <span>${total.toFixed(2)}</span>
              </div>
              <div className="summary-line">
                <span>Shipping</span>
                <span>Free</span>
              </div>
              <div className="summary-line total">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>

            <div className="checkout-actions">
              <button onClick={() => setStep(1)} className="btn btn-outline">Back</button>
              <button onClick={handlePayment} className="btn btn-primary btn-block" disabled={loading}>
                {loading ? 'Processing...' : `Pay $${total.toFixed(2)}`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}