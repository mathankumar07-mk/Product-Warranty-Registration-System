import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productApi } from '../services/api';
import { useCart } from '../context/CartContext';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const { addItem } = useCart();

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await productApi.list();
      // Backend returns a paginated envelope {products, total, ...}; be lenient.
      const data = response.data;
      setProducts(Array.isArray(data) ? data : data.products || []);
    } catch (err) {
      setError('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  const categories = ['all', ...new Set(products.map((product) => String(product.category_id || 'General')))] ;
  const filteredProducts = products.filter((product) => {
    const matchesSearch = `${product.name} ${product.brand} ${product.model_number}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase());

    const matchesCategory = selectedCategory === 'all' || String(product.category_id || 'General') === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  const handleAddToCart = async (productId) => {
    try {
      await addItem(productId, 1);
      alert('Added to cart!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add to cart');
    }
  };

  if (loading) return <div className="loading">Loading products...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div className="page products-page">
      <div className="page-header products-header">
        <div>
          <p className="eyebrow dark">Shop collection</p>
          <h1>Featured products</h1>
        </div>
        <Link to="/" className="btn btn-outline">
          Back home
        </Link>
      </div>

      <div className="product-toolbar">
        <div className="product-search-wrap">
          <span className="search-icon">⌕</span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search products, brands, models"
            className="product-search"
          />
        </div>

        <div className="filter-chips">
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              className={`filter-chip ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category === 'all' ? 'All' : `Category ${category}`}
            </button>
          ))}
        </div>
      </div>

      <div className="products-grid">
        {filteredProducts.length === 0 ? (
          <div className="empty-state">
            <p>No products match your search.</p>
          </div>
        ) : (
          filteredProducts.map((product) => (
            <article key={product.id} className="product-card">
              <div className="product-image">
                <span className="product-badge">Featured</span>
              </div>

              <div className="product-info">
                <div className="product-topline">
                  <span className="product-brand">{product.brand}</span>
                  <span className={`product-stock ${product.stock_quantity > 0 ? 'in-stock' : 'out-of-stock'}`}>
                    {product.stock_quantity > 0 ? `In stock: ${product.stock_quantity}` : 'Out of stock'}
                  </span>
                </div>

                <h3>{product.name}</h3>
                <p className="product-model">{product.model_number}</p>
                <p className="product-description">{product.description}</p>

                <div className="product-meta">
                  <span className="product-price">${product.price}</span>
                  <span className="product-rating">★★★★★</span>
                </div>
              </div>

              <div className="product-actions">
                <Link to={`/products/${product.id}`} className="btn btn-outline product-secondary-btn">
                  Details
                </Link>
                <button
                  onClick={() => handleAddToCart(product.id)}
                  disabled={product.stock_quantity === 0}
                  className="btn btn-primary product-primary-btn"
                >
                  Add to cart
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}