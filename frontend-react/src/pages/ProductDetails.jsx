import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { productApi } from '../services/api';
import { useCart } from '../context/CartContext';

export default function ProductDetails() {
  const { id } = useParams();
  const { addItem } = useCart();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadProduct = async () => {
      try {
        const response = await productApi.get(id);
        setProduct(response.data);
      } catch (err) {
        setError('Failed to load product details');
      } finally {
        setLoading(false);
      }
    };

    loadProduct();
  }, [id]);

  const handleAddToCart = async () => {
    try {
      await addItem(product.id, 1);
      alert('Added to cart!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add to cart');
    }
  };

  if (loading) return <div className="loading">Loading product...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!product) return null;

  return (
    <div className="page product-detail-page">
      <div className="detail-backlink">
        <Link to="/products" className="btn btn-outline">
          ← Back to products
        </Link>
      </div>

      <div className="detail-hero">
        <div className="detail-visual">
          <div className="detail-image">
            <span className="product-badge">Featured</span>
          </div>
        </div>

        <div className="detail-content">
          <p className="eyebrow dark">{product.brand}</p>
          <h1>{product.name}</h1>
          <p className="detail-subtitle">{product.model_number}</p>

          <div className="detail-price-row">
            <span className="detail-price">${product.price}</span>
            <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
              {product.stock_quantity > 0 ? `In stock: ${product.stock_quantity}` : 'Out of stock'}
            </span>
          </div>

          <p className="detail-description">{product.description}</p>

          <div className="detail-actions">
            <button onClick={handleAddToCart} className="btn btn-primary btn-large" disabled={product.stock_quantity === 0}>
              Add to cart
            </button>
            <Link to="/checkout" className="btn btn-outline btn-large">
              Buy now
            </Link>
          </div>

          <div className="detail-specs">
            <div className="detail-spec">
              <span>Category</span>
              <strong>{product.category_id || 'General'}</strong>
            </div>
            <div className="detail-spec">
              <span>Warranty</span>
              <strong>24 months</strong>
            </div>
            <div className="detail-spec">
              <span>Rating</span>
              <strong>★★★★★</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="detail-section">
        <div className="detail-section-card">
          <h2>Why customers love it</h2>
          <p>
            Built for everyday comfort and reliability, this product combines premium craftsmanship,
            dependable performance, and smart convenience for modern living.
          </p>
        </div>

        <div className="detail-section-card">
          <h2>Included with purchase</h2>
          <ul className="detail-list">
            <li>Premium quality packaging</li>
            <li>Digital product support</li>
            <li>Warranty registration ready</li>
            <li>Fast shipping and secure checkout</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
