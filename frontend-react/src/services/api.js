import axios from 'axios';

// Configured via frontend-react/.env (VITE_API_URL) in production builds;
// falls back to the local backend for development.
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    const requestUrl = config?.url || '';
    const isAuthRequest = requestUrl.startsWith('/auth/');
    const hasToken = Boolean(localStorage.getItem('access_token'));

    if (error.response?.status === 401 && hasToken && !isAuthRequest && !config._retried) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', refreshResponse.data.access_token);
          localStorage.setItem('refresh_token', refreshResponse.data.refresh_token);
          config._retried = true;
          config.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
          return api(config);
        } catch (refreshError) {
          // Refresh failed — fall through to logout.
        }
      }
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      const onAdminPage = window.location.pathname.startsWith('/admin');
      window.location.href = onAdminPage ? '/admin/login' : '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  adminMe: () => api.get('/admins/me'),
  refresh: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: (refreshToken) => api.post('/auth/logout', { refresh_token: refreshToken }),
  changePassword: (data) => api.post('/auth/change-password', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
};

export const adminApi = {
  dashboard: () => api.get('/admin/dashboard'),
  overview: () => api.get('/admin/overview'),
  users: (page = 1, pageSize = 20) => api.get('/admin/users', { params: { page, page_size: pageSize } }),
  searchUsers: (params = {}) => api.get('/admin/users/search', { params }),
  getUser: (id) => api.get(`/admin/users/${id}`),
  setUserActive: (id, isActive) => api.patch(`/admin/users/${id}`, { is_active: isActive }),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  listAdmins: () => api.get('/admin/admins'),
  createAdmin: (data) => api.post('/admin/admins', data),
  setAdminActive: (id, isActive) => api.patch(`/admin/admins/${id}`, { is_active: isActive }),
  deleteAdmin: (id) => api.delete(`/admin/admins/${id}`),
  orders: (params = {}) => api.get('/admin/orders', { params }),
  payments: (page = 1, pageSize = 20) => api.get('/admin/payments', { params: { page, page_size: pageSize } }),
  invoices: (params = {}) => api.get('/admin/invoices', { params }),
  getInvoice: (id) => api.get(`/admin/invoices/${id}`),
  downloadAdminInvoice: (id) => api.get(`/admin/invoices/${id}/download`, { responseType: 'blob' }),
  adminNotifications: (params = {}) => api.get('/admin/notifications', { params }),
  reports: () => api.get('/admin/reports/summary'),
  auditLogs: (params = {}) => api.get('/admin/audit-logs', { params }),
  settings: () => api.get('/admin/settings'),
  broadcast: (data) => api.post('/admin/notifications/broadcast', data),
  changePassword: (data) => api.post('/auth/admin/change-password', data),
  searchWarranties: (params = {}) => api.get('/warranties/registrations/search', { params }),
  listPolicies: () => api.get('/warranties/policies'),
  importProducts: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/products/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
};

export const userApi = {
  getMe: () => api.get('/users/me'),
  updateMe: (data) => api.put('/users/me', data),
  getAddresses: () => api.get('/users/me/addresses'),
  createAddress: (data) => api.post('/users/me/addresses', data),
};

export const categoryApi = {
  list: () => api.get('/categories'),
  get: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
};

export const productApi = {
  list: (params = {}) => api.get('/products', { params }),
  get: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
};

export const cartApi = {
  get: () => api.get('/cart'),
  addItem: (data) => api.post('/cart/items', data),
  updateItem: (id, data) => api.put(`/cart/items/${id}`, data),
  removeItem: (id) => api.delete(`/cart/items/${id}`),
  clear: () => api.delete('/cart'),
};

export const orderApi = {
  list: () => api.get('/orders'),
  get: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  update: (id, data) => api.put(`/orders/${id}`, data),
};

export const paymentApi = {
  list: (orderId) => api.get('/payments', { params: { order_id: orderId } }),
  get: (id) => api.get(`/payments/${id}`),
  create: (data) => api.post('/payments', data),
  update: (id, data) => api.put(`/payments/${id}`, data),
  simulate: (id, success = true) => api.post(`/payments/${id}/simulate?success=${success}`),
  refund: (id) => api.post(`/payments/${id}/refund`),
};

export const invoiceApi = {
  list: () => api.get('/invoices'),
  get: (id) => api.get(`/invoices/${id}`),
  getByOrder: (orderId) => api.get(`/invoices/order/${orderId}`),
  getByNumber: (invoiceNumber) => api.get(`/invoices/by-number/${encodeURIComponent(invoiceNumber)}`),
  create: (data) => api.post('/invoices', data),
  update: (id, data) => api.put(`/invoices/${id}`, data),
  download: (id) => api.get(`/invoices/${id}/download`, { responseType: 'blob' }),
};

export const downloadInvoiceFile = async (invoiceId, invoiceNumber) => {
  const response = await invoiceApi.download(invoiceId);
  const disposition = response.headers?.['content-disposition'] || '';
  const match = disposition.match(/filename="?([^";]+)"?/);
  const fallbackExt = invoiceNumber?.endsWith('.pdf') ? '' : '.pdf';
  const filename = match?.[1] || `${invoiceNumber || `invoice-${invoiceId}`}${fallbackExt}`;
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const warrantyApi = {
  createPolicy: (data) => api.post('/warranties/policies', data),
  listPolicies: (params = {}) => api.get('/warranties/policies', { params }),
  getPolicy: (id) => api.get(`/warranties/policies/${id}`),
  getPolicyByProduct: (productId) => api.get(`/warranties/policies/product/${productId}`),
  updatePolicy: (id, data) => api.put(`/warranties/policies/${id}`, data),
  register: (data) => api.post('/warranties/register', data),
  listRegistrations: (params = {}) => api.get('/warranties/registrations', { params }),
  getRegistration: (id) => api.get(`/warranties/registrations/${id}`),
  updateRegistration: (id, data) => api.put(`/warranties/registrations/${id}`, data),
  checkValidity: (id) => api.get(`/warranties/registrations/${id}/validity`),
};

export const notificationApi = {
  list: (unreadOnly = false) => api.get('/notifications', { params: { unread_only: unreadOnly } }),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAllAsRead: () => api.put('/notifications/read-all'),
};

export default api;