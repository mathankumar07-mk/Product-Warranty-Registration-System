import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { orderApi, invoiceApi, downloadInvoiceFile } from '../services/api';

export default function OrderDetails() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadOrder = async () => {
      try {
        const [orderRes, invoiceRes] = await Promise.all([
          orderApi.get(id),
          invoiceApi.getByOrder(id).catch(() => null),
        ]);

        setOrder(orderRes.data);
        setInvoice(invoiceRes?.data || null);
      } catch (err) {
        setError('Failed to load order details');
      } finally {
        setLoading(false);
      }
    };

    loadOrder();
  }, [id]);

  if (loading) return <div className="loading">Loading order details...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!order) return null;

  const getStatusClass = (status) => {
    const map = {
      pending: 'status-pending',
      confirmed: 'status-confirmed',
      shipped: 'status-shipped',
      delivered: 'status-delivered',
      cancelled: 'status-cancelled',
    };
    return map[status] || '';
  };

  return (
    <div className="page order-detail-page">
      <div className="detail-backlink">
        <Link to="/orders" className="btn btn-outline">
          ← Back to orders
        </Link>
      </div>

      <div className="order-detail-card">
        <div className="order-detail-header">
          <div>
            <p className="eyebrow dark">Order summary</p>
            <h1>Order #{order.id}</h1>
          </div>
          <span className={`order-status ${getStatusClass(order.status)}`}>{order.status}</span>
        </div>

        <div className="order-detail-grid">
          <div className="detail-section-card">
            <h2>Order details</h2>
            <div className="detail-meta-list">
              <div>
                <span>Placed</span>
                <strong>{new Date(order.created_at).toLocaleString()}</strong>
              </div>
              <div>
                <span>Total</span>
                <strong>${order.total_amount}</strong>
              </div>
              <div>
                <span>Items</span>
                <strong>{order.items?.length || 0}</strong>
              </div>
            </div>
          </div>

          <div className="detail-section-card">
            <h2>Invoice</h2>
            {invoice ? (
              <div className="detail-meta-list">
                <div>
                  <span>Invoice No</span>
                  <strong>{invoice.invoice_number || invoice.id}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>Issued</strong>
                </div>
                <div>
                  <span>Amount</span>
                  <strong>${invoice.total_amount || order.total_amount}</strong>
                </div>
                <button
                  onClick={async () => {
                    try {
                      await downloadInvoiceFile(invoice.id, invoice.invoice_number);
                    } catch (err) {
                      alert('Failed to download invoice');
                    }
                  }}
                  className="btn btn-outline btn-sm"
                >
                  Download Invoice
                </button>
              </div>
            ) : (
              <p className="muted-text">Invoice is not available yet.</p>
            )}
          </div>
        </div>

        <div className="detail-section-card full-width">
          <h2>Items</h2>
          <div className="checkout-item-list">
            {(order.items || []).map((item) => {
              const unitPrice = Number(item.unit_price ?? item.product?.price ?? 0);
              return (
                <div key={item.id} className="checkout-item">
                  <div>
                    <strong>{item.product?.name || 'Product'}</strong>
                    <span>{item.quantity} × ${unitPrice.toFixed(2)}</span>
                  </div>
                  <span>${(unitPrice * item.quantity).toFixed(2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
