import { useState, useEffect } from 'react';
import { notificationApi } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Notifications() {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [unreadOnly, setUnreadOnly] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadNotifications();
    }
  }, [isAuthenticated, unreadOnly]);

  const loadNotifications = async () => {
    try {
      const response = await notificationApi.list(unreadOnly);
      setNotifications(response.data);
    } catch {
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id) => {
    try {
      await notificationApi.markAsRead(id);
      setNotifications(notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch {
      alert('Failed to mark as read');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead();
      setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    } catch {
      alert('Failed to mark all as read');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="page notifications-page">
        <div className="empty-state">
          <h2>Please login to view notifications</h2>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading">Loading notifications...</div>;

  const getTypeClass = (type) => {
    const types = {
      order: 'type-order',
      payment: 'type-payment',
      warranty: 'type-warranty',
      general: 'type-general',
    };
    return types[type] || '';
  };

  return (
    <div className="page notifications-page">
      <div className="page-header">
        <h1>Notifications</h1>
        <div className="notification-controls">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
            />
            Unread only
          </label>
          {notifications.some((n) => !n.is_read) && (
            <button onClick={handleMarkAllAsRead} className="btn btn-outline btn-sm">
              Mark All as Read
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {notifications.length === 0 ? (
        <div className="empty-state">
          <p>No notifications</p>
        </div>
      ) : (
        <div className="notifications-list">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
            >
              <div className="notification-icon">
                <span className={getTypeClass(notification.type)}>
                  {notification.type.charAt(0).toUpperCase() + notification.type.slice(1)}
                </span>
              </div>
              <div className="notification-content">
                <div className="notification-header">
                  <h4>{notification.title}</h4>
                  <span className="notification-time">
                    {new Date(notification.created_at).toLocaleString()}
                  </span>
                </div>
                <p>{notification.message}</p>
              </div>
              {!notification.is_read && (
                <button
                  onClick={() => handleMarkAsRead(notification.id)}
                  className="btn btn-sm btn-outline"
                >
                  Mark Read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}