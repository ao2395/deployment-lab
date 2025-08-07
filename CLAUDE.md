# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Auto-Deployment Platform that automatically deploys Next.js + FastAPI applications from GitHub repositories with complete infrastructure management. The platform consists of a Next.js frontend and FastAPI backend, designed to run directly on a host system (not containerized itself) to manage Docker containers, Nginx configurations, and Cloudflare DNS for deployed applications.

## Development Commands

### Frontend (Next.js)
```bash
# Development server (with Turbopack)
npm run dev

# Production build
npm run build

# Start production server
npm run start
npm start  # Alternative command

# Linting
npm run lint
```

### Backend (FastAPI)
```bash
cd api

# Install dependencies
poetry install

# Development server (with auto-reload)
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Full Application Management
```bash
# Start both frontend and backend with production setup
./start.sh

# Stop all services
./stop.sh

# View all logs
./logs.sh

# Check service status
./status.sh

# Monitor live activity
./monitor.sh
```

## Architecture

### Core Components

**Frontend (Next.js 15 + TypeScript)**:
- `app/page.tsx` - Landing page
- `app/login/page.tsx` - Authentication page
- `app/dashboard/page.tsx` - Main deployment dashboard
- `app/deployments/[id]/logs/page.tsx` - Real-time deployment logs
- `app/components/CreateDeploymentDialog.tsx` - New deployment creation
- `app/components/DeploymentCard.tsx` - Individual deployment management
- `app/hooks/useAuth.tsx` - JWT-based authentication hook

**Backend Services (FastAPI)**:
- `api/main.py` - FastAPI application with CORS and request logging
- `api/app/auth.py` - JWT authentication router
- `api/app/deployments.py` - Main deployment management router
- `api/services/docker_service.py` - Docker container management and project detection
- `api/services/nginx_service.py` - Nginx configuration management
- `api/services/cloudflare_service.py` - Cloudflare DNS management
- `api/services/port_service.py` - Port allocation management
- `api/services/cleanup_service.py` - Resource cleanup operations

**Database Models** (`api/models/`):
- MongoDB-based with Motor async driver
- `DeploymentModel` - Deployment metadata and status
- `BuildLogModel` - Real-time build and deployment logs

### Deployment Flow Architecture

1. **Repository Cloning**: Clones GitHub repos to temporary directories (`/tmp/`)
2. **Project Detection**: Automatically detects Next.js + FastAPI, Node.js, Python, or static projects
3. **Docker Management**: Generates Dockerfiles if missing, builds images, manages containers
4. **Infrastructure Setup**: 
   - Assigns unique ports starting from 3001
   - Creates Nginx reverse proxy configurations
   - Sets up Cloudflare DNS records for subdomains
5. **Cleanup**: Removes temporary files but keeps containers and configurations running

### Key Design Patterns

- **Service-based architecture**: Each infrastructure component (Docker, Nginx, Cloudflare) has dedicated service classes
- **Async/await throughout**: All I/O operations use asyncio
- **Real-time logging**: Build logs stored in MongoDB and streamed to frontend
- **Port management**: Automatic port allocation with conflict prevention
- **Complete cleanup**: Full resource cleanup when deployments are deleted

## Environment Setup

### Required Services
- MongoDB running on localhost:27017
- Nginx installed with writable `/etc/nginx/sites-available/` and `/etc/nginx/sites-enabled/`
- Docker Engine with user permissions
- Cloudflare tunnel configured (optional)

### Environment Variables
Create `.env` file in project root:
```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=deployment_lab

# Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-here

# Cloudflare (optional)
CLOUDFLARE_API_TOKEN=your-token
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_TUNNEL_ID=your-tunnel-id
BASE_DOMAIN=yourdomain.com

# Port allocation
MIN_PORT=3001
MAX_PORT=8000
```

## Development Notes

### Running in Development
- Frontend runs on port 3000
- Backend API runs on port 8000
- Use `npm run dev` and separate `cd api && poetry run uvicorn main:app --reload` for development
- Use `./start.sh` for production-like testing

### Project Type Detection
The system automatically detects:
- **Next.js + FastAPI**: `package.json` + `api/main.py` or `api/pyproject.toml`
- **Node.js**: `package.json` without FastAPI backend
- **Python**: `requirements.txt` or `pyproject.toml` without Next.js
- **Static**: HTML files without dynamic backends

### Port Management
- Main app uses port 3000 (frontend) and 8000 (backend)
- Deployed applications get ports starting from 3001
- Port conflicts are automatically resolved
- Ports are freed when deployments are deleted

### Security Model
- JWT-based authentication with hardcoded admin credentials
- No user registration - admin-only access
- Container isolation for deployed applications
- Host system access required for infrastructure management