import docker
import os
import tempfile
import shutil
import asyncio
from typing import Optional, Dict, Any
from git import Repo
from models import get_database, DeploymentModel, BuildLogModel, DeploymentStatus, LogLevel

class DockerService:
    def __init__(self):
        self.client = docker.from_env()
        
    async def log_build(self, deployment_id: str, message: str, level: LogLevel = LogLevel.INFO):
        db = get_database()
        log_entry = BuildLogModel(
            deployment_id=deployment_id,
            message=message,
            log_level=level
        )
        await db.build_logs.insert_one(log_entry.dict(by_alias=True))
        
    async def update_deployment_status(self, deployment_id: str, status: DeploymentStatus):
        db = get_database()
        await db.deployments.update_one(
            {"_id": deployment_id},
            {"$set": {"status": status}}
        )
    
    async def clone_repository(self, github_url: str, deployment_id: str) -> Optional[str]:
        try:
            temp_dir = tempfile.mkdtemp()
            await self.log_build(deployment_id, f"Cloning repository: {github_url}")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, Repo.clone_from, github_url, temp_dir)
            
            await self.log_build(deployment_id, f"Repository cloned to: {temp_dir}")
            return temp_dir
        except Exception as e:
            await self.log_build(deployment_id, f"Failed to clone repository: {str(e)}", LogLevel.ERROR)
            return None
    
    def detect_project_type(self, repo_path: str) -> str:
        if os.path.exists(os.path.join(repo_path, "package.json")):
            return "node"
        elif os.path.exists(os.path.join(repo_path, "requirements.txt")) or os.path.exists(os.path.join(repo_path, "pyproject.toml")):
            return "python"
        elif os.path.exists(os.path.join(repo_path, "go.mod")):
            return "go"
        elif os.path.exists(os.path.join(repo_path, "Dockerfile")):
            return "docker"
        else:
            return "static"
    
    def generate_dockerfile(self, repo_path: str, project_type: str, port: int) -> str:
        # Multi-stage Dockerfile for Next.js + FastAPI projects
        nextjs_fastapi_dockerfile = f"""
# Multi-stage Dockerfile for Next.js frontend and FastAPI backend

# Stage 1: Build Next.js frontend
FROM node:20-alpine AS frontend-deps
RUN apk add --no-cache libc6-compat python3 make g++
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:20-alpine AS frontend-builder
RUN apk add --no-cache libc6-compat python3 make g++
WORKDIR /app
COPY --from=frontend-deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 2: Python backend setup
FROM python:3.11-slim AS backend-base
WORKDIR /app/api
RUN pip install poetry
COPY api/pyproject.toml api/poetry.lock* ./
RUN poetry config virtualenvs.create false && \\
    poetry install --no-interaction --no-ansi

# Stage 3: Final runtime image
FROM python:3.11-slim AS runner
WORKDIR /app

# Install Node.js for Next.js
RUN apt-get update && apt-get install -y \\
    curl \\
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \\
    && apt-get install -y nodejs \\
    && apt-get clean \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=backend-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-base /usr/local/bin /usr/local/bin

# Copy Next.js build
COPY --from=frontend-builder /app/.next/standalone ./
COPY --from=frontend-builder /app/.next/static ./.next/static
COPY --from=frontend-builder /app/public ./public

# Copy FastAPI backend
COPY api ./api

# Create startup script
RUN echo '#!/bin/bash\\n\\
# Start FastAPI backend in background (localhost only for internal access)\\n\\
cd /app/api && uvicorn main:app --host 127.0.0.1 --port 8000 &\\n\\
\\n\\
# Start Next.js frontend\\n\\
cd /app && node server.js' > /app/start.sh && \\
    chmod +x /app/start.sh

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT={port}
ENV HOSTNAME="0.0.0.0"

# Expose port
EXPOSE {port}

# Start both services
CMD ["/app/start.sh"]
        """
        
        # Fallback dockerfiles for other project types
        dockerfiles = {
            "nextjs-fastapi": nextjs_fastapi_dockerfile,
            "node": f"""
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build || echo "No build script found"
EXPOSE {port}
CMD ["npm", "start"]
            """,
            "python": f"""
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt . 2>/dev/null || echo "flask" > requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]
            """,
            "static": f"""
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
            """
        }
        
        # Default to Next.js + FastAPI if both frontend and backend detected
        if project_type == "nextjs-fastapi" or (
            os.path.exists(os.path.join(repo_path, "package.json")) and 
            os.path.exists(os.path.join(repo_path, "api"))
        ):
            return nextjs_fastapi_dockerfile.strip()
        
        return dockerfiles.get(project_type, dockerfiles["static"]).strip()
    
    async def build_image(self, repo_path: str, deployment: DeploymentModel) -> Optional[str]:
        try:
            await self.log_build(deployment.id, "Starting Docker build...")
            
            project_type = self.detect_project_type(repo_path)
            await self.log_build(deployment.id, f"Detected project type: {project_type}")
            
            dockerfile_path = os.path.join(repo_path, "Dockerfile")
            if not os.path.exists(dockerfile_path):
                dockerfile_content = self.generate_dockerfile(repo_path, project_type, deployment.port)
                with open(dockerfile_path, "w") as f:
                    f.write(dockerfile_content)
                await self.log_build(deployment.id, "Generated Dockerfile")
            
            # Docker tags must be lowercase and alphanumeric with limited special chars
            safe_name = deployment.name.lower().replace('_', '-').replace(' ', '-')
            # Remove any characters that aren't alphanumeric, hyphens, or dots
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '-.')
            # Ensure it starts with alphanumeric (remove leading hyphens/dots)
            safe_name = safe_name.lstrip('-.')
            # Fallback if name becomes empty
            if not safe_name:
                safe_name = "deployment"
                
            image_tag = f"{safe_name}:{deployment.id}"
            
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                None, 
                lambda: self.client.images.build(
                    path=repo_path, 
                    tag=image_tag,
                    rm=True
                )[0]
            )
            
            await self.log_build(deployment.id, f"Docker image built: {image_tag}")
            return image_tag
            
        except Exception as e:
            await self.log_build(deployment.id, f"Docker build failed: {str(e)}", LogLevel.ERROR)
            return None
    
    async def run_container(self, image_tag: str, deployment: DeploymentModel) -> Optional[str]:
        try:
            await self.log_build(deployment.id, f"Starting container from image: {image_tag}")
            
            container_name = f"{deployment.name}-{deployment.id}"
            
            env_vars = deployment.env_vars.copy()
            env_vars["PORT"] = str(deployment.port)
            
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.run(
                    image_tag,
                    name=container_name,
                    ports={f'{deployment.port}/tcp': deployment.port},
                    environment=env_vars,
                    detach=True,
                    restart_policy={"Name": "unless-stopped"}
                )
            )
            
            await self.log_build(deployment.id, f"Container started: {container.id}")
            return container.id
            
        except Exception as e:
            await self.log_build(deployment.id, f"Failed to start container: {str(e)}", LogLevel.ERROR)
            return None
    
    async def stop_container(self, container_id: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(None, self.client.containers.get, container_id)
            await loop.run_in_executor(None, container.stop)
            return True
        except Exception as e:
            print(f"Failed to stop container {container_id}: {e}")
            return False
    
    async def remove_container(self, container_id: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(None, self.client.containers.get, container_id)
            await loop.run_in_executor(None, container.remove)
            return True
        except Exception as e:
            print(f"Failed to remove container {container_id}: {e}")
            return False
    
    async def remove_image(self, image_tag: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.images.remove, image_tag)
            return True
        except Exception as e:
            print(f"Failed to remove image {image_tag}: {e}")
            return False
    
    async def cleanup_build_files(self, repo_path: str):
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
        except Exception as e:
            print(f"Failed to cleanup build files: {e}")
    
    async def deploy_from_github(self, deployment: DeploymentModel) -> bool:
        try:
            await self.update_deployment_status(deployment.id, DeploymentStatus.BUILDING)
            
            repo_path = await self.clone_repository(deployment.github_url, deployment.id)
            if not repo_path:
                await self.update_deployment_status(deployment.id, DeploymentStatus.FAILED)
                return False
            
            image_tag = await self.build_image(repo_path, deployment)
            if not image_tag:
                await self.cleanup_build_files(repo_path)
                await self.update_deployment_status(deployment.id, DeploymentStatus.FAILED)
                return False
            
            container_id = await self.run_container(image_tag, deployment)
            if not container_id:
                await self.cleanup_build_files(repo_path)
                await self.update_deployment_status(deployment.id, DeploymentStatus.FAILED)
                return False
            
            db = get_database()
            await db.deployments.update_one(
                {"_id": deployment.id},
                {
                    "$set": {
                        "container_id": container_id,
                        "docker_image": image_tag,
                        "status": DeploymentStatus.RUNNING
                    }
                }
            )
            
            await self.cleanup_build_files(repo_path)
            await self.log_build(deployment.id, "Deployment completed successfully!")
            
            return True
            
        except Exception as e:
            await self.log_build(deployment.id, f"Deployment failed: {str(e)}", LogLevel.ERROR)
            await self.update_deployment_status(deployment.id, DeploymentStatus.FAILED)
            return False