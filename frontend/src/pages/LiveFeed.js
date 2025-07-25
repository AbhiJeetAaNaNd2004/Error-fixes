//LiveFeed.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { useNotifications } from '../utils/helpers';

const LiveFeed = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cameras, setCameras] = useState([]);
  const [selectedCameraId, setSelectedCameraId] = useState('');
  const [frame, setFrame] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  
  // NEW: Toggle states for display options
  const [showBboxes, setShowBboxes] = useState(true);
  const [showTripwires, setShowTripwires] = useState(false);
  
  const ws = useRef(null);
  const { success, error: notifyError } = useNotifications();

  const loadCameras = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const camerasData = await apiService.getCameras();
      setCameras(camerasData);
      if (camerasData.length > 0) {
        setSelectedCameraId(camerasData[0].id);
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to load cameras';
      setError(errorMessage);
      notifyError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [notifyError]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close(1000, 'User disconnected');
      ws.current = null;
    }
    setIsConnected(false);
    setFrame(null);
    setConnectionError('');
  }, []);

  // UPDATED: Connect function with toggle parameters
  const connect = useCallback(() => {
    if (!selectedCameraId) return;
    
    disconnect(); // Close existing connection

    try {
      // FIXED: Use dynamic URL construction and include toggle parameters
      const ws = apiService.createVideoWebSocket(selectedCameraId, showTripwires, showBboxes);
      ws.current = ws;

      ws.current.onopen = () => {
        console.log('WebSocket Connected');
        setIsConnected(true);
        setConnectionError('');
        success('Connected to camera feed');
      };

      ws.current.onmessage = (event) => {
        setFrame(event.data);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket Disconnected', event.code, event.reason);
        setIsConnected(false);
        if (event.code !== 1000) { // Not a normal closure
          setConnectionError('Connection lost. Attempting to reconnect...');
          // Auto-reconnect after 3 seconds
          setTimeout(() => {
            if (selectedCameraId) {
              connect();
            }
          }, 3000);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket Error:', error);
        setIsConnected(false);
        setConnectionError('Connection error occurred');
        notifyError('Video stream connection failed');
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError('Failed to connect to video stream');
      notifyError('Failed to connect to video stream');
    }
  }, [selectedCameraId, showTripwires, showBboxes, disconnect, success, notifyError]);

  useEffect(() => {
    loadCameras();
    return () => {
      disconnect();
    };
  }, [loadCameras, disconnect]);

  // UPDATED: Reconnect when toggle states change
  useEffect(() => {
    if (selectedCameraId && isConnected) {
      connect(); // Reconnect with new settings
    } else if (selectedCameraId && !isConnected) {
      // Only connect if not already connected
      connect();
    } else {
      disconnect();
    }
    return () => disconnect();
  }, [selectedCameraId, connect, disconnect]);

  const handleCameraChange = (cameraId) => {
    setSelectedCameraId(cameraId);
  };

  // NEW: Toggle handlers
  const handleBboxToggle = () => {
    setShowBboxes(prev => !prev);
  };

  const handleTripwireToggle = () => {
    setShowTripwires(prev => !prev);
  };

  const getSelectedCamera = () => {
    return cameras.find(cam => cam.id === selectedCameraId);
  };

  if (loading) {
    return (
      <Layout title="Live Video Feed" subtitle="Real-time camera streaming">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Live Video Feed" subtitle="Real-time camera streaming">
        <Card>
          <div className="text-center py-8">
            <div className="text-red-400 mb-4">
              <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-xl font-semibold">Error Loading Cameras</p>
              <p className="text-gray-400 mt-2">{error}</p>
            </div>
            <Button onClick={loadCameras}>
              Try Again
            </Button>
          </div>
        </Card>
      </Layout>
    );
  }

  return (
    <Layout title="Live Video Feed" subtitle="Real-time camera streaming">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Camera Selection */}
        <div className="lg:col-span-1">
          <Card>
            <h3 className="text-lg font-semibold text-indigo-400 mb-4">Camera Selection</h3>
            
            <div className="space-y-2">
              {cameras.map((camera) => (
                <button
                  key={camera.id}
                  onClick={() => handleCameraChange(camera.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedCameraId === camera.id
                      ? 'border-indigo-500 bg-indigo-900/20 text-indigo-300'
                      : 'border-gray-600 hover:border-gray-500 text-gray-300'
                  }`}
                >
                  <div className="font-medium">{camera.camera_name}</div>
                  <div className="text-sm text-gray-400">Camera ID: {camera.id}</div>
                </button>
              ))}
            </div>

            {/* Connection Status */}
            <div className="mt-6 p-3 rounded-lg bg-gray-800">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Status:</span>
                <div className={`flex items-center ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                  <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span className="text-sm">{isConnected ? 'Connected' : 'Disconnected'}</span>
                </div>
              </div>
              {connectionError && (
                <div className="mt-2 text-sm text-yellow-400">
                  {connectionError}
                </div>
              )}
            </div>

            {/* Controls */}
            <div className="mt-4 space-y-2">
              <Button
                onClick={connect}
                disabled={!selectedCameraId || isConnected}
                fullWidth
                size="sm"
              >
                Connect
              </Button>
              <Button
                onClick={disconnect}
                disabled={!isConnected}
                variant="secondary"
                fullWidth
                size="sm"
              >
                Disconnect
              </Button>
            </div>

            {/* NEW: Display Options */}
            <div className="mt-6 p-3 rounded-lg bg-gray-800">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Display Options</h4>
              
              <div className="space-y-3">
                {/* Bounding Boxes Toggle */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Bounding Boxes</span>
                  <button
                    onClick={handleBboxToggle}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      showBboxes ? 'bg-indigo-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        showBboxes ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Tripwires Toggle */}
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Tripwires</span>
                  <button
                    onClick={handleTripwireToggle}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      showTripwires ? 'bg-indigo-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        showTripwires ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              <div className="mt-3 text-xs text-gray-400">
                Changes apply on next connection
              </div>
            </div>
          </Card>
        </div>

        {/* Video Feed */}
        <div className="lg:col-span-3">
          <Card>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-indigo-400">
                {getSelectedCamera()?.camera_name || 'Select a camera'}
              </h3>
              <div className={`px-3 py-1 rounded-full text-sm ${
                isConnected ? 'bg-green-900 text-green-300' : 'bg-gray-700 text-gray-300'
              }`}>
                {isConnected ? 'Live' : 'Offline'}
              </div>
            </div>

            <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
              {frame ? (
                <img
                  src={`data:image/jpeg;base64,${frame}`}
                  alt="Live video feed"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    {isConnected ? (
                      <>
                        <LoadingSpinner size="lg" className="mb-4" />
                        <p className="text-gray-400">Waiting for video stream...</p>
                      </>
                    ) : (
                      <>
                        <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        <p className="text-gray-400">
                          {selectedCameraId ? 'Click Connect to start streaming' : 'Select a camera to begin'}
                        </p>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
};

export default LiveFeed;