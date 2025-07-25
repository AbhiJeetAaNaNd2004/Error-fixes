import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { formatDateTime, getStatusColor, getStatusText, handleApiError } from '../utils/helpers';

const Attendance = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attendanceData, setAttendanceData] = useState([]);
  const [userStatus, setUserStatus] = useState(null);

  useEffect(() => {
    loadAttendanceData();
  }, []);

  const loadAttendanceData = async () => {
    setLoading(true);
    setError('');

    try {
      const [attendance, status] = await Promise.all([
        apiService.getUserAttendance(),
        apiService.getUserStatus()
      ]);
      
      setAttendanceData(attendance);
      setUserStatus(status);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load attendance data'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout title="My Attendance" subtitle="Personal attendance records">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="My Attendance" subtitle="Personal attendance records">
        <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded">
          {error}
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="My Attendance" subtitle="Personal attendance records">
      <div className="space-y-6">
        {/* Current Status Card */}
        <Card title="Current Status">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400">Status</p>
              <p className={`text-xl font-semibold ${getStatusColor(userStatus?.status)}`}>
                {getStatusText(userStatus?.status)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-400">Last Activity</p>
              <p className="text-lg text-gray-300">
                {formatDateTime(userStatus?.last_event_time)}
              </p>
            </div>
          </div>
        </Card>

        {/* Attendance History */}
        <Card title="Attendance History">
          {attendanceData.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400">No attendance records found.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Date & Time</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Event</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Camera</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Location</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceData.map((record, index) => (
                    <tr key={index} className="border-b border-gray-700 hover:bg-gray-800">
                      <td className="py-3 px-4 text-sm text-gray-300">
                        {formatDateTime(record.timestamp)}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-sm font-medium ${getStatusColor(record.event_type)}`}>
                          {getStatusText(record.event_type)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-300">
                        {record.camera_name || 'Unknown Camera'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-300">
                        {record.location || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Summary Statistics */}
        {attendanceData.length > 0 && (
          <Card title="This Month Summary">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-indigo-400">
                  {attendanceData.filter(r => r.event_type === 'check_in').length}
                </p>
                <p className="text-sm text-gray-400">Check-ins</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">
                  {attendanceData.filter(r => r.event_type === 'check_out').length}
                </p>
                <p className="text-sm text-gray-400">Check-outs</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-400">
                  {new Set(attendanceData.map(r => new Date(r.timestamp).toDateString())).size}
                </p>
                <p className="text-sm text-gray-400">Active Days</p>
              </div>
            </div>
          </Card>
        )}
      </div>
    </Layout>
  );
};

export default Attendance;