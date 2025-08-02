# Deployment Lab - How It Works

## 🏗️ Deployment Architecture

### File Storage Locations:

```
/home/abdullah/deployment-lab/          # Main app
├── logs/                               # App logs
├── start.sh, stop.sh, logs.sh         # Control scripts
└── ...

/tmp/                                   # Temporary cloning (auto-cleanup)
├── tmpXXXXXX/                         # Git repos cloned here during build
└── ...

Docker containers                       # Running deployments
├── project1-container                 # Each deployment runs here
├── project2-container
└── ...

/etc/nginx/sites-available/            # Nginx configs
├── test.ao2395.com                    # Auto-generated per deployment
├── project1.ao2395.com
└── ...
```

## 🚀 Deployment Process:

### Step 1: User Creates Deployment
- User visits: `https://deployment-lab.ao2395.com`
- Submits: GitHub URL + subdomain + env vars
- Example: `https://github.com/user/project` → `test.ao2395.com`

### Step 2: Background Processing
```python
async def deploy_application(deployment_id: str):
    # 1. Clone repo to /tmp/tmpXXXXXX
    repo_path = await clone_repository(github_url, deployment_id)
    
    # 2. Detect project type (Next.js + FastAPI, Node.js, Python, etc.)
    project_type = detect_project_type(repo_path)
    
    # 3. Generate Dockerfile if needed
    if not exists("Dockerfile"):
        create_dockerfile(project_type, port)
    
    # 4. Build Docker image
    docker build -t project-name:deployment-id /tmp/tmpXXXXXX
    
    # 5. Run container
    docker run -d -p {assigned_port}:{container_port} project-name:deployment-id
    
    # 6. Setup Nginx config
    create_nginx_config(subdomain, assigned_port)
    
    # 7. Setup Cloudflare DNS
    create_dns_record(subdomain)
    
    # 8. Cleanup temp files
    rm -rf /tmp/tmpXXXXXX
```

### Step 3: Live Deployment
- Container runs the built application
- Nginx proxies `subdomain.ao2395.com` → `localhost:assigned_port`
- Cloudflare tunnel routes external traffic → Nginx → Container

## 📁 Where Code Lives:

### During Build (Temporary):
```bash
/tmp/tmpABC123/                        # Git clone happens here
├── package.json                      # User's frontend
├── api/                              # User's backend
├── Dockerfile                        # Generated if missing
└── ...                               # All user files
```

### After Build (Permanent):
```bash
Docker Image: project-name:deployment-id    # Built code stored in image
Docker Container: project-container         # Running instance
```

### Configuration Files:
```bash
/etc/nginx/sites-available/test.ao2395.com  # Nginx config
MongoDB: deployment records                  # Metadata & logs
Cloudflare: DNS records                      # Domain routing
```

## 🔄 Multi-Project Example:

```
User deploys 3 projects:
├── blog.ao2395.com      → Port 3001 → Docker container
├── api.ao2395.com       → Port 3002 → Docker container  
└── shop.ao2395.com      → Port 3003 → Docker container

Each has:
├── Separate Docker container
├── Separate Nginx config
├── Separate database record
└── Separate Cloudflare DNS record
```

## 🗂️ Database Records:

```javascript
// MongoDB collections:
deployments: {
  _id: "deployment-id",
  name: "project-name", 
  github_url: "https://github.com/user/repo",
  subdomain: "test",
  port: 3001,
  status: "running",
  container_id: "docker-container-id",
  docker_image: "project-name:deployment-id"
}

build_logs: {
  deployment_id: "deployment-id",
  message: "Cloning repository...",
  timestamp: "2025-08-02T16:00:00Z"
}
```

## 🔧 Management Operations:

### View Deployments:
- Dashboard shows all running deployments
- Live status, logs, and management options

### Delete Deployment:
1. Stop Docker container
2. Remove Docker image  
3. Delete Nginx config
4. Remove Cloudflare DNS
5. Free up port
6. Delete database records

### Logs:
- Build logs stored in MongoDB
- Runtime logs from Docker containers
- Management app logs in `/logs/`

## 🚀 Scaling:

The system can handle multiple deployments because:
- Each gets unique port (3001, 3002, 3003...)
- Each gets unique subdomain (test.ao2395.com, api.ao2395.com...)
- Each runs in isolated Docker container
- Port registry prevents conflicts
- Nginx handles all routing

This way you can deploy unlimited projects without conflicts!