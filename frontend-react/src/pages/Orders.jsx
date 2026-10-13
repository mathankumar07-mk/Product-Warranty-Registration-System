import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { orderApi, invoiceApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Orders() {
  const { isAuthenticated } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      loadOrders();
    }
  }, [isAuthenticated]);

  const loadOrders = async () => {
    try {
      const response = await orderApi.list();
      setOrders(response.data);
    } catch (err) {
      setError('Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="page orders-page">
        <div className="empty-state-card">
          <p className="eyebrow dark">Orders</p>
          <h2>Please login to view your orders</h2>
          <Link to="/login" className="btn btn-primary btn-large">Login</Link>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading orders...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  const getStatusClass = (status) => {
    const statuses = {
      pending: 'status-pending',
      confirmed: 'status-confirmed',
      shipped: 'status-shipped',
      delivered: 'status-delivered',
      cancelled: 'status-cancelled',
    };
    return statuses[status] || '';
  };

  return (
    <div className="page orders-page">
      <div className="page-header orders-header">
        <div>
          <p className="eyebrow dark">Order history</p>
          <h1>My Orders</h1>
        </div>
      </div>

      {orders.length === 0 ? (
        <div className="empty-state-card">
          <p className="eyebrow dark">No orders yet</p>
          <h2>You haven’t placed any orders</h2>
          <Link to="/products" className="btn btn-primary btn-large">Start Shopping</Link>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order) => (
            <div key={order.id} className="order-card">
              <div className="order-header">
                <div>
                  <h3>Order #{order.id}</h3>
                  <p className="order-date">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`order-status ${getStatusClass(order.status)}`}>
                  {order.status}
                </span>
              </div>

              <div className="order-details">
                <div>
                  <span>Total</span>
                  <strong>${order.total_amount}</strong>
                </div>
                <div>
                  <span>Items</span>
                  <strong>{order.items?.length || 0}</strong>
                </div>
              </div>

              <div className="order-actions">
                <Link to={`/orders/${order.id}`} className="btn btn-outline order-action-btn">
                  View Details
                </Link>
                <button
                  onClick={async () => {
                    try {
                      await invoiceApi.getByOrder(order.id);
                      alert('Invoice available!');
                    } catch (err) {
                      alert('Invoice not available yet');
                    }
                  }}
                  className="btn btn-outline order-action-btn"
                >
                  View Invoice
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}