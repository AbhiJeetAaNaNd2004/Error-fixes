import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Modal from '../components/UI/Modal';
import LoadingSpinner from '../components/UI/LoadingSpinner';
import apiService from '../services/api';
import { handleApiError } from '../utils/helpers';

const FaceManagement = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userFaces, setUserFaces] = useState([]);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showFacesModal, setShowFacesModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

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

  const loadUserFaces = async (userId) => {
    setActionLoading(true);
    try {
      const faces = await apiService.getUserFaces(userId);
      setUserFaces(faces);
    } catch (err) {
      setError(handleApiError(err, 'Failed to load user faces'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleEnrollFace = async () => {
    if (!selectedFile || !selectedUser) return;

    setActionLoading(true);
    try {
      await apiService.enrollFace(selectedUser.id, selectedFile);
      setShowEnrollModal(false);
      setSelectedFile(null);
      setPreviewUrl(null);
      await loadUsers(); // Refresh to update face count
    } catch (err) {
      setError(handleApiError(err, 'Failed to enroll face'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteFace = async (faceId) => {
    if (!window.confirm('Are you sure you want to delete this face?')) return;

    // Store the current state in case we need to revert
    const originalFaces = userFaces;
    // Optimistically remove the face from the UI immediately
    setUserFaces(currentFaces => currentFaces.filter(face => face.id !== faceId));

    try {
      await apiService.deleteFaceEmbedding(faceId);
      // On success, just refresh the user list to update the face count
      await loadUsers();
    } catch (err) {
      // Check if the error is a 404 (Not Found)
      if (err.message && err.message.startsWith('404')) {
        // The image was already deleted, so our UI is now correct.
        // We can ignore this error and just refresh the user count.
        console.log('Image was already deleted from server, UI is now in sync.');
        await loadUsers();
      } else {
        // For any other error, show a message and revert the UI change
        setError(handleApiError(err, 'Failed to delete face'));
        setUserFaces(originalFaces);
      }
    }
  };
    // --- NEW FUNCTION ---
  const handleSetProfilePicture = async (embeddingId) => {
    setActionLoading(true);
    try {
        await apiService.setProfilePicture(embeddingId);
        // Optionally, show a success message
        alert('Profile picture updated!');
        closeModals();
    } catch (err) {
        setError(handleApiError(err, 'Failed to set profile picture'));
    } finally {
        setActionLoading(false);
    }
  };

  const openEnrollModal = (user) => {
    setSelectedUser(user);
    setShowEnrollModal(true);
  };

  const openFacesModal = async (user) => {
    setSelectedUser(user);
    setShowFacesModal(true);
    await loadUserFaces(user.id);
  };

  const closeModals = () => {
    setShowEnrollModal(false);
    setShowFacesModal(false);
    setSelectedUser(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setUserFaces([]);
  };

  if (loading) {
    return (
      <Layout title="Face Management" subtitle="Enroll and manage face images">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Face Management" subtitle="Enroll and manage face images">
      <div className="space-y-6">
        {error && (
          <div className="bg-red-900 border border-red-700 text-red-100 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Users Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map((user) => (
            <Card key={user.id} title={user.full_name || user.username}>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="bg-gray-700 rounded-full w-20 h-20 mx-auto flex items-center justify-center mb-3">
                    <span className="text-2xl text-gray-400">👤</span>
                  </div>
                  <p className="text-sm text-gray-400">@{user.username}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>

                <div className="text-center">
                  <span className="bg-indigo-600 text-white px-3 py-1 rounded-full text-sm">
                    {user.face_count || 0} enrolled faces
                  </span>
                </div>

                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    fullWidth
                    onClick={() => openEnrollModal(user)}
                  >
                    Enroll Face
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    fullWidth
                    onClick={() => openFacesModal(user)}
                    disabled={!user.face_count}
                  >
                    View Faces
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {users.length === 0 && (
          <Card>
            <div className="text-center py-8">
              <p className="text-gray-400">No users found.</p>
            </div>
          </Card>
        )}

        {/* Enroll Face Modal */}
        <Modal
          isOpen={showEnrollModal}
          onClose={closeModals}
          title={`Enroll Face for ${selectedUser?.full_name || selectedUser?.username}`}
          footer={
            <>
              <Button variant="secondary" onClick={closeModals}>
                Cancel
              </Button>
              <Button
                onClick={handleEnrollFace}
                disabled={!selectedFile || actionLoading}
              >
                {actionLoading ? 'Enrolling...' : 'Enroll Face'}
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Select Face Image
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {previewUrl && (
              <div className="text-center">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="max-w-full max-h-64 mx-auto rounded-md"
                />
              </div>
            )}

            <div className="text-sm text-gray-400">
              <p>• Use clear, well-lit face images</p>
              <p>• Face should be clearly visible and facing forward</p>
              <p>• Supported formats: JPG, PNG</p>
            </div>
          </div>
        </Modal>

        {/* View Faces Modal */}
        <Modal
          isOpen={showFacesModal}
          onClose={closeModals}
          title={`Face Images for ${selectedUser?.full_name || selectedUser?.username}`}
        >
          <div className="space-y-4">
            {actionLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : userFaces.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">No face images found.</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                {userFaces.map((face, index) => (
                  <div key={face.id || index} className="relative">
                    <img
                      src={`data:image/jpeg;base64,${face.source_image}`}
                      alt={`Face ${index + 1}`}
                      className="w-full h-32 object-cover rounded-md"
                    />
                    <Button
                      size="sm"
                      variant="danger"
                      className="absolute top-2 right-2"
                      onClick={() => handleDeleteFace(face.id)}
                      disabled={actionLoading}
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Modal>
      </div>
    </Layout>
  );
};

export default FaceManagement;