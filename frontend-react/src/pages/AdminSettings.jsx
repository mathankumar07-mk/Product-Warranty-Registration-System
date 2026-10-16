import { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

export default function AdminSettings() {
  const [settings, setSettings] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    adminApi.settings().then((res) => setSettings(res.data)).catch(() => setError('Failed to load settings'));
  }, []);

  return (
    <div className="page admin-page">
      <div className="page-header">
        <div>
          <p className="eyebrow dark">Admin</p>
          <h1>Settings</h1>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!settings ? (
        <div className="loading">Loading settings…</div>
      ) : (
        <div className="detail-section-card">
          <h2>Environment (read-only, secrets never exposed)</h2>
          <div className="detail-meta-list">
            <div><span>App</span><strong>{settings.app_name}</strong></div>
            <div><span>Environment</span><strong>{settings.environment}</strong></div>
            <div><span>Frontend URL</span><strong>{settings.frontend_url || '—'}</strong></div>
            <div><span>JWT algorithm</span><strong>{settings.jwt_algorithm}</strong></div>
            <div><span>Token expiry</span><strong>{settings.access_token_expire_minutes} min</strong></div>
            <div><span>Database</span><strong>{settings.db_dialect}</strong></div>
            <div><span>SMTP configured</span><strong>{settings.smtp_configured ? 'yes' : 'no'}</strong></div>
            <div><span>Email from</span><strong>{settings.email_from || '—'}</strong></div>
          </div>
          <h2>Payments</h2>
          <p className="muted-link">{settings.payment_note}</p>
          <h2>CORS origins</h2>
          <ul>{(settings.cors_origins || []).map((o) => <li key={o}>{o}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
