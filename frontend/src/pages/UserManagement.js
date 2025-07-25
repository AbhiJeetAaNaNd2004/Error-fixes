import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Input from '../components/UI/Input';
import Modal from '../components/UI/Modal';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { canAccessSuperAdminFeatures } from '../utils/auth';
import { handleApiError } from '../utils/helpers';

const UserManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'employee',
    password: ''
  });
  const [actionLoading, setActionLoading] = useState(false);

  const isSuperAdmin = canAccessSuperAdminFeatures();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    setError('');

    try {
      const usersData = await apiService.getAllUsers();
      setUsers(usersData);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load users'));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setActionLoading(true);

    try {
      await apiService.createUser(formData);
      setShowCreateModal(false);
      setFormData({
        username: '',
        email: '',
        full_name: '',
        role: 'employee',
        password: ''
      });
      await loadUsers();
    } catch (err) {
      setError(handleApiError(err, 'Failed to create user'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }

    setActionLoading(true);
    try {
      await apiService.deleteUser(userId);
      await loadUsers();
    } catch (err) {
      setError(handleApiError(err, 'Failed to delete user'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRole = async (userId, newRole) => {
    setActionLoading(true);
    try {
      await apiService.updateUserRole(userId, newRole);
      await loadUsers();
    } catch (err) {
      setError(handleApiError(err, 'Failed to update user role'));
    } finally {
      setActionLoading(false);
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
        return 'bg-purple-600';
      case 'admin':
        return 'bg-blue-600';
      case 'employee':
        return 'bg-green-600';
      default:
        return 'bg-gray-600';
    }
  };

  if (loading) {
    return (
      <Layout title="User Management" subtitle="Manage employees and their access">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="User Management" subtitle="Manage employees and their access">
      <div className="space-y-6">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Actions Bar */}
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-white">All Users ({users.length})</h2>
          <Button onClick={() => setShowCreateModal(true)}>
            Add New User
          </Button>
        </div>

        {/* Users Table */}
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Name</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Username</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Email</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Role</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Face Images</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-gray-700 hover:bg-gray-800">
                    <td className="py-3 px-4 text-sm text-gray-300">
                      {user.full_name || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-300">
                      {user.username}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-300">
                      {user.email || 'N/A'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium text-white rounded-full ${getRoleBadgeColor(user.role)}`}>
                        {getRoleDisplayName(user.role)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-300">
                      <span className="bg-indigo-600 text-white px-2 py-1 rounded-full text-xs">
                        {user.face_count || 0} faces
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex space-x-2">
                        {isSuperAdmin && user.role !== 'super_admin' && (
                          <select
                            value={user.role}
                            onChange={(e) => handleUpdateRole(user.id, e.target.value)}
                            className="bg-gray-700 border border-gray-600 text-white rounded px-2 py-1 text-xs"
                            disabled={actionLoading}
                          >
                            <option value="employee">Employee</option>
                            <option value="admin">Admin</option>
                          </select>
                        )}
                        {user.role_name !== 'super_admin' && (
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={actionLoading}
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-400">No users found.</p>
              </div>
            )}
          </div>
        </Card>

        {/* Create User Modal */}
        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create New User"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateUser} disabled={actionLoading}>
                {actionLoading ? 'Creating...' : 'Create User'}
              </Button>
            </>
          }
        >
          <form onSubmit={handleCreateUser} className="space-y-4">
            <Input
              id="username"
              label="Username"
              value={formData.username}
              onChange={handleInputChange}
              required
              disabled={actionLoading}
            />
            <Input
              id="full_name"
              label="Full Name"
              value={formData.full_name}
              onChange={handleInputChange}
              required
              disabled={actionLoading}
            />
            <Input
              id="email"
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              disabled={actionLoading}
            />
            <Input
              id="password"
              label="Password"
              type="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              disabled={actionLoading}
            />
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-300 mb-1">
                Role
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={actionLoading}
              >
                <option value="employee">Employee</option>
                {isSuperAdmin && <option value="admin">Admin</option>}
              </select>
            </div>
          </form>
        </Modal>
      </div>
    </Layout>
  );
};

export default UserManagement;