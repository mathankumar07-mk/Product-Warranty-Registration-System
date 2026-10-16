import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Navbar from './components/Navbar';
import AdminLayout from './components/AdminLayout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import Products from './pages/Products';
import ProductDetails from './pages/ProductDetails';
import Categories from './pages/Categories';
import CategoryDetails from './pages/CategoryDetails';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Orders from './pages/Orders';
import OrderDetails from './pages/OrderDetails';
import Warranties from './pages/Warranties';
import Notifications from './pages/Notifications';
import Account from './pages/Account';
import Admin from './pages/Admin';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import AdminProducts from './pages/AdminProducts';
import AdminOrders from './pages/AdminOrders';
import AdminWarranties from './pages/AdminWarranties';
import AdminUsers from './pages/AdminUsers';
import AdminAdmins from './pages/AdminAdmins';
import AdminCategories from './pages/AdminCategories';
import AdminPayments from './pages/AdminPayments';
import AdminInvoices from './pages/AdminInvoices';
import AdminPolicies from './pages/AdminPolicies';
import AdminRegistrations from './pages/AdminRegistrations';
import AdminNotifications from './pages/AdminNotifications';
import AdminReports from './pages/AdminReports';
import AdminAuditLogs from './pages/AdminAuditLogs';
import AdminSettings from './pages/AdminSettings';
import './App.css';

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!isAuthenticated) return <Navigate to="/admin/login" replace />;
  if (!isAdmin) return <Navigate to="/" replace />;
  return <AdminLayout>{children}</AdminLayout>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/products" element={<Products />} />
      <Route path="/products/:id" element={<ProductDetails />} />
      <Route path="/categories" element={<Categories />} />
      <Route path="/categories/:id" element={<CategoryDetails />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/checkout" element={<Checkout />} />
      <Route
        path="/orders"
        element={
          <PrivateRoute>
            <Orders />
          </PrivateRoute>
        }
      />
      <Route
        path="/orders/:id"
        element={
          <PrivateRoute>
            <OrderDetails />
          </PrivateRoute>
        }
      />
      <Route
        path="/warranties"
        element={
          <PrivateRoute>
            <Warranties />
          </PrivateRoute>
        }
      />
      <Route
        path="/notifications"
        element={
          <PrivateRoute>
            <Notifications />
          </PrivateRoute>
        }
      />
      <Route
        path="/account"
        element={
          <PrivateRoute>
            <Account />
          </PrivateRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <Admin />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <AdminUsers />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/admins"
        element={
          <AdminRoute>
            <AdminAdmins />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/products"
        element={
          <AdminRoute>
            <AdminProducts />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/categories"
        element={
          <AdminRoute>
            <AdminCategories />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/orders"
        element={
          <AdminRoute>
            <AdminOrders />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/payments"
        element={
          <AdminRoute>
            <AdminPayments />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/invoices"
        element={
          <AdminRoute>
            <AdminInvoices />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/policies"
        element={
          <AdminRoute>
            <AdminPolicies />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/registrations"
        element={
          <AdminRoute>
            <AdminRegistrations />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/warranties"
        element={
          <AdminRoute>
            <AdminWarranties />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/notifications"
        element={
          <AdminRoute>
            <AdminNotifications />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/reports"
        element={
          <AdminRoute>
            <AdminReports />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/audit-logs"
        element={
          <AdminRoute>
            <AdminAuditLogs />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/settings"
        element={
          <AdminRoute>
            <AdminSettings />
          </AdminRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

function AppShell() {
  const location = useLocation();
  const hideNavbar =
    ['/login', '/register', '/forgot-password', '/admin/login'].includes(location.pathname) ||
    location.pathname.startsWith('/admin/');

  return (
    <div className="app">
      {!hideNavbar && <Navbar />}
      <main className="main-content">
        <AppRoutes />
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <AppShell />
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
