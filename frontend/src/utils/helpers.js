import { useState, useEffect, useCallback, useRef } from 'react';
import apiService from '../services/api';

// Existing helper functions
export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

export const formatDateOnly = (dateString) => {
  return new Date(dateString).toLocaleDateString();
};

export const formatTime = (dateString) => {
  return new Date(dateString).toLocaleTimeString();
};

export const capitalizeFirst = (str) => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const handleImageDownload = async (imageBlob, filename) => {
  if (imageBlob) {
    downloadBlob(imageBlob, filename);
  }
};

// NEW: Custom React hook for API calls to eliminate boilerplate
export const useApi = (apiCall, dependencies = [], options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const mountedRef = useRef(true);
  
  const {
    immediate = true, // Whether to call API immediately on mount
    onSuccess,
    onError,
    defaultValue = null
  } = options;

  const execute = useCallback(async (...args) => {
    if (!mountedRef.current) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall(...args);
      
      if (mountedRef.current) {
        setData(result);
        if (onSuccess) onSuccess(result);
      }
      
      return result;
    } catch (err) {
      if (mountedRef.current) {
        const errorMessage = err.message || 'An error occurred';
        setError(errorMessage);
        if (onError) onError(err);
        
        // Handle structured error responses
        if (err.message && err.message.includes('404')) {
          console.warn('Resource not found:', err.message);
        } else if (err.message && err.message.includes('403')) {
          console.warn('Access denied:', err.message);
        } else {
          console.error('API Error:', err);
        }
      }
      throw err;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, dependencies);

  useEffect(() => {
    mountedRef.current = true;
    
    if (immediate) {
      execute();
    } else if (defaultValue !== null) {
      setData(defaultValue);
    }
    
    return () => {
      mountedRef.current = false;
    };
  }, dependencies);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const reset = useCallback(() => {
    if (mountedRef.current) {
      setData(defaultValue);
      setError(null);
      setLoading(false);
    }
  }, [defaultValue]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
    refetch: execute
  };
};

// Specialized hooks for common API patterns
export const useApiList = (listApiCall, dependencies = []) => {
  return useApi(listApiCall, dependencies, { defaultValue: [] });
};

export const useApiMutation = (mutationApiCall) => {
  return useApi(mutationApiCall, [], { immediate: false });
};

// Hook for managing action loading states (fixes actionLoading not being reset)
export const useActionState = (initialState = {}) => {
  const [actionLoading, setActionLoading] = useState(initialState);
  
  const setLoading = useCallback((action, isLoading) => {
    setActionLoading(prev => ({
      ...prev,
      [action]: isLoading
    }));
  }, []);
  
  const resetLoading = useCallback(() => {
    setActionLoading(initialState);
  }, [initialState]);
  
  const isLoading = useCallback((action) => {
    return actionLoading[action] || false;
  }, [actionLoading]);
  
  return {
    actionLoading,
    setLoading,
    resetLoading,
    isLoading
  };
};

// Notification system to replace alert() calls
export class NotificationManager {
  static notifications = [];
  static listeners = [];
  
  static addNotification(notification) {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      timestamp: new Date(),
      ...notification
    };
    
    this.notifications.unshift(newNotification);
    this.notifyListeners();
    
    // Auto-remove after delay
    if (notification.autoRemove !== false) {
      setTimeout(() => {
        this.removeNotification(id);
      }, notification.duration || 5000);
    }
    
    return id;
  }
  
  static removeNotification(id) {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notifyListeners();
  }
  
  static addListener(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  static notifyListeners() {
    this.listeners.forEach(listener => listener(this.notifications));
  }
  
  static success(message, options = {}) {
    return this.addNotification({
      type: 'success',
      message,
      ...options
    });
  }
  
  static error(message, options = {}) {
    return this.addNotification({
      type: 'error',
      message,
      duration: 8000, // Errors stay longer
      ...options
    });
  }
  
  static warning(message, options = {}) {
    return this.addNotification({
      type: 'warning',
      message,
      ...options
    });
  }
  
  static info(message, options = {}) {
    return this.addNotification({
      type: 'info',
      message,
      ...options
    });
  }
}

// Hook for using notifications
export const useNotifications = () => {
  const [notifications, setNotifications] = useState(NotificationManager.notifications);
  
  useEffect(() => {
    const unsubscribe = NotificationManager.addListener(setNotifications);
    return unsubscribe;
  }, []);
  
  return {
    notifications,
    addNotification: NotificationManager.addNotification.bind(NotificationManager),
    removeNotification: NotificationManager.removeNotification.bind(NotificationManager),
    success: NotificationManager.success.bind(NotificationManager),
    error: NotificationManager.error.bind(NotificationManager),
    warning: NotificationManager.warning.bind(NotificationManager),
    info: NotificationManager.info.bind(NotificationManager)
  };
};