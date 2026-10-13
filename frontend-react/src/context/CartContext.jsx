import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { cartApi } from '../services/api';

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!localStorage.getItem('access_token')) {
      setCart(null);
      return;
    }

    setLoading(true);
    try {
      const response = await cartApi.get();
      setCart(response.data);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addItem = async (productId, quantity = 1) => {
    await cartApi.addItem({ product_id: productId, quantity });
    await fetchCart();
  };

  const updateItem = async (itemId, quantity) => {
    await cartApi.updateItem(itemId, { quantity });
    await fetchCart();
  };

  const removeItem = async (itemId) => {
    await cartApi.removeItem(itemId);
    await fetchCart();
  };

  const clearCart = async () => {
    await cartApi.clear();
    setCart({ items: [] });
  };

  const itemCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const total = cart?.items?.reduce((sum, item) => sum + item.product.price * item.quantity, 0) || 0;

  const value = {
    cart,
    loading,
    itemCount,
    total,
    addItem,
    updateItem,
    removeItem,
    clearCart,
    refreshCart: fetchCart,
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}