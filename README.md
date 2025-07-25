# 🎯 Face Recognition System

A comprehensive real-time face recognition and attendance management system with multi-camera support, role-based access control, and live video streaming capabilities.

## 📋 **Project Overview**

This system combines a powerful **FastAPI backend** with a modern **React frontend** to deliver enterprise-grade face recognition capabilities. It processes multiple camera streams simultaneously, provides real-time attendance tracking, and offers intuitive dashboards for different user roles.

### 🎥 **Core Capabilities**
- **Real-time face recognition** across multiple camera feeds
- **Automated attendance tracking** with check-in/check-out detection
- **Live video streaming** with WebSocket connections
- **Multi-camera viewing** (1, 2, or 4 feeds simultaneously)
- **Role-based access control** (Employee, Admin, Super Admin)
- **Face enrollment and management** system
- **Camera and tripwire configuration** tools
- **System monitoring and control** dashboards

---

## 🏗️ **System Architecture**

### **Backend Stack**
- **Framework**: FastAPI 0.104+ with Python 3.8+
- **Database**: PostgreSQL 13+
- **Authentication**: JWT tokens with role-based access
- **Face Recognition**: InsightFace with GPU acceleration
- **Video Processing**: OpenCV with multi-threading
- **WebSocket**: Real-time video streaming

### **Frontend Stack**
- **Framework**: React 19.1.0 with functional components
- **Routing**: React Router DOM 6.x
- **Styling**: Tailwind CSS 4.x
- **HTTP Client**: Native Fetch API (no external libraries)
- **WebSocket**: Native WebSocket API
- **State Management**: React Hooks (useState, useEffect)

---

## 👥 **Role-Based Features**

### 🟢 **Employee Dashboard**
**Access Level**: Basic User
- ✅ **Personal Attendance**: View own attendance logs and history
- ✅ **Current Status**: Real-time check-in/check-out status display
- ✅ **Profile Picture**: Automatic display from enrolled face images
- ✅ **Activity Summary**: Personal attendance statistics

**Example Status Display**:
```
Status: Checked In (at 10:45 AM)
Last Activity: 2 hours ago
Today's Hours: 6h 23m
```

### 🟡 **Admin Dashboard**
**Access Level**: Employee + Admin Features
- ✅ **All Employee Features**
- ✅ **User Management**: Create/delete employee accounts
- ✅ **Face Enrollment**: Upload and manage face images (3-5 per user)
- ✅ **System Statistics**: Total employees, active cameras count
- ✅ **Activity Monitoring**: View all users' attendance logs
- ✅ **Live Video Feed**: Single camera viewing with annotations
- ✅ **Profile Management**: View user profiles with face image counts

**Dashboard Widgets**:
- Total Employees: 47 users
- Active Cameras: 3 of 5 running
- Today's Check-ins: 42 employees
- Recent Activity: Live feed

### 🔴 **Super Admin Dashboard**
**Access Level**: Full System Control
- ✅ **All Admin Features**
- ✅ **Tracker Control**: Start/stop global face recognition service
- ✅ **Camera Management**: Add, configure, and delete cameras
- ✅ **Individual Camera Control**: Start/stop specific camera feeds
- ✅ **Multi-Camera Viewing**: View 1, 2, or 4 feeds simultaneously
- ✅ **Tripwire Configuration**: Set up detection zones and boundaries
- ✅ **User Role Management**: Create admin accounts, change user roles
- ✅ **System Settings**: View recognition thresholds and parameters

**Advanced Controls**:
```
🟢 Tracker Service: Running
📹 Camera Status: 3/5 Active
⚙️ Recognition Threshold: 0.75
🎯 Tripwires: 8 configured
👥 Admin Users: 3 active
```

---

## 🚀 **Quick Start Guide**

### **Prerequisites**
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **PostgreSQL 13+** database server
- **GPU support** (optional, for better performance)

### **1. Backend Setup**

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database (update DB_SETTINGS in db/db_utils.py)
# Default: postgresql://postgres:password@localhost:5432/face_recognition_db

# Run database migrations
python scripts/init_db.py

# Start the FastAPI server
python main.py
# Server runs on: http://localhost:8000
```

### **2. Frontend Setup**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the React development server
npm start
# Application runs on: http://localhost:3000
```

### **3. Access the System**

1. **Open browser**: Navigate to `http://localhost:3000`
2. **Login**: Use your credentials (default admin setup required)
3. **Dashboard**: Access role-appropriate features

---

## 📡 **API Documentation**

### **Authentication**
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "admin"
}
```

### **Employee Endpoints**
```http
GET /employee/me/attendance          # Personal attendance logs
GET /employee/me/status              # Current check-in status
```

### **Admin Endpoints**
```http
GET /superadmin/users                # List all users
POST /admin/users/create/employee    # Create employee account
POST /admin/faces/enroll/{user_id}   # Enroll face images (3-5 files)
GET /admin/faces/{user_id}           # Get user's face images
DELETE /admin/faces/{embedding_id}   # Delete specific face embedding
```

### **Super Admin Endpoints**
```http
POST /superadmin/tracker/start       # Start recognition service
POST /superadmin/tracker/stop        # Stop recognition service
GET /superadmin/tracker/status       # Get service status

POST /superadmin/cameras/{id}/start  # Start individual camera
POST /superadmin/cameras/{id}/stop   # Stop individual camera

POST /superadmin/cameras             # Create new camera
PUT /superadmin/cameras/{id}         # Update camera config
DELETE /superadmin/cameras/{id}      # Delete camera
```

### **WebSocket Streaming**
```javascript
// Connect to live video feed
const ws = new WebSocket('ws://localhost:8000/ws/video_feed/1?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  const frameData = event.data; // Base64 encoded image
  displayFrame(`data:image/jpeg;base64,${frameData}`);
};
```

---

## 🎬 **Multi-Camera Viewing**

### **Layout Options**
- **Single View**: Full-screen single camera feed
- **Split View**: Two cameras side-by-side
- **Quad View**: 2x2 grid with four camera feeds

### **Implementation**
```javascript
// React state structure for multi-feed
const [feedConfig, setFeedConfig] = useState({
  layout: 'quad', // 'single', 'split', 'quad'
  feeds: [
    { id: 1, cameraId: 1, connected: true },
    { id: 2, cameraId: 3, connected: true },
    { id: 3, cameraId: 5, connected: false },
    { id: 4, cameraId: null, connected: false },
  ]
});

// Each feed maintains its own WebSocket connection
const connectToCamera = (feedId, cameraId) => {
  const token = getAuthToken();
  const ws = new WebSocket(`ws://localhost:8000/ws/video_feed/${cameraId}?token=${token}`);
  
  ws.onmessage = (event) => {
    updateFeedFrame(feedId, event.data);
  };
};
```

### **Features**
- ✅ **Concurrent Connections**: Multiple WebSocket streams
- ✅ **Dynamic Camera Selection**: Change cameras per feed slot
- ✅ **Layout Switching**: Change view layouts on-the-fly
- ✅ **Connection Management**: Auto-reconnection on failure
- ✅ **Performance Optimized**: Efficient frame handling

---

## 👤 **Profile Picture System**

### **Implementation**
Profile pictures are automatically generated from enrolled face images:

```javascript
// Get user's profile picture (first enrolled face image)
async getUserProfilePicture(userId) {
  try {
    const faces = await apiService.getUserFaces(userId);
    if (faces && faces.length > 0) {
      // Convert bytes to base64 for display
      const imageBytes = faces[0].source_image;
      return `data:image/jpeg;base64,${btoa(String.fromCharCode(...imageBytes))}`;
    }
    return null; // Use default avatar
  } catch (error) {
    return null;
  }
}
```

### **Display Locations**
- Employee dashboard header
- User management tables
- Attendance logs
- Profile pages

---

## 🔧 **Configuration**

### **Backend Configuration**
Edit `backend/config.json`:
```json
{
  "api": {
    "recognition_threshold": 0.75,
    "max_concurrent_streams": 10,
    "frame_rate": 30,
    "gpu_enabled": true
  },
  "cameras": [
    {
      "id": 1,
      "name": "Main Entrance",
      "stream_url": "rtsp://192.168.1.100:554/stream",
      "tripwires": [
        {
          "name": "Entry Line",
          "direction": "horizontal",
          "position": 0.5
        }
      ]
    }
  ]
}
```

### **Frontend Configuration**
Update `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000'; // Backend URL
```

### **Database Configuration**
Update `backend/db/db_utils.py`:
```python
DB_SETTINGS = {
    "dbname": "face_recognition_db",
    "user": "postgres", 
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}
```

---

## 🏭 **Production Deployment**

### **Backend Deployment**
```bash
# Install production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Or with Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **Frontend Deployment**
```bash
# Build for production
npm run build

# Serve with nginx or any static file server
# Build files will be in the 'build/' directory
```

### **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend (React)
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### **Environment Variables**
```bash
# Backend
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export SECRET_KEY="your-super-secret-key"
export ENVIRONMENT="production"

# Frontend
export REACT_APP_API_URL="https://your-api-domain.com"
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Backend Issues**
```bash
# Database connection failed
# ✅ Check PostgreSQL is running
sudo systemctl status postgresql

# ✅ Verify database credentials in db_utils.py
# ✅ Ensure database exists
createdb face_recognition_db
```

#### **Frontend Issues**
```bash
# Login fails with network error
# ✅ Verify backend is running on port 8000
curl http://localhost:8000/

# ✅ Check CORS settings in main.py
# ✅ Verify API_BASE_URL in api.js
```

#### **Video Streaming Issues**
```bash
# WebSocket connection fails
# ✅ Check camera permissions and URLs
# ✅ Verify JWT token is valid
# ✅ Ensure user has admin/super_admin role
```

#### **Face Recognition Issues**
```bash
# No faces detected during enrollment
# ✅ Use clear, well-lit images
# ✅ Ensure face is clearly visible and forward-facing
# ✅ Upload 3-5 different images per person
```

### **Performance Optimization**
- **GPU Acceleration**: Enable CUDA for faster face processing
- **Database Indexing**: Add indexes on frequently queried columns
- **Caching**: Implement Redis for session and frame caching
- **Load Balancing**: Use multiple backend instances for high load

---

## 🧪 **Testing**

### **Backend Testing**
```bash
# Run API tests
python -m pytest tests/

# Test specific endpoints
curl -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=password"
```

### **Frontend Testing**
```bash
# Run component tests
npm test

# Run integration tests
npm run test:integration

# Build verification
npm run build
```

### **System Integration Testing**
1. **Authentication Flow**: Login with different roles
2. **Video Streaming**: Test WebSocket connections
3. **Face Enrollment**: Upload and process images
4. **Multi-Camera**: Test concurrent video feeds
5. **Role Permissions**: Verify access controls

---

## 📊 **System Requirements**

### **Minimum Requirements**
- **CPU**: 4 cores, 2.5GHz
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: 100Mbps
- **GPU**: Optional (GTX 1060 or better recommended)

### **Recommended for Production**
- **CPU**: 8+ cores, 3.0GHz+
- **RAM**: 16GB+
- **Storage**: 200GB+ SSD
- **Network**: 1Gbps
- **GPU**: RTX 3060 or better
- **Cameras**: Up to 20 concurrent streams

---

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Follow the coding standards:
   - **Backend**: PEP 8 for Python
   - **Frontend**: ESLint + Prettier for JavaScript
4. Add tests for new features
5. Submit a pull request

### **Code Style**
```python
# Backend: Use type hints and docstrings
def create_user(user_data: UserCreate) -> UserResponse:
    """Creates a new user with the specified role."""
    pass
```

```javascript
// Frontend: Use functional components with hooks
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  // Component logic here
};
```

---

## 📄 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Face Recognition System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 📞 **Support & Contact**

### **Documentation**
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Integration Guide**: [INTEGRATION_ANALYSIS.md](INTEGRATION_ANALYSIS.md)
- **Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

### **Support Channels**
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: support@facerecognition.com

### **Maintenance**
- **Version**: 1.5.0
- **Last Updated**: December 2024
- **Maintainer**: Development Team
- **Status**: ✅ Active Development

---

## 🔄 **Version History**

### **v1.5.0** (Current)
- ✅ Multi-camera viewing support
- ✅ Enhanced role-based access control
- ✅ Profile picture system
- ✅ Improved WebSocket stability
- ✅ React 19 compatibility

### **v1.4.0**
- ✅ Face enrollment system
- ✅ Camera management UI
- ✅ Tripwire configuration
- ✅ System monitoring dashboard

### **v1.3.0**
- ✅ Live video streaming
- ✅ WebSocket integration
- ✅ Real-time attendance tracking

### **v1.2.0**
- ✅ Role-based authentication
- ✅ Admin dashboard
- ✅ User management system

### **v1.1.0**
- ✅ Basic face recognition
- ✅ Employee dashboard
- ✅ Attendance logging

### **v1.0.0**
- ✅ Initial release
- ✅ Core system architecture
- ✅ Database schema

---

## 🌟 **Acknowledgments**

- **InsightFace** - Face recognition models
- **FastAPI** - Modern Python web framework
- **React** - Frontend user interface library
- **Tailwind CSS** - Utility-first CSS framework
- **PostgreSQL** - Robust database system
- **OpenCV** - Computer vision library

---

**Built with ❤️ for enterprise-grade face recognition and attendance management**