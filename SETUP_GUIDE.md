# 🚀 Face Recognition System - Complete Setup Guide

A comprehensive step-by-step guide for setting up the Face Recognition System from scratch, including development and production deployment instructions.

---

## 📋 **Prerequisites Checklist**

Before starting the installation, ensure you have the following prerequisites installed:

### **System Requirements**
- **Operating System**: Ubuntu 20.04+, Windows 10+, or macOS 10.15+
- **CPU**: Minimum 4 cores, 2.5GHz (Recommended: 8+ cores, 3.0GHz+)
- **RAM**: Minimum 8GB (Recommended: 16GB+)
- **Storage**: Minimum 50GB SSD (Recommended: 200GB+)
- **Network**: Stable internet connection for package downloads

### **Required Software**

#### **1. Python 3.8+**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Windows (using Python.org installer)
# Download from: https://www.python.org/downloads/
# Ensure "Add Python to PATH" is checked during installation

# macOS (using Homebrew)
brew install python@3.9

# Verify installation
python3 --version  # Should show 3.8.x or higher
pip3 --version
```

#### **2. Node.js 16+ and npm**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Windows (using Node.js installer)
# Download from: https://nodejs.org/en/download/
# Choose "LTS" version

# macOS (using Homebrew)
brew install node

# Verify installation
node --version   # Should show v16.x.x or higher
npm --version
```

#### **3. PostgreSQL 13+**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Windows
# Download from: https://www.postgresql.org/download/windows/
# Use the installer with default settings

# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Verify installation
psql --version  # Should show 13.x or higher
```

#### **4. Git (for cloning repository)**
```bash
# Ubuntu/Debian
sudo apt install git

# Windows
# Download from: https://git-scm.com/download/win

# macOS
brew install git

# Verify installation
git --version
```

#### **5. Optional: CUDA Toolkit (for GPU acceleration)**
```bash
# Ubuntu (NVIDIA GPU required)
# Check GPU compatibility first
nvidia-smi

# Install CUDA 11.8 (compatible with PyTorch)
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# Add to PATH (add to ~/.bashrc)
export PATH=/usr/local/cuda-11.8/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH
```

---

## 📁 **Project Structure Overview**

```
face-recognition-system/
├── backend/                    # FastAPI backend
│   ├── api/                   # API route handlers
│   ├── core/                  # Face recognition engine
│   ├── db/                    # Database utilities
│   ├── schemas/               # Pydantic models
│   ├── config.json           # System configuration
│   ├── main.py               # FastAPI application
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Dashboard pages
│   │   ├── services/        # API services
│   │   └── utils/           # Utility functions
│   ├── package.json         # Node.js dependencies
│   └── tailwind.config.js   # Tailwind CSS config
├── README.md                 # Main documentation
├── SETUP_GUIDE.md           # This setup guide
└── INTEGRATION_ANALYSIS.md  # Integration analysis
```

---

## 🔧 **Step 1: Project Setup**

### **1.1 Clone the Repository**
```bash
# Clone the project (replace with your repository URL)
git clone https://github.com/your-username/face-recognition-system.git
cd face-recognition-system

# Verify project structure
ls -la
# Should show: backend/ frontend/ README.md
```

### **1.2 Create Project Directories**
```bash
# If directories don't exist, create them
mkdir -p backend/logs
mkdir -p backend/uploads
mkdir -p frontend/build
```

---

## 🗄️ **Step 2: Database Setup**

### **2.1 Create PostgreSQL Database**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE face_recognition_db;
CREATE USER face_user WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE face_recognition_db TO face_user;

# Exit PostgreSQL
\q
```

### **2.2 Verify Database Connection**
```bash
# Test connection
psql -h localhost -U face_user -d face_recognition_db -c "SELECT version();"
# Enter password when prompted
```

### **2.3 Configure Database Settings**
```bash
# Edit backend database configuration
cd backend
nano db/db_utils.py

# Update DB_SETTINGS:
DB_SETTINGS = {
    "dbname": "face_recognition_db",
    "user": "face_user",
    "password": "secure_password_123",
    "host": "localhost",
    "port": 5432
}
```

---

## 🐍 **Step 3: Backend Setup**

### **3.1 Create Python Virtual Environment**
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
which python  # Should point to venv/bin/python
```

### **3.2 Install Python Dependencies**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# If you encounter issues with specific packages:
# For GPU support (optional):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CPU-only installation:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Verify critical packages
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import psycopg2; print('psycopg2: OK')"
```

### **3.3 Initialize Database Schema**
```bash
# Run database initialization script
python scripts/init_db.py

# If script doesn't exist, create it:
cat > scripts/init_db.py << 'EOF'
import sys
sys.path.append('..')
from db import db_utils

def init_database():
    """Initialize database with required tables and default data."""
    print("Initializing database...")
    
    # Create tables (implement based on your schema)
    # This is a placeholder - implement actual table creation
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
EOF

python scripts/init_db.py
```

### **3.4 Configure System Settings**
```bash
# Create or update config.json
cat > config.json << 'EOF'
{
  "api": {
    "recognition_threshold": 0.75,
    "max_concurrent_streams": 10,
    "frame_rate": 30,
    "gpu_enabled": true
  },
  "system": {
    "auto_detect_cameras": true,
    "default_gpu_id": 0,
    "log_level": "INFO"
  },
  "cameras": [
    {
      "id": 1,
      "camera_name": "Main Entrance",
      "stream_url": "0",
      "resolution": [640, 480],
      "fps": 15,
      "tripwires": []
    }
  ]
}
EOF
```

### **3.5 Test Backend Server**
```bash
# Start the FastAPI server
python main.py

# Server should start on http://localhost:8000
# You should see output like:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000

# Test in another terminal:
curl http://localhost:8000/
# Should return: {"message": "Welcome to the Face Recognition API..."}

# Stop server with Ctrl+C
```

---

## ⚛️ **Step 4: Frontend Setup**

### **4.1 Install Node.js Dependencies**
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# If you encounter permission issues on Linux/macOS:
sudo npm install -g npm@latest

# Verify installation
npm list --depth=0
# Should show React, React Router, Tailwind CSS, etc.
```

### **4.2 Configure Frontend Settings**
```bash
# Update API base URL if needed
nano src/services/api.js

# Ensure API_BASE_URL points to your backend:
const API_BASE_URL = 'http://localhost:8000';
```

### **4.3 Setup Tailwind CSS**
```bash
# Verify Tailwind configuration
cat tailwind.config.js
# Should include proper content paths

# If missing, create tailwind.config.js:
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF
```

### **4.4 Test Frontend Development Server**
```bash
# Start React development server
npm start

# Server should start on http://localhost:3000
# Browser should automatically open
# You should see the login page

# If port 3000 is busy, React will ask to use another port
# Type 'y' to accept

# Stop server with Ctrl+C
```

---

## 🔄 **Step 5: Running Both Servers Concurrently**

### **5.1 Method 1: Separate Terminals**
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
python main.py

# Terminal 2 - Frontend
cd frontend
npm start
```

### **5.2 Method 2: Using Process Managers**

#### **Using tmux (Linux/macOS)**
```bash
# Install tmux
sudo apt install tmux  # Ubuntu
brew install tmux      # macOS

# Create tmux session
tmux new-session -d -s face-recognition

# Split window
tmux split-window -h

# Run backend in first pane
tmux send-keys -t 0 'cd backend && source venv/bin/activate && python main.py' Enter

# Run frontend in second pane
tmux send-keys -t 1 'cd frontend && npm start' Enter

# Attach to session
tmux attach -t face-recognition

# Detach: Ctrl+b, then d
# Kill session: tmux kill-session -t face-recognition
```

#### **Using PM2 (All platforms)**
```bash
# Install PM2 globally
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'face-recognition-backend',
      cwd: './backend',
      script: 'python',
      args: 'main.py',
      interpreter: './venv/bin/python',
      env: {
        NODE_ENV: 'development'
      }
    },
    {
      name: 'face-recognition-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      env: {
        NODE_ENV: 'development'
      }
    }
  ]
};
EOF

# Start both applications
pm2 start ecosystem.config.js

# Monitor applications
pm2 monit

# Stop applications
pm2 stop all
```

---

## 🧪 **Step 6: System Verification**

### **6.1 Backend Health Check**
```bash
# Test API endpoints
curl -X GET http://localhost:8000/
curl -X GET http://localhost:8000/docs  # Swagger UI

# Test database connection
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### **6.2 Frontend Functionality Check**
```bash
# Open browser and test:
# 1. Navigate to http://localhost:3000
# 2. Try login page
# 3. Check console for errors (F12)
# 4. Verify responsive design (mobile view)
```

### **6.3 Integration Test**
```bash
# Test full login flow:
# 1. Open frontend (http://localhost:3000)
# 2. Login with default credentials
# 3. Verify dashboard loads
# 4. Check browser network tab for API calls
# 5. Test role-based navigation
```

---

## 🏭 **Step 7: Production Deployment**

### **7.1 Backend Production Setup**

#### **Install Production Server**
```bash
cd backend
source venv/bin/activate

# Install Gunicorn
pip install gunicorn

# Create Gunicorn configuration
cat > gunicorn.conf.py << 'EOF'
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
EOF
```

#### **Create Systemd Service (Linux)**
```bash
# Create service file
sudo nano /etc/systemd/system/face-recognition-backend.service

# Add content:
[Unit]
Description=Face Recognition Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project/backend
Environment=PATH=/path/to/your/project/backend/venv/bin
ExecStart=/path/to/your/project/backend/venv/bin/gunicorn -c gunicorn.conf.py main:app
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable face-recognition-backend
sudo systemctl start face-recognition-backend
sudo systemctl status face-recognition-backend
```

### **7.2 Frontend Production Build**

#### **Build React Application**
```bash
cd frontend

# Build for production
npm run build

# Verify build
ls -la build/
# Should contain: index.html, static/ folder, etc.

# Test production build locally
npm install -g serve
serve -s build -l 3000
```

#### **Deploy with Nginx**
```bash
# Install Nginx
sudo apt install nginx  # Ubuntu
brew install nginx      # macOS

# Create site configuration
sudo nano /etc/nginx/sites-available/face-recognition

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    # Frontend (React build)
    location / {
        root /path/to/your/project/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support for video streaming
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
}

# Enable site
sudo ln -s /etc/nginx/sites-available/face-recognition /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### **7.3 SSL Certificate (Production)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### **7.4 Environment Variables**
```bash
# Create environment file
cat > /path/to/your/project/.env << 'EOF'
# Database
DATABASE_URL=postgresql://face_user:secure_password_123@localhost/face_recognition_db

# Security
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=another-secure-key-for-jwt

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# GPU (if available)
CUDA_VISIBLE_DEVICES=0
EOF

# Load environment variables in your application
# Update main.py to load from .env file
```

---

## 🔍 **Step 8: Troubleshooting Common Issues**

### **8.1 Backend Issues**

#### **Database Connection Failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U face_user -d face_recognition_db

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log

# Fix: Update pg_hba.conf if needed
sudo nano /etc/postgresql/13/main/pg_hba.conf
# Add: local   all   face_user   md5
```

#### **Python Package Issues**
```bash
# Reinstall problematic packages
pip uninstall package_name
pip install package_name

# Clear pip cache
pip cache purge

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel
```

#### **GPU/CUDA Issues**
```bash
# Check GPU availability
nvidia-smi

# Test PyTorch GPU support
python -c "import torch; print(torch.cuda.is_available())"

# Install CPU-only version if GPU not available
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### **8.2 Frontend Issues**

#### **npm Install Failures**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Use yarn as alternative
npm install -g yarn
yarn install
```

#### **Build Failures**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build

# Check for TypeScript errors
npm run type-check  # if available
```

#### **CORS Issues**
```bash
# Verify backend CORS settings in main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **8.3 Integration Issues**

#### **WebSocket Connection Failed**
```bash
# Check if backend WebSocket endpoint is accessible
# Browser console should show WebSocket connection attempts

# Test WebSocket manually
wscat -c ws://localhost:8000/ws/video_feed/1?token=your_jwt_token

# Install wscat if needed
npm install -g wscat
```

#### **Authentication Issues**
```bash
# Check JWT token in browser localStorage
# Open browser dev tools > Application > Local Storage

# Test login endpoint directly
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

---

## 📊 **Step 9: Performance Optimization**

### **9.1 Backend Optimization**
```bash
# Database indexing
psql -U face_user -d face_recognition_db -c "
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_attendance_user_id ON attendance_records(user_id);
CREATE INDEX idx_attendance_timestamp ON attendance_records(timestamp);
"

# Python optimizations
# Add to main.py:
import uvloop  # Faster event loop
uvicorn.run("main:app", host="0.0.0.0", port=8000, loop="uvloop")
```

### **9.2 Frontend Optimization**
```bash
# Analyze bundle size
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer build/static/js/*.js

# Enable gzip compression in Nginx
# Add to nginx configuration:
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### **9.3 System Monitoring**
```bash
# Install monitoring tools
pip install psutil

# Create monitoring script
cat > monitor.py << 'EOF'
import psutil
import time

def monitor_system():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        print(f"CPU: {cpu}% | Memory: {memory}% | Disk: {disk}%")
        time.sleep(5)

if __name__ == "__main__":
    monitor_system()
EOF
```

---

## 🔐 **Step 10: Security Hardening**

### **10.1 Backend Security**
```bash
# Update SECRET_KEY in production
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add rate limiting
pip install slowapi
# Implement in main.py

# Enable HTTPS only
# Update main.py for production:
if ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### **10.2 Database Security**
```bash
# Create read-only user for monitoring
sudo -u postgres psql
CREATE USER monitoring_user WITH PASSWORD 'monitor_pass';
GRANT CONNECT ON DATABASE face_recognition_db TO monitoring_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;
```

### **10.3 System Security**
```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw deny 8000   # Block direct backend access

# Regular security updates
sudo apt update && sudo apt upgrade -y
```

---

## 📋 **Step 11: Maintenance & Backup**

### **11.1 Database Backup**
```bash
# Create backup script
cat > backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/path/to/backups"
DB_NAME="face_recognition_db"

mkdir -p $BACKUP_DIR
pg_dump -U face_user -h localhost $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup_db.sh
```

### **11.2 Log Rotation**
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/face-recognition

# Add configuration:
/path/to/your/project/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### **11.3 Health Checks**
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash

# Check backend
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ $BACKEND_STATUS -eq 200 ]; then
    echo "✅ Backend: OK"
else
    echo "❌ Backend: FAILED ($BACKEND_STATUS)"
fi

# Check database
DB_STATUS=$(psql -U face_user -d face_recognition_db -c "SELECT 1;" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAILED"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✅ Disk Space: OK ($DISK_USAGE%)"
else
    echo "⚠️ Disk Space: WARNING ($DISK_USAGE%)"
fi
EOF

chmod +x health_check.sh
```

---

## 🎯 **Step 12: Final Verification**

### **12.1 Complete System Test**
```bash
# Run comprehensive test
./health_check.sh

# Test all user roles
# 1. Login as Employee
# 2. Login as Admin  
# 3. Login as Super Admin

# Test all major features
# 1. Face enrollment
# 2. Live video streaming
# 3. User management
# 4. Camera controls
# 5. System monitoring
```

### **12.2 Performance Benchmarks**
```bash
# Load test backend
pip install locust

# Create load test script
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/token", data={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
    
    @task
    def dashboard(self):
        self.client.get("/", headers={
            "Authorization": f"Bearer {self.token}"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## 📞 **Support & Next Steps**

### **Getting Help**
- **Documentation**: Review README.md and INTEGRATION_ANALYSIS.md
- **Issues**: Create GitHub issues for bugs
- **Community**: Join discussions for questions

### **Recommended Next Steps**
1. **Customize Configuration**: Adjust settings for your environment
2. **Add Cameras**: Configure your actual camera streams
3. **User Training**: Train users on the system
4. **Monitoring Setup**: Implement comprehensive monitoring
5. **Backup Strategy**: Set up regular backups
6. **Security Audit**: Conduct security review

### **Production Checklist**
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Database backups automated
- [ ] Log rotation configured
- [ ] Monitoring alerts set up
- [ ] Performance optimized
- [ ] Security hardened
- [ ] Documentation updated
- [ ] Team trained
- [ ] Support procedures established

---

**🎉 Congratulations! Your Face Recognition System is now fully set up and ready for production use.**

For ongoing maintenance and updates, refer to the main README.md and keep your system dependencies up to date.