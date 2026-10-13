import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { categoryApi, productApi } from '../services/api';

export default function CategoryDetails() {
  const { id } = useParams();
  const [category, setCategory] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadCategory = async () => {
      try {
        const [categoryRes, productsRes] = await Promise.all([
          categoryApi.get(id),
          productApi.list(),
        ]);

        const categoryData = categoryRes.data;
        const filteredProducts = productsRes.data.filter((product) => product.category_id === Number(id));

        setCategory(categoryData);
        setProducts(filteredProducts);
      } catch (err) {
        setError('Failed to load category details');
      } finally {
        setLoading(false);
      }
    };

    loadCategory();
  }, [id]);

  if (loading) return <div className="loading">Loading category...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!category) return null;

  return (
    <div className="page category-detail-page">
      <div className="detail-backlink">
        <Link to="/categories" className="btn btn-outline">
          ← Back to categories
        </Link>
      </div>

      <div className="category-detail-header">
        <div>
          <p className="eyebrow dark">Collection</p>
          <h1>{category.name}</h1>
        </div>
        <span className={`category-status ${category.is_active ? 'active' : 'inactive'}`}>
          {category.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      <div className="category-detail-intro">
        <p>{category.description || 'Explore the curated products in this category.'}</p>
      </div>

      <div className="products-grid">
        {products.length === 0 ? (
          <div className="empty-state">
            <p>No products in this category yet.</p>
          </div>
        ) : (
          products.map((product) => (
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
                <Link to={`/products/${product.id}`} className="btn btn-primary product-primary-btn">
                  View item
                </Link>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
