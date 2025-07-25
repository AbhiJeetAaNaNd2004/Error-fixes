import React, { useState, useEffect, useCallback, useRef } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { getStatusColor, getStatusText, handleApiError } from '../utils/helpers';

const SystemControl = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [trackerStatus, setTrackerStatus] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [systemSettings, setSystemSettings] = useState({});
  const [actionLoading, setActionLoading] = useState(false);
  const pollingIntervalRef = useRef(null);

  const loadSystemData = useCallback(async (isInitialLoad = false) => {
    // Only show the full-page spinner on the very first load
    if (isInitialLoad) {
      setLoading(true);
    }
    setError('');
  
    try {
      const [trackerData, camerasData, settingsData] = await Promise.all([
        apiService.getTrackerStatus(),
        apiService.getCameras(),
        apiService.getSystemSettings().catch(() => ({}))
      ]);
  
      const camerasWithStatus = camerasData.map(camera => ({
        ...camera,
        status: trackerData.camera_statuses ? trackerData.camera_statuses[camera.id] || 'stopped' : 'stopped'
      }));
  
      setTrackerStatus(trackerData);
      setCameras(camerasWithStatus);
      setSystemSettings(settingsData);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load system data'));
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadSystemData(true); // Call it as an initial load
  }, [loadSystemData]);

  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const startStatusPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    let pollCount = 0;
    const maxPolls = 15;

    pollingIntervalRef.current = setInterval(() => {
      pollCount++;
      loadSystemData();

      if (pollCount >= maxPolls) {
        clearInterval(pollingIntervalRef.current);
        setActionLoading(false);
      }
    }, 2000);
  };

  const handleStartTracker = async () => {
    setActionLoading(true);
    try {
      await apiService.startTracker();
      startStatusPolling();
    } catch (err) {
      setError(handleApiError(err, 'Failed to start tracker'));
      setActionLoading(false);
    }
  };

  const handleStopTracker = async () => {
    if (!window.confirm('Are you sure you want to stop the tracking service?')) {
      return;
    }
    setActionLoading(true);
    try {
      await apiService.stopTracker();
      startStatusPolling();
    } catch (err) {
      setError(handleApiError(err, 'Failed to stop tracker'));
      setActionLoading(false);
    }
  };

  const handleStartCamera = async (cameraId) => {
    setActionLoading(true);
    try {
      await apiService.startCamera(cameraId);
      await loadSystemData();
    } catch (err) {
      setError(handleApiError(err, 'Failed to start camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopCamera = async (cameraId) => {
    setActionLoading(true);
    try {
      await apiService.stopCamera(cameraId);
      await loadSystemData();
    } catch (err) {
      setError(handleApiError(err, 'Failed to stop camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const getSystemStats = () => {
    const totalCameras = cameras.length;
    const runningCameras = cameras.filter(cam => cam.status === 'running').length;
    const stoppedCameras = totalCameras - runningCameras;

    return {
      totalCameras,
      runningCameras,
      stoppedCameras
    };
  };

  if (loading) {
    return (
      <Layout title="System Control" subtitle="Manage tracking service and system settings">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  const stats = getSystemStats();

  return (
    <Layout title="System Control" subtitle="Manage tracking service and system settings">
      <div className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <Card title="Face Recognition Tracker">
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-heading">Service Status</h3>
                <p className={`text-2xl font-bold ${
                  trackerStatus?.is_service_running ? 'text-green-600' : 'text-red-600'
                }`}>
                  {trackerStatus?.is_service_running ? 'Running' : 'Stopped'}
                </p>
                {trackerStatus?.message && (
                  <p className="text-sm text-muted mt-1">{trackerStatus.message}</p>
                )}
              </div>
              <div className="flex space-x-3">
                {trackerStatus?.is_service_running ? (
                  <Button variant="danger" onClick={handleStopTracker} disabled={actionLoading}>
                    {actionLoading ? 'Stopping...' : 'Stop Tracker'}
                  </Button>
                ) : (
                  <Button variant="success" onClick={handleStartTracker} disabled={actionLoading}>
                    {actionLoading ? 'Starting...' : 'Start Tracker'}
                  </Button>
                )}
              </div>
            </div>

            {trackerStatus?.details && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <p className="text-sm text-muted">Uptime</p>
                  <p className="text-lg font-semibold text-heading">
                    {trackerStatus.details.uptime || 'N/A'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted">Processed Frames</p>
                  <p className="text-lg font-semibold text-heading">
                    {trackerStatus.details.processed_frames || 'N/A'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted">Recognition Events</p>
                  <p className="text-lg font-semibold text-heading">
                    {trackerStatus.details.recognition_events || 'N/A'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Total Cameras">
            <div className="text-center">
              <p className="text-3xl font-bold text-indigo-600">{stats.totalCameras}</p>
              <p className="text-sm text-muted">Configured</p>
            </div>
          </Card>

          <Card title="Running Cameras">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{stats.runningCameras}</p>
              <p className="text-sm text-muted">Active</p>
            </div>
          </Card>

          <Card title="Stopped Cameras">
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{stats.stoppedCameras}</p>
              <p className="text-sm text-muted">Inactive</p>
            </div>
          </Card>
        </div>
        
        <Card title="Individual Camera Control">
          <div className="space-y-4">
            {cameras.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted">No cameras configured.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {cameras.map((camera) => (
                  <div key={camera.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
                    <div>
                      <h4 className="font-medium text-heading">{camera.camera_name}</h4>
                      <p className="text-sm text-muted">ID: {camera.id}</p>
                      <p className="text-sm text-muted">Location: {camera.location || 'N/A'}</p>
                      <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        camera.status === 'running' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {getStatusText(camera.status)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4">
                      {camera.status === 'running' ? (
                        <Button size="sm" variant="danger" onClick={() => handleStopCamera(camera.id)} disabled={actionLoading}>
                          Stop
                        </Button>
                      ) : (
                        <Button size="sm" variant="success" onClick={() => handleStartCamera(camera.id)} disabled={actionLoading}>
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="System Settings">
          <div className="space-y-4">
            {Object.keys(systemSettings).length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted">System settings not available.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(systemSettings).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-3 bg-gray-50 rounded-md border">
                    <span className="text-sm font-medium text-gray-600">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <span className="text-sm text-heading font-mono">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card title="System Actions">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button
              variant="success"
              onClick={() => loadSystemData(true)}
              disabled={loading}
              fullWidth
            >
              {loading ? 'Refreshing...' : 'Refresh System Status'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => window.location.reload()}
              fullWidth
            >
              Reload Application
            </Button>
          </div>
        </Card>
      </div>
    </Layout>
  );
};

export default SystemControl;