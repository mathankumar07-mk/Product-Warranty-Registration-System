import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const { itemCount } = useCart();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">Warranty Desk</Link>

        <div className="navbar-menu">
          <Link to="/products" className={`navbar-link ${isActive('/products') ? 'active' : ''}`}>
            Products
          </Link>
          <Link to="/categories" className={`navbar-link ${isActive('/categories') ? 'active' : ''}`}>
            Categories
          </Link>

          {isAuthenticated && (
            <>
              <Link to="/cart" className={`navbar-link ${isActive('/cart') ? 'active' : ''}`}>
                Cart ({itemCount})
              </Link>
              <Link to="/orders" className={`navbar-link ${isActive('/orders') ? 'active' : ''}`}>
                Orders
              </Link>
              <Link to="/warranties" className={`navbar-link ${isActive('/warranties') ? 'active' : ''}`}>
                Warranties
              </Link>
              <Link to="/notifications" className={`navbar-link ${isActive('/notifications') ? 'active' : ''}`}>
                Notifications
              </Link>
            </>
          )}

          <div className="navbar-user">
            {isAuthenticated ? (
              <>
                <span className="navbar-user-name">Hi, {user?.name}</span>
                <button onClick={logout} className="btn btn-outline">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline">Login</Link>
                <Link to="/register" className="btn btn-primary">Register</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}