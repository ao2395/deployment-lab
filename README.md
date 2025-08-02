# Auto-Deployment Platform

A comprehensive platform for automatically deploying Next.js + FastAPI applications from GitHub repositories with complete infrastructure management.

## Features

- **Automatic Deployment**: Deploy applications directly from GitHub repositories
- **Multi-Stack Support**: Optimized for Next.js + FastAPI projects
- **Infrastructure Management**: Automatic Docker, Nginx, and Cloudflare configuration
- **Port Management**: Automatic port allocation starting from 3001
- **Complete Cleanup**: Full resource cleanup when deleting deployments
- **Real-time Logs**: Monitor build and deployment progress
- **Secure Authentication**: JWT-based admin-only access

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with async/await support
- **Database**: MongoDB for deployment metadata
- **Containerization**: Docker for application isolation
- **Reverse Proxy**: Nginx for routing
- **DNS**: Cloudflare for domain management
- **Authentication**: JWT tokens with hardcoded admin credentials

## How to Run on Host System

### Prerequisites

1. **System Requirements**:
   - Ubuntu/Debian Linux server
   - Docker Engine installed and running
   - Nginx installed
   - MongoDB installed and running
   - Node.js 20+ and Python 3.11+
   - Cloudflare account (optional)

2. **Permissions**:
   ```bash
   # Add your user to docker group
   sudo usermod -aG docker $USER
   
   # Create nginx directories if they don't exist
   sudo mkdir -p /etc/nginx/sites-available
   sudo mkdir -p /etc/nginx/sites-enabled
   
   # Allow user to modify nginx configs (or run with sudo)
   sudo chown -R $USER:$USER /etc/nginx/sites-available
   sudo chown -R $USER:$USER /etc/nginx/sites-enabled
   ```

### Installation Steps

1. **Clone and Setup**:
   ```bash
   git clone <this-repo>
   cd deployment-lab
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   nano .env
   ```

3. **Install Backend Dependencies**:
   ```bash
   cd api
   pip install poetry
   poetry install
   cd ..
   ```

4. **Install Frontend Dependencies**:
   ```bash
   npm install
   ```

5. **Start MongoDB**:
   ```bash
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

6. **Build Frontend**:
   ```bash
   npm run build
   ```

### Running the Application

1. **Start the Backend** (in one terminal):
   ```bash
   cd api
   poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the Frontend** (in another terminal):
   ```bash
   npm start
   # This will run on port 3000
   ```

3. **Access the Application**:
   - Open browser to `http://your-server-ip:3000`
   - Login with credentials from your `.env` file

### Environment Configuration

Key variables in `.env`:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=deployment_lab

# Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-here

# Cloudflare (optional)
CLOUDFLARE_API_TOKEN=your-cloudflare-token
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_TUNNEL_ID=your-tunnel-id
BASE_DOMAIN=yourdomain.com

# Port Range (starts from 3001 since 3000 is used by this app)
MIN_PORT=3001
MAX_PORT=8000
```

### Deployment Workflow

1. **Create Deployment**:
   - Enter GitHub repository URL
   - Choose subdomain
   - Add environment variables (optional)

2. **Automatic Process**:
   - Clones GitHub repository
   - Detects project type (Next.js + FastAPI)
   - Generates appropriate Dockerfile
   - Builds Docker image
   - Creates and starts container
   - Configures Nginx reverse proxy
   - Sets up Cloudflare DNS (if configured)
   - Updates port registry

3. **Access Deployed App**:
   - `https://subdomain.yourdomain.com` (if Cloudflare configured)
   - `http://your-server-ip:assigned-port` (direct access)

### Management Features

- **Real-time Monitoring**: View build logs and deployment status
- **Easy Cleanup**: Delete deployments with complete resource cleanup
- **Port Management**: Automatic allocation and deallocation
- **Multi-project Support**: Handle multiple deployments simultaneously

### Security Notes

- **Run on host system** - Don't containerize this management app
- **Admin-only access** - No user registration, secure credentials
- **Container isolation** - Each deployment runs in isolated container
- **Resource cleanup** - Complete cleanup prevents resource leaks

This platform is designed to run directly on your server host system for maximum control and access to system resources.
