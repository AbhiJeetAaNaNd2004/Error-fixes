// Updated auth utilities for httpOnly cookie-based authentication
// Tokens are now handled automatically by the browser via secure cookies

export const getUserRole = () => {
  return localStorage.getItem('userRole');
};

export const setUserRole = (role) => {
  localStorage.setItem('userRole', role);
};

export const clearUserRole = () => {
  localStorage.removeItem('userRole');
};

// Authentication status is determined by the presence of user role
// The actual authentication is handled by httpOnly cookies
export const isAuthenticated = () => {
  return !!getUserRole();
};

export const hasRole = (requiredRole) => {
  const userRole = getUserRole();
  if (!userRole) return false;
  
  const roleHierarchy = {
    'employee': 1,
    'admin': 2,
    'super_admin': 3
  };
  
  return roleHierarchy[userRole] >= roleHierarchy[requiredRole];
};

export const canAccessAdminFeatures = () => {
  return hasRole('admin');
};

export const canAccessSuperAdminFeatures = () => {
  return hasRole('super_admin');
};