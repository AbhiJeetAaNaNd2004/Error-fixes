//dashboars.js
import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import Button from '../components/UI/Button';
import apiService from '../services/api';
import { getUserRole, canAccessAdminFeatures, canAccessSuperAdminFeatures } from '../utils/auth';
import { formatDateTime, getStatusColor, getStatusText, handleApiError } from '../utils/helpers';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState({
    userStatus: null,
    totalEmployees: 0,
    activeCameras: 0,
    trackerStatus: null,
    recentAttendance: []
  });

  const userRole = getUserRole();
  const isAdmin = canAccessAdminFeatures();
  const isSuperAdmin = canAccessSuperAdminFeatures();

  // Wrap the function in useCallback
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      // Load user status for all roles
      const userStatus = await apiService.getUserStatus();
      
      let totalEmployees = 0;
      let activeCameras = 0;
      let trackerStatus = null;
      let recentAttendance = [];

      // Load additional data for admin and super admin
      if (isAdmin) {
        const [users, cameras, attendance] = await Promise.all([
          apiService.getAllUsers(),
          apiService.getCameras(),
          apiService.getAllAttendanceLogs()
        ]);
        
        totalEmployees = users.length;
        activeCameras = cameras.filter(cam => cam.status === 'running').length;
        recentAttendance = attendance.slice(0, 5); // Show last 5 entries
      }

      // Load tracker status for super admin
      if (isSuperAdmin) {
        trackerStatus = await apiService.getTrackerStatus();
      }

      setDashboardData({
        userStatus,
        totalEmployees,
        activeCameras,
        trackerStatus,
        recentAttendance
      });
    } catch (err) {
      setError(handleApiError(err, 'Failed to load dashboard data'));
    } finally {
      setLoading(false);
    }
  }, [isAdmin, isSuperAdmin]); // The dependencies that affect the function behavior

  // Add the function to the dependency array
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const StatCard = ({ title, value, icon, color = 'blue', subtitle }) => (
    <Card className="hover:shadow-light-lg transition-shadow duration-200">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-${color}-100 text-${color}-600 mr-4`}>
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-muted text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-heading">{value}</p>
          {subtitle && <p className="text-muted text-xs mt-1">{subtitle}</p>}
        </div>
      </div>
    </Card>
  );

  const StatusBadge = ({ status, lastEventTime }) => {
    const isCheckedIn = status === 'checked_in';
    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
        isCheckedIn ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
      }`}>
        <div className={`w-2 h-2 rounded-full mr-2 ${
          isCheckedIn ? 'bg-green-400' : 'bg-red-400'
        }`}></div>
        {isCheckedIn ? 'Checked In' : 'Checked Out'}
        {lastEventTime && (
          <span className="ml-2 text-xs opacity-75">
            at {formatDateTime(lastEventTime)}
          </span>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout title="Dashboard" subtitle="System Overview">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Dashboard" subtitle="System Overview">
        <Card>
          <div className="text-center py-8">
            <div className="text-red-500 mb-4">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-xl font-semibold text-heading">Error Loading Dashboard</p>
              <p className="text-body mt-2">{error}</p>
            </div>
            <Button onClick={loadDashboardData}>
              Try Again
            </Button>
          </div>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard" subtitle="System Overview">
      <div className="space-y-6">
        {/* Welcome Section */}
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-heading mb-2">
                Welcome back!
              </h2>
              <p className="text-body">
                You're logged in as <span className="font-medium text-blue-600">{userRole.replace('_', ' ')}</span>
              </p>
            </div>
            <div className="text-right">
              <p className="text-muted text-sm">Current Status</p>
              {dashboardData.userStatus && (
                <StatusBadge 
                  status={dashboardData.userStatus.status} 
                  lastEventTime={dashboardData.userStatus.last_event_time}
                />
              )}
            </div>
          </div>
        </Card>

        {/* Stats Grid */}
        {(isAdmin || isSuperAdmin) && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Total Employees"
              value={dashboardData.totalEmployees}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              }
              color="blue"
              subtitle="Registered users"
            />

            <StatCard
              title="Active Cameras"
              value={dashboardData.activeCameras}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              }
              color="green"
              subtitle="Currently running"
            />

            {isSuperAdmin && dashboardData.trackerStatus && (
              <>
                <StatCard
                  title="Tracker Status"
                  value={dashboardData.trackerStatus.global_status === 'running' ? 'Running' : 'Stopped'}
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  }
                  color={dashboardData.trackerStatus.global_status === 'running' ? 'green' : 'red'}
                  subtitle="Face recognition"
                />

                <StatCard
                  title="System Health"
                  value="Healthy"
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                  color="green"
                  subtitle="All systems operational"
                />
              </>
            )}
          </div>
        )}

        {/* Recent Activity */}
        {isAdmin && dashboardData.recentAttendance.length > 0 && (
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-heading">Recent Activity</h3>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </div>
            <div className="space-y-3">
              {dashboardData.recentAttendance.map((record) => (
                <div key={record.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      record.event_type === 'check_in' ? 'bg-green-400' : 'bg-red-400'
                    }`}></div>
                    <div>
                      <p className="font-medium text-heading">{record.employee_name || 'Unknown User'}</p>
                      <p className="text-sm text-muted">
                        {record.event_type === 'check_in' ? 'Checked in' : 'Checked out'} via {record.camera_name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted">{formatDateTime(record.event_timestamp)}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Quick Actions */}
        <Card>
          <h3 className="text-lg font-semibold text-heading mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center">
              <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>View Attendance</span>
            </Button>

            {isAdmin && (
              <Button variant="outline" className="h-auto p-4 flex flex-col items-center">
                <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Live Feed</span>
              </Button>
            )}

            {isSuperAdmin && (
              <Button variant="outline" className="h-auto p-4 flex flex-col items-center">
                <svg className="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>System Control</span>
              </Button>
            )}
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default Dashboard;