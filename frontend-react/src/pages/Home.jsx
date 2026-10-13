import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="page home-page">
      <section className="hero-section">
        <div className="hero-copy">
          <span className="badge">New season essentials</span>
          <h1>Mini e-commerce built for smarter buying.</h1>
          <p>
            Discover premium products, track every order, and register your warranty with one seamless shopping experience.
          </p>

          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary btn-large">
              Shop now
            </Link>
            {isAuthenticated ? (
              <Link to="/cart" className="btn btn-outline btn-large home-light-btn">
                View cart
              </Link>
            ) : (
              <Link to="/register" className="btn btn-outline btn-large home-light-btn">
                Get started
              </Link>
            )}
          </div>

          <div className="hero-stats">
            <div>
              <strong>12k+</strong>
              <span>Happy buyers</span>
            </div>
            <div>
              <strong>4.9/5</strong>
              <span>Average rating</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>Warranty support</span>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div className="floating-card card-top">
            <span className="card-label">Best seller</span>
            <h3>NoiseGuard Pro</h3>
            <p>Premium wireless audio</p>
            <strong>$129</strong>
          </div>

          <div className="hero-product-panel">
            <div className="device-shape"></div>
          </div>

          <div className="floating-card card-bottom">
            <span className="card-label success">Warranty active</span>
            <p>24 months coverage</p>
            <strong>Protected</strong>
          </div>
        </div>
      </section>

      <section className="features-grid">
        <div className="feature-card">
          <div className="icon-wrap">🛒</div>
          <h3>Shop products</h3>
          <p>Browse curated categories and add favorites to cart with one click.</p>
        </div>
        <div className="feature-card">
          <div className="icon-wrap">🛡️</div>
          <h3>Warranty registration</h3>
          <p>Register purchases quickly and track protection for every order.</p>
        </div>
        <div className="feature-card">
          <div className="icon-wrap">📦</div>
          <h3>Track orders</h3>
          <p>Follow payments, invoices, shipping updates, and recent activity.</p>
        </div>
        <div className="feature-card">
          <div className="icon-wrap">🔔</div>
          <h3>Smart notifications</h3>
          <p>Stay informed with alerts on delivery, payment, and warranty changes.</p>
        </div>
      </section>

      <section className="promo-grid">
        <div className="promo-card promo-primary">
          <p className="promo-kicker">Why shoppers choose us</p>
          <h2>Fast delivery, trusted products, and effortless after-sales care.</h2>
          <Link to="/products" className="btn btn-primary btn-large">
            Explore deals
          </Link>
        </div>

        <div className="promo-card promo-secondary">
          <p className="promo-kicker">Top picks</p>
          <ul>
            <li>Smart home essentials</li>
            <li>Audio & accessories</li>
            <li>Home office upgrades</li>
            <li>Daily convenience tech</li>
          </ul>
        </div>
      </section>

      <section className="cta-banner">
        <div>
          <p className="promo-kicker">Ready to shop smarter?</p>
          <h2>Protect your purchases and enjoy a faster checkout experience.</h2>
        </div>
        <Link to="/register" className="btn btn-primary btn-large">
          Create account
        </Link>
      </section>
    </div>
  );
}