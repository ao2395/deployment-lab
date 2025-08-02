import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from pydantic import BaseModel
from app.auth import get_current_user, User
from models import (
    get_database, 
    DeploymentModel, 
    DeploymentCreate, 
    DeploymentResponse,
    DeploymentStatus,
    BuildLogModel
)
from services import (
    DockerService,
    NginxService, 
    CloudflareService,
    PortService,
    CleanupService
)

router = APIRouter(prefix="/deployments", tags=["deployments"])

class DeploymentCreateRequest(BaseModel):
    github_url: str
    subdomain: str
    env_vars: dict = {}

class LogResponse(BaseModel):
    id: str
    message: str
    log_level: str
    timestamp: str

async def deploy_application(deployment_id: str):
    """Background task to handle deployment process"""
    try:
        from bson import ObjectId
        db = get_database()
        
        # Convert string ID to ObjectId for MongoDB query
        try:
            deployment_doc = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
        except Exception:
            deployment_doc = None
            
        if not deployment_doc:
            return
        
        # Create a simple deployment object instead of using Pydantic model
        deployment_id_str = str(deployment_doc["_id"])
        class SimpleDeployment:
            def __init__(self, doc):
                self.id = deployment_id_str
                self.name = doc["name"]
                self.github_url = doc["github_url"]
                self.subdomain = doc["subdomain"]
                self.port = doc["port"]
                self.status = doc["status"]
                self.env_vars = doc.get("env_vars", {})
        
        deployment = SimpleDeployment(deployment_doc)
        
        # Initialize services with error logging
        try:
            docker_service = DockerService()
            await docker_service.log_build(deployment_id_str, "Docker service initialized successfully")
        except Exception as e:
            # Log error directly to database since docker_service failed to initialize
            from models import BuildLogModel, LogLevel
            log_entry = BuildLogModel(
                deployment_id=deployment_id_str,
                message=f"Failed to initialize Docker service: {str(e)}",
                log_level=LogLevel.ERROR
            )
            await db.build_logs.insert_one(log_entry.dict(by_alias=True))
            raise
            
        nginx_service = NginxService()
        cloudflare_service = CloudflareService()
        cleanup_service = CleanupService()
        
        # Deploy using Docker service
        success = await docker_service.deploy_from_github(deployment)
        
        if success:
            # Setup nginx
            nginx_success = await nginx_service.setup_deployment_nginx(
                deployment.subdomain, 
                deployment.port, 
                deployment_id
            )
            
            if nginx_success:
                # Setup Cloudflare
                cf_success = await cloudflare_service.setup_deployment_cloudflare(
                    deployment.subdomain,
                    deployment.port,
                    deployment_id
                )
                
                if not cf_success:
                    await docker_service.log_build(
                        deployment_id, 
                        "Cloudflare setup failed, but deployment is accessible via direct nginx", 
                        "warning"
                    )
            else:
                await docker_service.log_build(
                    deployment_id,
                    "Nginx setup failed, cleaning up deployment",
                    "error"
                )
                await cleanup_service.cleanup_failed_deployment(deployment_id)
        else:
            await cleanup_service.cleanup_failed_deployment(deployment_id)
            
    except Exception as e:
        print(f"Background deployment task failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Log error to database for user visibility
        try:
            db = get_database()
            from models import BuildLogModel, LogLevel
            log_entry = BuildLogModel(
                deployment_id=deployment_id,
                message=f"Background deployment task failed: {str(e)}",
                log_level=LogLevel.ERROR
            )
            await db.build_logs.insert_one(log_entry.dict(by_alias=True))
            
            # Update deployment status to failed
            await db.deployments.update_one(
                {"_id": ObjectId(deployment_id)},
                {"$set": {"status": "failed"}}
            )
        except Exception as log_error:
            print(f"Failed to log error to database: {log_error}")
        
        cleanup_service = CleanupService()
        await cleanup_service.cleanup_failed_deployment(deployment_id)

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(current_user: User = Depends(get_current_user)):
    db = get_database()
    deployments = await db.deployments.find().to_list(length=None)
    
    return [
        DeploymentResponse(
            id=str(deployment["_id"]),
            name=deployment["name"],
            github_url=deployment["github_url"],
            subdomain=deployment["subdomain"],
            port=deployment["port"],
            status=deployment["status"],
            created_at=deployment["created_at"],
            updated_at=deployment["updated_at"]
        )
        for deployment in deployments
    ]

@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deployment_data: DeploymentCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    db = get_database()
    port_service = PortService()
    
    # Check if subdomain is already taken
    existing_deployment = await db.deployments.find_one({"subdomain": deployment_data.subdomain})
    if existing_deployment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already exists"
        )
    
    # Extract repository name from GitHub URL
    repo_name = deployment_data.github_url.split("/")[-1].replace(".git", "")
    
    # Find available port
    deployment_id = None  # Will be set after creating deployment
    available_port = await port_service.find_available_port("temp")
    if not available_port:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No available ports"
        )
    
    # Create deployment record
    deployment = DeploymentModel(
        name=repo_name,
        github_url=deployment_data.github_url,
        subdomain=deployment_data.subdomain,
        port=available_port,
        status=DeploymentStatus.PENDING,
        user_id=current_user.id,
        env_vars=deployment_data.env_vars
    )
    
    result = await db.deployments.insert_one(deployment.dict(by_alias=True))
    deployment_id = str(result.inserted_id)
    
    # Update port registry with correct deployment ID
    await db.port_registry.update_one(
        {"port": available_port},
        {"$set": {"deployment_id": deployment_id}}
    )
    
    # Start background deployment task
    background_tasks.add_task(deploy_application, deployment_id)
    
    return DeploymentResponse(
        id=deployment_id,
        name=deployment.name,
        github_url=deployment.github_url,
        subdomain=deployment.subdomain,
        port=deployment.port,
        status=deployment.status,
        created_at=deployment.created_at,
        updated_at=deployment.updated_at
    )

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    from bson import ObjectId
    db = get_database()
    
    # Convert string ID to ObjectId for MongoDB query
    try:
        deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    except Exception:
        deployment = None
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    return DeploymentResponse(
        id=str(deployment["_id"]),
        name=deployment["name"],
        github_url=deployment["github_url"],
        subdomain=deployment["subdomain"],
        port=deployment["port"],
        status=deployment["status"],
        created_at=deployment["created_at"],
        updated_at=deployment["updated_at"]
    )

@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    from bson import ObjectId
    db = get_database()
    
    # Convert string ID to ObjectId for MongoDB query
    try:
        deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    except Exception:
        deployment = None
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    cleanup_service = CleanupService()
    background_tasks.add_task(cleanup_service.delete_deployment, deployment_id)
    
    return {"message": "Deployment deletion started"}

@router.get("/{deployment_id}/logs", response_model=List[LogResponse])
async def get_deployment_logs(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    from bson import ObjectId
    db = get_database()
    
    # Check if deployment exists
    try:
        deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    except Exception:
        deployment = None
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    # Get logs
    logs = await db.build_logs.find(
        {"deployment_id": deployment_id}
    ).sort("timestamp", 1).to_list(length=None)
    
    return [
        LogResponse(
            id=str(log["_id"]),
            message=log["message"],
            log_level=log["log_level"],
            timestamp=log["timestamp"].isoformat()
        )
        for log in logs
    ]

@router.get("/{deployment_id}/status")
async def get_deployment_status(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    from bson import ObjectId
    db = get_database()
    
    # Convert string ID to ObjectId for MongoDB query
    try:
        deployment = await db.deployments.find_one({"_id": ObjectId(deployment_id)})
    except Exception:
        deployment = None
    
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found"
        )
    
    return {
        "id": deployment_id,
        "status": deployment["status"],
        "updated_at": deployment["updated_at"]
    }