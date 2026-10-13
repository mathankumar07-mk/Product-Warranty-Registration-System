import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

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
  (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthRequest = requestUrl.startsWith('/auth/');
    const hasToken = Boolean(localStorage.getItem('access_token'));

    if (error.response?.status === 401 && hasToken && !isAuthRequest) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
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
  list: () => api.get('/products'),
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
};

export const invoiceApi = {
  get: (id) => api.get(`/invoices/${id}`),
  getByOrder: (orderId) => api.get(`/invoices/order/${orderId}`),
  create: (data) => api.post('/invoices', data),
  update: (id, data) => api.put(`/invoices/${id}`, data),
};

export const warrantyApi = {
  createPolicy: (data) => api.post('/warranties/policies', data),
  getPolicy: (id) => api.get(`/warranties/policies/${id}`),
  getPolicyByProduct: (productId) => api.get(`/warranties/policies/product/${productId}`),
  updatePolicy: (id, data) => api.put(`/warranties/policies/${id}`, data),
  register: (data) => api.post('/warranties/register', data),
  listRegistrations: () => api.get('/warranties/registrations'),
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