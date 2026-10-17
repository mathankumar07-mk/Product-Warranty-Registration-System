import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { categoryApi } from '../services/api';

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await categoryApi.list();
      setCategories(response.data);
    } catch {
      setError('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading categories...</div>;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div className="page categories-page">
      <div className="page-header">
        <h1>Categories</h1>
      </div>

      <div className="categories-grid">
        {categories.length === 0 ? (
          <p className="empty-state">No categories available</p>
        ) : (
          categories.map((category) => (
            <Link key={category.id} to={`/categories/${category.id}`} className="category-card">
              <h3>{category.name}</h3>
              {category.description && <p>{category.description}</p>}
              <span className={`category-status ${category.is_active ? 'active' : 'inactive'}`}>
                {category.is_active ? 'Active' : 'Inactive'}
              </span>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}