import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const response = await authApi.me();
      setUser({ ...response.data, role: 'customer' });
    } catch (error) {
      // Fall through to admin profile: admins authenticate with is_admin tokens
      // that /auth/me rejects.
      try {
        const adminResponse = await authApi.adminMe();
        setUser({ ...adminResponse.data, role: 'admin' });
      } catch (adminError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email, password) => {
    const response = await authApi.login({ email, password });
    localStorage.setItem('access_token', response.data.access_token);
    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    await fetchUser();
    return response.data;
  };

  // Separate admin login: authenticates, then verifies admin privileges
  // server-side via /admins/me. Customer tokens are rejected here and cleared.
  const adminLogin = async (email, password) => {
    const response = await authApi.login({ email, password });
    localStorage.setItem('access_token', response.data.access_token);
    if (response.data.refresh_token) {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    try {
      const adminResponse = await authApi.adminMe();
      const adminUser = { ...adminResponse.data, role: 'admin' };
      setUser(adminUser);
      setLoading(false);
      return adminUser;
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setLoading(false);
      throw new Error('This account does not have admin access');
    }
  };

  const register = async (name, email, password, phone) => {
    const response = await authApi.register({ name, email, password, phone });
    return response.data;
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch (error) {
        console.error('Server logout failed:', error);
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    adminLogin,
    register,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    refreshUser: fetchUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}