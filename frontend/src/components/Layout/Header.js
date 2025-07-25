import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../UI/Button';
import { getUserRole, clearUserRole } from '../../utils/auth';
import apiService from '../../services/api';

const Header = ({ title, subtitle }) => {
  const navigate = useNavigate();
  const userRole = getUserRole();

  const handleLogout = async () => {
    try {
      // Call backend logout endpoint to clear the httpOnly cookie
      await apiService.logout();
    } catch (error) {
      console.warn('Logout API call failed:', error);
      // Continue with logout even if API call fails
    } finally {
      // Clear user role from localStorage and redirect
      clearUserRole();
      navigate('/login');
    }
  };

  const getRoleDisplayName = (role) => {
    switch (role) {
      case 'super_admin':
        return 'Super Admin';
      case 'admin':
        return 'Admin';
      case 'employee':
        return 'Employee';
      default:
        return role;
    }
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'super_admin':
        return 'bg-purple-100 text-purple-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      case 'employee':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-light">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-heading">{title}</h1>
          {subtitle && (
            <p className="text-sm text-muted mt-1">{subtitle}</p>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-body">Role:</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(userRole)}`}>
                {getRoleDisplayName(userRole)}
              </span>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;