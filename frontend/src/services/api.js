const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies in all requests
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(`${response.status}: ${errorData.detail || 'Request failed'}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return await response.text();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // All requests now use the same method since authentication is handled by cookies
  async authenticatedRequest(endpoint, options = {}) {
    return this.request(endpoint, options);
  }

  // Auth endpoints
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    return this.request('/auth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });
  }
    // --- DEPARTMENT METHODS ---
  async getDepartments() {
    return this.authenticatedRequest('/superadmin/departments');
  }
  async createDepartment(departmentName) {
    return this.authenticatedRequest('/superadmin/departments', {
      method: 'POST', body: JSON.stringify({ department_name: departmentName }),
    });
  }
  async updateDepartment(departmentId, newName) {
    return this.authenticatedRequest(`/superadmin/departments/${departmentId}`, {
      method: 'PUT', body: JSON.stringify({ department_name: newName }),
    });
  }
  async deleteDepartment(departmentId) {
    return this.authenticatedRequest(`/superadmin/departments/${departmentId}`, { method: 'DELETE' });
  }
  async assignUserDepartment(userId, departmentId) {
    return this.authenticatedRequest('/admin/users/department', {
      method: 'PUT', body: JSON.stringify({ user_id: userId, department_id: departmentId }),
    });
  }

  // Logout endpoint to clear the httpOnly cookie
  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  // User endpoints - Cookie-based authentication
  async getCurrentUser() {
    return this.authenticatedRequest('/me');
  }

  async getUserAttendance() {
    return this.authenticatedRequest('/employee/me/attendance');
  }

  async getUserStatus() {
    return this.authenticatedRequest('/employee/me/status');
  }

  // User management endpoints
  async getAllUsers() {
    return this.authenticatedRequest('/superadmin/users');
  }

  async createEmployee(userData) {
    return this.authenticatedRequest('/admin/users/create/employee', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async createAdmin(userData) {
    return this.authenticatedRequest('/superadmin/users/create/admin', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async deleteUser(userId) {
    return this.authenticatedRequest(`/superadmin/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async updateUserRole(userId, role) {
    return this.authenticatedRequest(`/superadmin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  // Face management endpoints
  async getUserFaces(userId) {
    return this.authenticatedRequest(`/admin/faces/${userId}`);
  }

  async enrollFaces(userId, imageFiles) {
    const formData = new FormData();
    // Backend expects multiple files with 'images' field name
    imageFiles.forEach(file => formData.append('images', file));

    return fetch(`${this.baseURL}/admin/faces/enroll/${userId}`, {
      method: 'POST',
      credentials: 'include', // Include cookies for authentication
      body: formData,
    }).then(response => {
      if (!response.ok) {
        throw new Error('Face enrollment failed');
      }
      return response.json();
    });
  }

  async deleteFaceEmbedding(embeddingId) {
    return this.authenticatedRequest(`/admin/faces/${embeddingId}`, {
      method: 'DELETE',
    });
  }

  // Profile picture helper
  async getUserProfilePicture(userId) {
    try {
      const faces = await this.getUserFaces(userId);
      if (faces && faces.length > 0) {
        // Convert bytes to base64 for display
        const imageBytes = faces[0].source_image;
        // Handle different data formats
        if (typeof imageBytes === 'string') {
          return `data:image/jpeg;base64,${imageBytes}`;
        } else if (imageBytes instanceof ArrayBuffer || Array.isArray(imageBytes)) {
          const base64String = btoa(String.fromCharCode(...new Uint8Array(imageBytes)));
          return `data:image/jpeg;base64,${base64String}`;
        }
      }
      return null; // No profile picture available
    } catch (error) {
      console.warn(`Could not load profile picture for user ${userId}:`, error);
      return null;
    }
  }

  // Camera endpoints
  async getCameras() {
    return this.authenticatedRequest('/api/cameras');
  }

  async createCamera(cameraData) {
    return this.authenticatedRequest('/superadmin/cameras', {
      method: 'POST',
      body: JSON.stringify(cameraData),
    });
  }

  async updateCamera(cameraId, cameraData) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}`, {
      method: 'PUT',
      body: JSON.stringify(cameraData),
    });
  }

  async deleteCamera(cameraId) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}`, {
      method: 'DELETE',
    });
  }

  async startCamera(cameraId) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/start`, {
      method: 'POST',
    });
  }

  async stopCamera(cameraId) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/stop`, {
      method: 'POST',
    });
  }

  // Tracker endpoints
  async getTrackerStatus() {
    return this.authenticatedRequest('/superadmin/tracker/status');
  }

  async startTracker() {
    return this.authenticatedRequest('/superadmin/tracker/start', {
      method: 'POST',
    });
  }

  async stopTracker() {
    return this.authenticatedRequest('/superadmin/tracker/stop', {
      method: 'POST',
    });
  }

  // Tripwire endpoints
  async getTripwires(cameraId) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/tripwires`);
  }

  async createTripwire(cameraId, tripwireData) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/tripwires`, {
      method: 'POST',
      body: JSON.stringify(tripwireData),
    });
  }

  async updateTripwire(cameraId, tripwireId, tripwireData) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/tripwires/${tripwireId}`, {
      method: 'PUT',
      body: JSON.stringify(tripwireData),
    });
  }

  async deleteTripwire(cameraId, tripwireId) {
    return this.authenticatedRequest(`/superadmin/cameras/${cameraId}/tripwires/${tripwireId}`, {
      method: 'DELETE',
    });
  }

  // System settings
  async getSystemSettings() {
    return this.authenticatedRequest('/superadmin/settings');
  }

  // Attendance logs
  async getAllAttendanceLogs() {
    return this.authenticatedRequest('/admin/attendance');
  }
    // --- NEW PROFILE PICTURE METHODS ---

  async getProfilePicture() {
    // This assumes you want the logged-in user's picture.
    // For admins getting other users' pictures, a different endpoint would be needed.
    return this.authenticatedRequest('/employee/me/profile-picture');
  }

  async setProfilePicture(embeddingId) {
    return this.authenticatedRequest(`/employee/me/profile-picture/${embeddingId}`, {
      method: 'PUT',
    });
  }

  async uploadProfilePicture(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);

    // Note: We use fetch directly for multipart/form-data
    return fetch(`${this.baseURL}/employee/me/profile-picture`, {
      method: 'POST',
      credentials: 'include', // Important for cookie-based auth
      body: formData,
    }).then(response => {
      if (!response.ok) {
        throw new Error('Profile picture upload failed');
      }
      return response.json();
    });
  }

  // Multi-camera WebSocket helper - Updated for cookie-based auth
  createVideoWebSocket(cameraId) {
    // Cookies are automatically sent with WebSocket connections to the same domain
    const wsUrl = `ws://localhost:8000/ws/video_feed/${cameraId}`;
    return new WebSocket(wsUrl);
  }

  // Batch operations for multi-camera support
  async getMultipleCameraFeeds(cameraIds) {
    const connections = [];
    
    cameraIds.forEach(cameraId => {
      if (cameraId) {
        const ws = this.createVideoWebSocket(cameraId);
        connections.push({ cameraId, ws });
      }
    });
    
    return connections;
  }
}

const apiService = new ApiService();
export default apiService;