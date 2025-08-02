Auto-Deployment App Requirements & Design (Updated)

  🎯 Core Functionality Requirements

  Authentication System

  - Login Only - No registration, admin-controlled access
  - Session Management with JWT tokens
  - Protected Routes - All deployment features require
  authentication
  - Single Admin User or predefined user credentials

  User Input Interface

  - GitHub Repository URL validation and access
  - Environment Variables key-value input form
  - Subdomain Selection with availability checking
  - Deployment Configuration (optional overrides)

  Deployment Management

  - Create Deployments from GitHub repos
  - View All Deployments in dashboard table/grid
  - Delete Deployments with complete cleanup
  - Deployment Status tracking and monitoring

  Port Management

  - Auto Port Detection starting from 3000, increment for
  conflicts
  - Port Registry database to track allocated ports
  - Port Cleanup on deployment deletion
  - Health Check Integration to verify port availability

  Infrastructure Automation

  - Docker Container build and deployment
  - Nginx Configuration auto-generation and reload
  - Cloudflare Tunnel setup and DNS management
  - Complete Cleanup on deployment deletion

  🏗️ System Architecture

  Frontend (Next.js)

  ├── Login Page - Authentication only (no register)
  ├── Dashboard - Protected deployment list view
  ├── Deploy Form - Protected GitHub URL + env vars input
  ├── Deployment Card - Individual deployment with delete
  button
  ├── Status Monitor - Real-time deployment tracking
  └── Logs Viewer - Build and runtime logs

  Backend (FastAPI)

  ├── /auth/login - Authentication endpoint
  ├── /auth/verify - Token verification
  ├── /deployments - CRUD operations for deployments
  │   ├── GET / - List all deployments
  │   ├── POST / - Create new deployment
  │   ├── GET /{id} - Get deployment details
  │   └── DELETE /{id} - Delete deployment completely
  ├── /deploy - Main deployment endpoint
  ├── /status/{deployment_id} - Deployment status
  ├── /logs/{deployment_id} - Log streaming
  ├── /ports - Port management
  └── /domains - Subdomain management

  Core Services

  1. Authentication Service
  2. GitHub Integration Service
  3. Docker Management Service
  4. Nginx Config Generator
  5. Cloudflare API Integration
  6. Port Registry Manager
  7. Cleanup Service (for deletions)

  📋 Technical Requirements

  Dependencies & Tools

  # Core Backend
  fastapi>=0.100.0
  uvicorn>=0.20.0
  docker>=6.0.0
  pydantic>=2.0.0
  sqlalchemy>=2.0.0
  asyncio
  aiofiles

  # Authentication
  python-jose[cryptography]  # JWT tokens
  passlib[bcrypt]  # Password hashing
  python-multipart  # Form data

  # External APIs
  httpx  # GitHub API calls
  cloudflare  # Cloudflare API
  gitpython  # Git operations

  # Infrastructure
  nginx  # Config generation
  jinja2  # Template rendering

  // Frontend Stack
  next.js 15+
  typescript
  tailwindcss
  shadcn/ui
  react-query  // API state management
  socket.io-client  // Real-time updates
  next-auth  // Authentication
  js-cookie  // Token management

  System Requirements

  - Docker Engine with API access
  - Nginx with config reload capability
  - Cloudflared CLI tool installed
  - Git for repository cloning
  - Node.js 20+ and Python 3.11+

  🔐 Authentication & Authorization

  Login System

  class AuthService:
      def authenticate_user(self, username: str, password: 
  str) -> Optional[User]:
          # Verify against predefined credentials
          # No database registration - hardcoded admin user

      def create_access_token(self, user_id: str) -> str:
          # Generate JWT token with expiration

      def verify_token(self, token: str) -> Optional[User]:
          # Validate JWT and return user info

  Frontend Auth Integration

  // Protected route wrapper
  function ProtectedRoute({ children }: { children: 
  React.ReactNode }) {
    const { user, loading } = useAuth()

    if (loading) return <Loading />
    if (!user) return <LoginPage />

    return <>{children}</>
  }

  // Auth context
  const AuthContext = createContext({
    user: null,
    login: async (username: string, password: string) => {},
    logout: () => {},
    loading: false
  })

  🗂️ Deployment Management

  Deployment Dashboard

  // Dashboard component showing all deployments
  interface DeploymentCard {
    id: string
    name: string
    subdomain: string
    status: 'running' | 'building' | 'failed' | 'stopped'
    github_url: string
    created_at: string
    port: number
    actions: {
      view: () => void
      logs: () => void
      delete: () => void
    }
  }

  Complete Deletion System

  class DeploymentCleanupService:
      async def delete_deployment(self, deployment_id: str):
          deployment = await
  self.get_deployment(deployment_id)

          # 1. Stop and remove Docker container
          await
  self.docker_service.stop_container(deployment.container_id)
          await self.docker_service.remove_container(deployme
  nt.container_id)

          # 2. Remove Docker image
          await self.docker_service.remove_image(f"{deploymen
  t.name}:{deployment.id}")

          # 3. Remove Nginx configuration
          await
  self.nginx_service.remove_config(deployment.subdomain)
          await self.nginx_service.reload()

          # 4. Remove Cloudflare tunnel entry
          await self.cloudflare_service.remove_tunnel_route(d
  eployment.subdomain)

          # 5. Free up port
          await
  self.port_manager.release_port(deployment.port)

          # 6. Clean up temporary files
          await
  self.file_service.cleanup_build_files(deployment.id)

          # 7. Remove from database
          await self.db.delete(deployment)

  🔧 Implementation Components

  1. Authentication Middleware

  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer

  security = HTTPBearer()

  async def get_current_user(token: str = Depends(security)):
      user = auth_service.verify_token(token.credentials)
      if not user:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid authentication credentials"
          )
      return user

  2. Protected Deployment Endpoints

  @router.get("/deployments")
  async def list_deployments(user: User = 
  Depends(get_current_user)):
      return await deployment_service.get_all_deployments()

  @router.delete("/deployments/{deployment_id}")
  async def delete_deployment(
      deployment_id: str, 
      user: User = Depends(get_current_user)
  ):
      await cleanup_service.delete_deployment(deployment_id)
      return {"message": "Deployment deleted successfully"}

  3. Frontend Deployment Management

  // Deployment list with delete functionality
  function DeploymentList() {
    const { data: deployments, refetch } =
  useQuery('deployments', fetchDeployments)

    const deleteDeployment = useMutation(
      (id: string) => api.delete(`/deployments/${id}`),
      {
        onSuccess: () => {
          refetch()
          toast.success('Deployment deleted successfully')
        }
      }
    )

    const handleDelete = async (deployment: Deployment) => {
      if (confirm(`Delete ${deployment.name}? This cannot be 
  undone.`)) {
        await deleteDeployment.mutateAsync(deployment.id)
      }
    }

    return (
      <div className="grid gap-4">
        {deployments?.map(deployment => (
          <DeploymentCard 
            key={deployment.id}
            deployment={deployment}
            onDelete={() => handleDelete(deployment)}
          />
        ))}
      </div>
    )
  }

  📊 Updated Database Schema

  class User(Base):
      __tablename__ = "users"
      id: str = UUID, Primary Key
      username: str = Unique
      password_hash: str  # bcrypt hashed
      is_active: bool = True
      created_at: datetime

  class Deployment(Base):
      __tablename__ = "deployments"
      id: str = UUID, Primary Key
      name: str  # Generated from repo name
      github_url: str
      subdomain: str = Unique
      port: int = Unique
      status: DeploymentStatus
      container_id: str
      docker_image: str  # For cleanup
      user_id: str = Foreign Key
      created_at: datetime
      updated_at: datetime
      env_vars: dict  # encrypted
      build_logs: relationship("BuildLog")

  class PortRegistry(Base):
      __tablename__ = "port_registry"
      port: int = Primary Key
      is_allocated: bool
      deployment_id: str = Foreign Key, nullable
      allocated_at: datetime
      released_at: datetime, nullable

  class BuildLog(Base):
      __tablename__ = "build_logs"
      id: str = UUID, Primary Key
      deployment_id: str = Foreign Key
      log_level: str  # info, error, debug
      message: str
      timestamp: datetime

  🖥️ Frontend Pages & Components

  Login Page

  function LoginPage() {
    const [credentials, setCredentials] = useState({
  username: '', password: '' })
    const { login, loading } = useAuth()

    const handleSubmit = async (e: FormEvent) => {
      e.preventDefault()
      try {
        await login(credentials.username,
  credentials.password)
        router.push('/dashboard')
      } catch (error) {
        toast.error('Invalid credentials')
      }
    }

    return (
      <div className="min-h-screen flex items-center 
  justify-center">
        <Card className="w-96">
          <CardHeader>
            <h1>Auto Deploy Login</h1>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <Input 
                type="text" 
                placeholder="Username"
                value={credentials.username}
                onChange={(e) => setCredentials(prev =>
  ({...prev, username: e.target.value}))}
              />
              <Input 
                type="password" 
                placeholder="Password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev =>
  ({...prev, password: e.target.value}))}
              />
              <Button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  Dashboard with Deployments

  function Dashboard() {
    const { data: deployments, isLoading } =
  useQuery('deployments', fetchDeployments)

    return (
      <ProtectedRoute>
        <div className="container mx-auto p-6">
          <div className="flex justify-between items-center 
  mb-6">
            <h1 className="text-3xl 
  font-bold">Deployments</h1>
            <Button onClick={() => router.push('/deploy')}>
              New Deployment
            </Button>
          </div>

          {isLoading ? (
            <DeploymentsSkeleton />
          ) : (
            <DeploymentList deployments={deployments} />
          )}
        </div>
      </ProtectedRoute>
    )
  }

  Deployment Card Component

  function DeploymentCard({ deployment, onDelete }: {
    deployment: Deployment
    onDelete: () => void
  }) {
    return (
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <h3 
  className="font-semibold">{deployment.name}</h3>
              <p className="text-sm 
  text-gray-600">{deployment.subdomain}.yourdomain.com</p>
            </div>
            <Badge 
  variant={getStatusVariant(deployment.status)}>
              {deployment.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" asChild>
                <a 
  href={`https://${deployment.subdomain}.yourdomain.com`} 
  target="_blank">
                  Visit
                </a>
              </Button>
              <Button variant="outline" size="sm" onClick={()
   => router.push(`/deployments/${deployment.id}/logs`)}>
                Logs
              </Button>
            </div>
            <Button 
              variant="destructive" 
              size="sm"
              onClick={onDelete}
            >
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  🚀 Updated Deployment Workflow

  User Flow

  1. Login: Authenticate with username/password
  2. Dashboard: View all existing deployments
  3. Create: Click "New Deployment" → Input GitHub URL + env
  vars + subdomain
  4. Monitor: Real-time build status and logs
  5. Manage: View, visit, or delete deployments
  6. Delete: Complete cleanup with confirmation

  System Flow

  graph TD
      A[User Login] --> B[Dashboard View]
      B --> C[Create New Deployment]
      B --> D[Manage Existing Deployments]
      C --> E[GitHub URL Input]
      E --> F[Clone & Analyze Repo]
      F --> G[Find Available Port]
      G --> H[Build & Deploy]
      H --> I[Update Dashboard]
      D --> J[View/Visit/Delete]
      J --> K[Complete Cleanup on Delete]
      K --> I

  This updated design provides comprehensive deployment
  lifecycle management with secure authentication and
  complete cleanup capabilities.



server {
listen 80;
server_name caresync.ao2395.com;

# Serve React frontend
location / {
    proxy_pass http://localhost:2998;  # Changed from 3000
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Route API calls to backend
location /api/ {
    proxy_pass http://localhost:2999;  # Changed from 5000
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
}