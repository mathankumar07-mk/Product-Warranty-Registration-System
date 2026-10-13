import { Link } from 'react-router-dom';

const sections = [
  { to: '/admin/dashboard', title: 'Dashboard', text: 'Metrics and user broadcasts' },
  { to: '/admin/products', title: 'Products', text: 'Catalogue, categories and CSV import' },
  { to: '/admin/orders', title: 'Orders', text: 'Order listing and status management' },
  { to: '/admin/warranties', title: 'Warranties', text: 'Registration review and policies' },
];

export default function Admin() {
  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Administration</h1>
        </div>
      </div>
      <div className="orders-list">
        {sections.map((s) => (
          <div key={s.to} className="order-card">
            <div className="order-header">
              <div>
                <h3>{s.title}</h3>
                <p className="order-date">{s.text}</p>
              </div>
            </div>
            <div className="order-actions">
              <Link to={s.to} className="btn btn-primary order-action-btn">
                Open
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
