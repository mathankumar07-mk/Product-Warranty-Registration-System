import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function Cart() {
  const { cart, loading, itemCount, total, updateItem, removeItem, clearCart, refreshCart } = useCart();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      refreshCart();
    }
  }, [isAuthenticated, refreshCart]);

  if (!isAuthenticated) {
    return (
      <div className="page cart-page">
        <div className="empty-cart">
          <div className="empty-cart-box">
            <p className="eyebrow dark">Your cart</p>
            <h2>Please login to view your cart</h2>
            <Link to="/login" state={{ from: '/cart' }} className="btn btn-primary btn-large">Login</Link>
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading cart...</div>;

  if (!cart || !cart.items || cart.items.length === 0) {
    return (
      <div className="page cart-page">
        <div className="empty-cart">
          <div className="empty-cart-box">
            <p className="eyebrow dark">Your cart</p>
            <h2>Your cart is empty</h2>
            <Link to="/products" className="btn btn-primary btn-large">Continue Shopping</Link>
          </div>
        </div>
      </div>
    );
  }

  const handleQuantityChange = async (itemId, quantity) => {
    if (quantity < 1) return;
    await updateItem(itemId, quantity);
  };

  const handleRemove = async (itemId) => {
    if (window.confirm('Remove this item?')) {
      await removeItem(itemId);
    }
  };

  return (
    <div className="page cart-page">
      <div className="page-header cart-header">
        <div>
          <p className="eyebrow dark">Bag</p>
          <h1>Shopping Cart ({itemCount} items)</h1>
        </div>
      </div>

      <div className="cart-layout">
        <div className="cart-items">
          {cart.items.map((item) => (
            <div key={item.id} className="cart-item">
              <div className="cart-item-preview"></div>

              <div className="cart-item-info">
                <h4>{item.product.name}</h4>
                <p className="cart-item-brand">{item.product.brand} • {item.product.model_number}</p>
                <p className="cart-item-price">${item.product.price} each</p>
              </div>

              <div className="cart-item-quantity">
                <button
                  onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                  disabled={item.quantity <= 1}
                  className="qty-btn"
                >
                  −
                </button>
                <span className="qty-value">{item.quantity}</span>
                <button
                  onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                  disabled={item.quantity >= item.product.stock_quantity}
                  className="qty-btn"
                >
                  +
                </button>
              </div>

              <div className="cart-item-total">
                ${(item.product.price * item.quantity).toFixed(2)}
              </div>

              <button onClick={() => handleRemove(item.id)} className="btn btn-danger btn-sm">
                Remove
              </button>
            </div>
          ))}
        </div>

        <aside className="cart-summary">
          <h3>Order Summary</h3>
          <div className="summary-line">
            <span>Subtotal ({itemCount} items)</span>
            <span>${total.toFixed(2)}</span>
          </div>
          <div className="summary-line">
            <span>Shipping</span>
            <span>Calculated at checkout</span>
          </div>
          <div className="summary-line total">
            <span>Total</span>
            <span>${total.toFixed(2)}</span>
          </div>
          <Link to="/checkout" className="btn btn-primary btn-block btn-large">
            Proceed to Checkout
          </Link>
          <button onClick={clearCart} className="btn btn-outline btn-block">
            Clear Cart
          </button>
        </aside>
      </div>
    </div>
  );
}