import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Input from '../components/UI/Input';
import Modal from '../components/UI/Modal';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { getStatusColor, getStatusText, handleApiError } from '../utils/helpers';

const CameraManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [showCameraModal, setShowCameraModal] = useState(false);
  const [showTripwireModal, setShowTripwireModal] = useState(false);
  const [tripwires, setTripwires] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const [cameraForm, setCameraForm] = useState({
    camera_name: '',
    location: '',
    camera_url: '',
    resolution: '',
    fps: 30
  });

  const [tripwireForm, setTripwireForm] = useState({
    name: '',
    coordinates: '',
    direction: 'both'
  });

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    setLoading(true);
    setError('');

    try {
      const camerasData = await apiService.getCameras();
      setCameras(camerasData);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load cameras'));
    } finally {
      setLoading(false);
    }
  };

  const loadTripwires = async (cameraId) => {
    setActionLoading(true);
    try {
      const tripwiresData = await apiService.getTripwires(cameraId);
      setTripwires(tripwiresData);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load tripwires'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCameraInputChange = (e) => {
    const { name, value } = e.target;
    setCameraForm(prev => ({
      ...prev,
      [name]: name === 'fps' ? parseInt(value) || 0 : value
    }));
  };

  const handleTripwireInputChange = (e) => {
    const { name, value } = e.target;
    setTripwireForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateCamera = async (e) => {
    e.preventDefault();
    setActionLoading(true);

    try {
      await apiService.createCamera(cameraForm);
      setShowCameraModal(false);
      resetCameraForm();
      await loadCameras();
    } catch (err) {
      setError(handleApiError(err, 'Failed to create camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateCamera = async (e) => {
    e.preventDefault();
    if (!selectedCamera) return;

    setActionLoading(true);
    try {
      await apiService.updateCamera(selectedCamera.id, cameraForm);
      setShowCameraModal(false);
      resetCameraForm();
      await loadCameras();
    } catch (err) {
      setError(handleApiError(err, 'Failed to update camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteCamera = async (cameraId) => {
    if (!window.confirm('Are you sure you want to delete this camera?')) {
      return;
    }

    setActionLoading(true);
    try {
      await apiService.deleteCamera(cameraId);
      await loadCameras();
    } catch (err) {
      setError(handleApiError(err, 'Failed to delete camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartCamera = async (cameraId) => {
    setActionLoading(true);
    try {
      await apiService.startCamera(cameraId);
      await loadCameras();
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
      await loadCameras();
    } catch (err) {
      setError(handleApiError(err, 'Failed to stop camera'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateTripwire = async (e) => {
    e.preventDefault();
    if (!selectedCamera) return;

    setActionLoading(true);
    try {
      await apiService.createTripwire(selectedCamera.id, tripwireForm);
      setTripwireForm({
        name: '',
        coordinates: '',
        direction: 'both'
      });
      await loadTripwires(selectedCamera.id);
    } catch (err) {
      setError(handleApiError(err, 'Failed to create tripwire'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTripwire = async (tripwireId) => {
    if (!window.confirm('Are you sure you want to delete this tripwire?')) {
      return;
    }

    setActionLoading(true);
    try {
      await apiService.deleteTripwire(selectedCamera.id, tripwireId);
      await loadTripwires(selectedCamera.id);
    } catch (err) {
      setError(handleApiError(err, 'Failed to delete tripwire'));
    } finally {
      setActionLoading(false);
    }
  };

  const openCreateCameraModal = () => {
    setIsEditing(false);
    setSelectedCamera(null);
    resetCameraForm();
    setShowCameraModal(true);
  };

  const openEditCameraModal = (camera) => {
    setIsEditing(true);
    setSelectedCamera(camera);
    setCameraForm({
      camera_name: camera.camera_name || '',
      location: camera.location || '',
      camera_url: camera.camera_url || '',
      resolution: camera.resolution || '',
      fps: camera.fps || 30
    });
    setShowCameraModal(true);
  };

  const openTripwireModal = async (camera) => {
    setSelectedCamera(camera);
    setShowTripwireModal(true);
    await loadTripwires(camera.id);
  };

  const resetCameraForm = () => {
    setCameraForm({
      camera_name: '',
      location: '',
      camera_url: '',
      resolution: '',
      fps: 30
    });
  };

  const closeModals = () => {
    setShowCameraModal(false);
    setShowTripwireModal(false);
    setSelectedCamera(null);
    setTripwires([]);
    resetCameraForm();
    setTripwireForm({
      name: '',
      coordinates: '',
      direction: 'both'
    });
  };

  if (loading) {
    return (
      <Layout title="Camera Management" subtitle="Manage cameras and tripwires">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Camera Management" subtitle="Manage cameras and tripwires">
      <div className="space-y-6">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Actions Bar */}
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-white">Cameras ({cameras.length})</h2>
          <Button onClick={openCreateCameraModal}>
            Add New Camera
          </Button>
        </div>

        {/* Cameras Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cameras.map((camera) => (
            <Card key={camera.id} title={camera.camera_name}>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    camera.status === 'running' 
                      ? 'bg-green-600 text-white' 
                      : 'bg-red-600 text-white'
                  }`}>
                    {getStatusText(camera.status)}
                  </span>
                  <span className="text-xs text-gray-400">ID: {camera.id}</span>
                </div>

                <div className="text-sm text-gray-300 space-y-1">
                  <p><strong>Location:</strong> {camera.location || 'N/A'}</p>
                  <p><strong>Resolution:</strong> {camera.resolution || 'N/A'}</p>
                  <p><strong>FPS:</strong> {camera.fps || 'N/A'}</p>
                  <p><strong>Tripwires:</strong> {camera.tripwire_count || 0}</p>
                </div>

                <div className="flex space-x-2">
                  {camera.status === 'running' ? (
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleStopCamera(camera.id)}
                      disabled={actionLoading}
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="success"
                      onClick={() => handleStartCamera(camera.id)}
                      disabled={actionLoading}
                    >
                      Start
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openTripwireModal(camera)}
                  >
                    Tripwires
                  </Button>
                </div>

                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => openEditCameraModal(camera)}
                    fullWidth
                  >
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDeleteCamera(camera.id)}
                    disabled={actionLoading}
                    fullWidth
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {cameras.length === 0 && (
          <Card>
            <div className="text-center py-8">
              <p className="text-gray-400">No cameras found. Add your first camera to get started.</p>
            </div>
          </Card>
        )}

        {/* Camera Modal */}
        <Modal
          isOpen={showCameraModal}
          onClose={closeModals}
          title={isEditing ? 'Edit Camera' : 'Add New Camera'}
          footer={
            <>
              <Button variant="secondary" onClick={closeModals}>
                Cancel
              </Button>
              <Button
                onClick={isEditing ? handleUpdateCamera : handleCreateCamera}
                disabled={actionLoading}
              >
                {actionLoading ? (isEditing ? 'Updating...' : 'Creating...') : (isEditing ? 'Update' : 'Create')}
              </Button>
            </>
          }
        >
          <form onSubmit={isEditing ? handleUpdateCamera : handleCreateCamera} className="space-y-4">
            <Input
              id="camera_name"
              label="Camera Name"
              value={cameraForm.camera_name}
              onChange={handleCameraInputChange}
              required
              disabled={actionLoading}
            />
            <Input
              id="location"
              label="Location"
              value={cameraForm.location}
              onChange={handleCameraInputChange}
              disabled={actionLoading}
            />
            <Input
              id="camera_url"
              label="Camera URL"
              value={cameraForm.camera_url}
              onChange={handleCameraInputChange}
              placeholder="rtsp://camera-ip:port/stream"
              required
              disabled={actionLoading}
            />
            <Input
              id="resolution"
              label="Resolution"
              value={cameraForm.resolution}
              onChange={handleCameraInputChange}
              placeholder="1920x1080"
              disabled={actionLoading}
            />
            <Input
              id="fps"
              label="FPS"
              type="number"
              value={cameraForm.fps}
              onChange={handleCameraInputChange}
              min="1"
              max="60"
              disabled={actionLoading}
            />
          </form>
        </Modal>

        {/* Tripwire Modal */}
        <Modal
          isOpen={showTripwireModal}
          onClose={closeModals}
          title={`Tripwires for ${selectedCamera?.camera_name}`}
        >
          <div className="space-y-6">
            {/* Create Tripwire Form */}
            <div>
              <h4 className="text-lg font-medium text-white mb-4">Add New Tripwire</h4>
              <form onSubmit={handleCreateTripwire} className="space-y-4">
                <Input
                  id="name"
                  label="Tripwire Name"
                  value={tripwireForm.name}
                  onChange={handleTripwireInputChange}
                  required
                  disabled={actionLoading}
                />
                <Input
                  id="coordinates"
                  label="Coordinates"
                  value={tripwireForm.coordinates}
                  onChange={handleTripwireInputChange}
                  placeholder="x1,y1,x2,y2"
                  required
                  disabled={actionLoading}
                />
                <div>
                  <label htmlFor="direction" className="block text-sm font-medium text-gray-300 mb-1">
                    Direction
                  </label>
                  <select
                    id="direction"
                    name="direction"
                    value={tripwireForm.direction}
                    onChange={handleTripwireInputChange}
                    className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={actionLoading}
                  >
                    <option value="both">Both Directions</option>
                    <option value="enter">Enter Only</option>
                    <option value="exit">Exit Only</option>
                  </select>
                </div>
                <Button type="submit" disabled={actionLoading} fullWidth>
                  {actionLoading ? 'Creating...' : 'Create Tripwire'}
                </Button>
              </form>
            </div>

            {/* Existing Tripwires */}
            <div>
              <h4 className="text-lg font-medium text-white mb-4">Existing Tripwires</h4>
              {actionLoading ? (
                <div className="flex justify-center py-4">
                  <LoadingSpinner />
                </div>
              ) : tripwires.length === 0 ? (
                <p className="text-gray-400 text-center py-4">No tripwires configured.</p>
              ) : (
                <div className="space-y-3">
                  {tripwires.map((tripwire, index) => (
                    <div key={tripwire.id || index} className="flex items-center justify-between p-3 bg-gray-700 rounded-md">
                      <div>
                        <p className="font-medium text-white">{tripwire.name}</p>
                        <p className="text-sm text-gray-400">
                          Coords: {tripwire.coordinates} | Direction: {tripwire.direction}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleDeleteTripwire(tripwire.id)}
                        disabled={actionLoading}
                      >
                        Delete
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      </div>
    </Layout>
  );
};

export default CameraManagement;