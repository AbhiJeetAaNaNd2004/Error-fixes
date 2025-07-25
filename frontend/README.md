# Face Recognition System - React Frontend

A comprehensive React-based frontend dashboard for the Face Recognition System with role-based access control.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication
- Role-based access control (Employee, Admin, Super Admin)
- Secure route protection
- Automatic token management

### 👥 User Roles & Capabilities

#### Employee (Basic User)
- ✅ Personal dashboard with status overview
- ✅ View personal attendance logs
- ✅ Check current attendance status
- ✅ View last activity timestamp

#### Admin
- ✅ All Employee features
- ✅ User management (create, delete employees)
- ✅ Face enrollment and management
- ✅ View all users' attendance logs
- ✅ Live video feed monitoring
- ✅ System statistics dashboard

#### Super Admin
- ✅ All Admin features
- ✅ Tracker service control (start/stop)
- ✅ Individual camera control
- ✅ Camera management (CRUD operations)
- ✅ Tripwire configuration
- ✅ User role management
- ✅ System settings overview

### 🎯 Core Functionalities

#### Dashboard
- Role-based content display
- Real-time status indicators
- System statistics
- Recent activity logs

#### User Management
- Create new users with role assignment
- Delete user accounts
- Role modification (Super Admin only)
- Face enrollment count display

#### Face Management
- Upload and enroll face images
- View enrolled faces
- Delete face embeddings
- Image preview and validation

#### Live Video Feed
- Real-time camera streaming via WebSocket
- Camera selection interface
- Connection status indicators
- Auto-reconnection on connection loss

#### Camera Management (Super Admin)
- Add/edit/delete cameras
- Start/stop individual cameras
- Tripwire configuration
- Camera status monitoring

#### System Control (Super Admin)
- Face recognition tracker control
- System-wide camera management
- System settings display
- Service status monitoring

## 🛠 Technology Stack

- **Framework**: React 19.1.0
- **Routing**: React Router DOM 6.x
- **Styling**: Tailwind CSS 4.x
- **HTTP Client**: Native Fetch API
- **WebSocket**: Native WebSocket API
- **State Management**: React Hooks (useState, useEffect)

## 📁 Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.js
│   │   │   ├── Navigation.js
│   │   │   └── Layout.js
│   │   ├── UI/
│   │   │   ├── Button.js
│   │   │   ├── Input.js
│   │   │   ├── Card.js
│   │   │   ├── Modal.js
│   │   │   └── LoadingSpinner.js
│   │   └── ProtectedRoute.js
│   ├── pages/
│   │   ├── Login.js
│   │   ├── Dashboard.js
│   │   ├── Attendance.js
│   │   ├── UserManagement.js
│   │   ├── FaceManagement.js
│   │   ├── CameraManagement.js
│   │   ├── SystemControl.js
│   │   └── LiveFeed.js
│   ├── services/
│   │   └── api.js
│   ├── utils/
│   │   ├── auth.js
│   │   └── helpers.js
│   ├── App.js
│   ├── index.js
│   └── index.css
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## 🚀 Getting Started

### Prerequisites
- Node.js 16.x or higher
- npm or yarn
- Running FastAPI backend server

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure API endpoint**:
   Update the `API_BASE_URL` in `src/services/api.js` if your backend runs on a different port:
   ```javascript
   const API_BASE_URL = 'http://localhost:8000';
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Access the application**:
   Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## 🔧 Configuration

### API Service Configuration
The API service is configured in `src/services/api.js`:
- Base URL configuration
- Authentication token management
- Request/response handling
- Error handling

### Route Protection
Routes are protected using the `ProtectedRoute` component:
- Authentication verification
- Role-based access control
- Automatic redirects

### Styling Configuration
Tailwind CSS is configured in `tailwind.config.js`:
- Content paths for purging
- Custom theme extensions
- Plugin configurations

## 🎨 UI Components

### Reusable Components
- **Button**: Multiple variants (primary, secondary, danger, success, outline)
- **Input**: Form input with validation and error states
- **Card**: Container component for content sections
- **Modal**: Overlay dialogs for forms and confirmations
- **LoadingSpinner**: Loading states with different sizes

### Layout Components
- **Header**: Top navigation with user info and logout
- **Navigation**: Sidebar navigation with role-based menu items
- **Layout**: Main layout wrapper combining header and navigation

## 🔒 Security Features

- JWT token storage and management
- Automatic token refresh handling
- Role-based route protection
- Secure API request handling
- Input validation and sanitization

## 📱 Responsive Design

- Mobile-first approach
- Responsive grid layouts
- Adaptive navigation
- Touch-friendly interfaces
- Cross-browser compatibility

## 🔄 Real-time Features

### WebSocket Integration
- Live video streaming
- Automatic reconnection
- Connection status indicators
- Error handling and recovery

### Auto-refresh
- Dashboard data updates
- Status monitoring
- Real-time notifications

## 🐛 Error Handling

- Comprehensive error boundaries
- API error handling
- User-friendly error messages
- Graceful degradation
- Retry mechanisms

## 🧪 Testing

Run tests with:
```bash
npm test
```

## 📝 API Integration

The frontend integrates with the following FastAPI endpoints:

### Authentication
- `POST /auth/token` - User login

### User Management
- `GET /me` - Current user info
- `GET /me/attendance` - User attendance logs
- `GET /me/status` - User status
- `GET /users` - All users (Admin+)
- `POST /users` - Create user (Admin+)
- `DELETE /users/{id}` - Delete user (Admin+)
- `PUT /superadmin/users/{id}/role` - Update role (Super Admin)

### Face Management
- `GET /users/{id}/faces` - User faces
- `POST /users/{id}/faces` - Enroll face
- `DELETE /users/{id}/faces/{face_id}` - Delete face

### Camera Management
- `GET /api/cameras` - All cameras
- `POST /superadmin/cameras` - Create camera
- `PUT /superadmin/cameras/{id}` - Update camera
- `DELETE /superadmin/cameras/{id}` - Delete camera
- `POST /cameras/{id}/start` - Start camera
- `POST /cameras/{id}/stop` - Stop camera

### System Control
- `GET /tracker/status` - Tracker status
- `POST /tracker/start` - Start tracker
- `POST /tracker/stop` - Stop tracker
- `GET /superadmin/settings` - System settings

### WebSocket
- `WS /ws/video_feed/{camera_id}` - Live video stream

## 🤝 Contributing

1. Follow the existing code structure
2. Use consistent naming conventions
3. Add proper error handling
4. Include loading states
5. Test across different roles
6. Maintain responsive design

## 📄 License

This project is part of the Face Recognition System and follows the same licensing terms.

## 🆘 Troubleshooting

### Common Issues

1. **Login fails**: Check if backend server is running on port 8000
2. **Video feed not working**: Verify WebSocket connection and camera status
3. **Styling issues**: Ensure Tailwind CSS is properly configured
4. **Route access denied**: Check user role and route protection settings

### Development Tips

- Use browser developer tools for debugging
- Check network tab for API request/response details
- Monitor console for JavaScript errors
- Verify JWT token in localStorage

---

Built with ❤️ using React and Tailwind CSS
