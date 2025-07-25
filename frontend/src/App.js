import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Attendance from './pages/Attendance';
import UserManagement from './pages/UserManagement';
import FaceManagement from './pages/FaceManagement';
import CameraManagement from './pages/CameraManagement';
import SystemControl from './pages/SystemControl';
import LiveFeed from './pages/LiveFeed';
import { isAuthenticated } from './utils/auth';
import DepartmentManagement from './pages/DepartmentManagement';
import NotificationContainer from './components/Layout/NotificationContainer';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public Routes */}
          <Route 
            path="/login" 
            element={
              isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />
            } 
          />

          {/* Protected Routes - All Roles */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/attendance" 
            element={
              <ProtectedRoute>
                <Attendance />
              </ProtectedRoute>
            } 
          />

          {/* Admin and Super Admin Routes */}
          <Route 
            path="/users" 
            element={
              <ProtectedRoute requiredRole="admin">
                <UserManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/faces" 
            element={
              <ProtectedRoute requiredRole="admin">
                <FaceManagement />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/live-feed" 
            element={
              <ProtectedRoute requiredRole="admin">
                <LiveFeed />
              </ProtectedRoute>
            } 
          />

          {/* Super Admin Only Routes */}
          <Route 
            path="/system" 
            element={
              <ProtectedRoute requiredRole="super_admin">
                <SystemControl />
              </ProtectedRoute>
            } 
          />

          {/* Default Route */}
          <Route 
            path="/" 
            element={
              isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
            } 
          />
          <Route
            path="/departments"
            element={
              <ProtectedRoute requiredRole="super_admin">
                <DepartmentManagement />
              </ProtectedRoute>
            }
          />

          {/* Catch all route */}
          <Route 
            path="*" 
            element={
              <Navigate to={isAuthenticated() ? "/dashboard" : "/login"} replace />
            } 
          />
        </Routes>
        
        {/* Global notification system */}
        <NotificationContainer />
      </div>
    </Router>
  );
}

export default App;
