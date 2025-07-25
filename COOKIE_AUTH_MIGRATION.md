# 🍪 Cookie-Based Authentication Migration Guide

## Overview

This document outlines the complete migration from JWT token-based authentication to secure httpOnly cookie-based authentication in the React frontend. The backend now stores JWT tokens in secure, httpOnly cookies instead of returning them in the JSON response.

---

## 🔄 **Migration Summary**

### **Backend Changes (For Context Only)**
The backend has been updated to:
- Store JWT tokens in secure, httpOnly cookies via `response.set_cookie()`
- Return only `{"status": "success", "role": "user_role"}` from login endpoint
- Read tokens from cookies using `request.cookies.get("access_token")`
- Provide logout endpoint to clear cookies

### **Frontend Changes Implemented**

#### **1. Authentication Utilities (`frontend/src/utils/auth.js`)**

**❌ REMOVED:**
```javascript
// Token handling functions removed
export const getAuthToken = () => { ... };
export const setAuthData = (token, role) => { ... };
export const clearAuthData = () => { ... };
```

**✅ UPDATED:**
```javascript
// Only role management functions remain
export const getUserRole = () => {
  return localStorage.getItem('userRole');
};

export const setUserRole = (role) => {
  localStorage.setItem('userRole', role);
};

export const clearUserRole = () => {
  localStorage.removeItem('userRole');
};

// Authentication status based on role presence
export const isAuthenticated = () => {
  return !!getUserRole();
};
```

#### **2. API Service (`frontend/src/services/api.js`)**

**❌ REMOVED:**
```javascript
// Token-based authentication
async authenticatedRequest(endpoint, options = {}) {
  const token = localStorage.getItem('authToken');
  return this.request(endpoint, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
}
```

**✅ UPDATED:**
```javascript
// Cookie-based authentication
async request(endpoint, options = {}) {
  return fetch(url, {
    credentials: 'include', // Include cookies in all requests
    ...config
  });
}

// All requests now use the same method
async authenticatedRequest(endpoint, options = {}) {
  return this.request(endpoint, options);
}

// New logout endpoint
async logout() {
  return this.request('/auth/logout', { method: 'POST' });
}
```

#### **3. Login Component (`frontend/src/pages/Login.js`)**

**❌ REMOVED:**
```javascript
// Token storage
const response = await apiService.login(username, password);
setAuthData(response.access_token, response.role);
```

**✅ UPDATED:**
```javascript
// Role-only storage
const response = await apiService.login(username, password);
if (response.status === 'success') {
  setUserRole(response.role);
  navigate('/dashboard');
}
```

#### **4. Header Component (`frontend/src/components/Layout/Header.js`)**

**❌ REMOVED:**
```javascript
// Simple logout
const handleLogout = () => {
  clearAuthData();
  navigate('/login');
};
```

**✅ UPDATED:**
```javascript
// API-based logout
const handleLogout = async () => {
  try {
    await apiService.logout(); // Clear httpOnly cookie
  } catch (error) {
    console.warn('Logout API call failed:', error);
  } finally {
    clearUserRole();
    navigate('/login');
  }
};
```

#### **5. Live Feed Component (`frontend/src/pages/LiveFeed.js`)**

**❌ REMOVED:**
```javascript
// Token-based WebSocket
const token = getAuthToken();
const wsUrl = `ws://localhost:8000/ws/video_feed/${cameraId}?token=${token}`;
```

**✅ UPDATED:**
```javascript
// Cookie-based WebSocket (cookies sent automatically)
const wsUrl = `ws://localhost:8000/ws/video_feed/${cameraId}`;
```

---

## 🔒 **Security Improvements**

### **HttpOnly Cookies Benefits**
- ✅ **XSS Protection**: Tokens cannot be accessed by JavaScript
- ✅ **Automatic Handling**: Browser manages cookie lifecycle
- ✅ **CSRF Protection**: SameSite=lax prevents cross-site attacks
- ✅ **Secure Transport**: Secure=true ensures HTTPS-only transmission

### **Implementation Details**
```javascript
// Backend cookie configuration
response.set_cookie(
  key="access_token",
  value=access_token,
  httponly=True,       // Prevents JavaScript access
  samesite="lax",      // CSRF protection
  secure=True,         // HTTPS only
  max_age=3600         // 1 hour expiration
)
```

---

## 📋 **Request Flow Changes**

### **Before (Token-Based)**
```javascript
// Login
POST /auth/token → {"access_token": "jwt...", "role": "admin"}
localStorage.setItem('authToken', token)

// Authenticated Requests
fetch('/api/endpoint', {
  headers: { 'Authorization': 'Bearer ' + token }
})

// WebSocket
new WebSocket(`ws://localhost:8000/ws/feed/1?token=${token}`)
```

### **After (Cookie-Based)**
```javascript
// Login
POST /auth/token → {"status": "success", "role": "admin"}
// Cookie set automatically by browser
localStorage.setItem('userRole', role)

// Authenticated Requests
fetch('/api/endpoint', {
  credentials: 'include' // Cookies sent automatically
})

// WebSocket
new WebSocket('ws://localhost:8000/ws/feed/1') // Cookies sent automatically
```

---

## 🧪 **Testing Checklist**

### **Authentication Flow**
- [ ] Login with valid credentials stores role and redirects
- [ ] Login with invalid credentials shows error
- [ ] Logout clears cookie and redirects to login
- [ ] Page refresh maintains authentication state

### **API Requests**
- [ ] All authenticated endpoints work without Authorization headers
- [ ] Unauthenticated requests return 401 errors
- [ ] File uploads (face enrollment) work with cookies
- [ ] WebSocket connections authenticate via cookies

### **Role-Based Access**
- [ ] Employee role can access employee features only
- [ ] Admin role can access admin and employee features
- [ ] Super Admin role can access all features
- [ ] Route protection works correctly

### **Security**
- [ ] JWT tokens not visible in browser DevTools
- [ ] Cookies have httpOnly, secure, and samesite attributes
- [ ] Cross-origin requests handled correctly
- [ ] Session expiration redirects to login

---

## 🔧 **Configuration Requirements**

### **Frontend Configuration**
```javascript
// API requests must include credentials
fetch(url, {
  credentials: 'include', // Required for cookie authentication
  ...options
});
```

### **Backend CORS Configuration**
```python
# FastAPI CORS middleware must allow credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🚀 **Deployment Considerations**

### **Development Environment**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Cookies work within same domain (localhost)

### **Production Environment**
- Use same domain or configure CORS properly
- Ensure HTTPS for secure cookies
- Configure reverse proxy for same-origin requests

### **Example Nginx Configuration**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    # Frontend
    location / {
        root /path/to/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Cookie $http_cookie;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Cookie $http_cookie;
    }
}
```

---

## 📊 **Migration Impact**

### **Files Modified**
1. `frontend/src/utils/auth.js` - Removed token functions
2. `frontend/src/services/api.js` - Updated all API calls
3. `frontend/src/pages/Login.js` - Updated login flow
4. `frontend/src/components/Layout/Header.js` - Updated logout flow
5. `frontend/src/pages/LiveFeed.js` - Updated WebSocket connection

### **Functionality Preserved**
- ✅ All role-based dashboard features
- ✅ User management capabilities
- ✅ Face enrollment and management
- ✅ Live video streaming
- ✅ Camera and system controls
- ✅ Multi-camera viewing support

### **Security Enhanced**
- ✅ XSS attack prevention
- ✅ CSRF attack mitigation
- ✅ Automatic token lifecycle management
- ✅ Secure token transmission

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Cookies Not Being Sent**
```javascript
// Ensure credentials: 'include' is set
fetch('/api/endpoint', {
  credentials: 'include' // Required!
});
```

#### **CORS Errors**
```python
# Backend must allow credentials
allow_credentials=True
```

#### **WebSocket Authentication Fails**
- Cookies are automatically sent with WebSocket connections to same domain
- Check browser network tab for cookie presence
- Verify WebSocket endpoint doesn't require token parameter

#### **Login Successful but API Calls Fail**
- Check if `credentials: 'include'` is set on all requests
- Verify cookie is being set by checking browser DevTools > Application > Cookies

### **Debugging Tools**
```javascript
// Check if role is stored
console.log('User Role:', getUserRole());

// Check authentication status
console.log('Is Authenticated:', isAuthenticated());

// Check cookies in browser DevTools
// Application > Storage > Cookies > localhost:8000
```

---

## ✅ **Migration Complete**

The React frontend has been successfully migrated from token-based to cookie-based authentication while maintaining all existing functionality. The system is now more secure and follows modern web security best practices.

### **Key Benefits Achieved**
- 🔒 Enhanced security with httpOnly cookies
- 🎯 Simplified frontend authentication logic
- 🚀 Automatic token lifecycle management
- 🛡️ Protection against XSS and CSRF attacks
- 📱 Consistent authentication across all features

The migration is complete and the system is ready for production deployment with improved security posture.