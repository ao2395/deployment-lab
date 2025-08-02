from typing import Optional
from .docker_service import DockerService
from .nginx_service import NginxService
from .cloudflare_service import CloudflareService
from .port_service import PortService
from models import get_database, DeploymentModel, BuildLogModel, LogLevel

class CleanupService:
    def __init__(self):
        self.docker_service = DockerService()
        self.nginx_service = NginxService()
        self.cloudflare_service = CloudflareService()
        self.port_service = PortService()
    
    async def log_cleanup(self, deployment_id: str, message: str, level: LogLevel = LogLevel.INFO):
        db = get_database()
        log_entry = BuildLogModel(
            deployment_id=deployment_id,
            message=message,
            log_level=level
        )
        await db.build_logs.insert_one(log_entry.dict(by_alias=True))
    
    async def delete_deployment(self, deployment_id: str) -> bool:
        try:
            db = get_database()
            
            # Get deployment info
            deployment_doc = await db.deployments.find_one({"_id": deployment_id})
            if not deployment_doc:
                print(f"Deployment {deployment_id} not found")
                return False
            
            deployment = DeploymentModel(**deployment_doc)
            
            await self.log_cleanup(deployment_id, f"Starting cleanup for deployment: {deployment.name}")
            
            success = True
            
            # 1. Stop and remove Docker container
            if deployment.container_id:
                await self.log_cleanup(deployment_id, "Stopping Docker container...")
                container_stopped = await self.docker_service.stop_container(deployment.container_id)
                if container_stopped:
                    await self.log_cleanup(deployment_id, "Container stopped successfully")
                else:
                    await self.log_cleanup(deployment_id, "Failed to stop container", LogLevel.ERROR)
                    success = False
                
                await self.log_cleanup(deployment_id, "Removing Docker container...")
                container_removed = await self.docker_service.remove_container(deployment.container_id)
                if container_removed:
                    await self.log_cleanup(deployment_id, "Container removed successfully")
                else:
                    await self.log_cleanup(deployment_id, "Failed to remove container", LogLevel.ERROR)
                    success = False
            
            # 2. Remove Docker image
            if deployment.docker_image:
                await self.log_cleanup(deployment_id, "Removing Docker image...")
                image_removed = await self.docker_service.remove_image(deployment.docker_image)
                if image_removed:
                    await self.log_cleanup(deployment_id, "Docker image removed successfully")
                else:
                    await self.log_cleanup(deployment_id, "Failed to remove Docker image", LogLevel.ERROR)
                    success = False
            
            # 3. Remove Nginx configuration
            await self.log_cleanup(deployment_id, "Removing Nginx configuration...")
            nginx_removed = await self.nginx_service.remove_config(deployment.subdomain, deployment_id)
            if nginx_removed:
                await self.log_cleanup(deployment_id, "Nginx config removed successfully")
                
                # Reload nginx
                nginx_reloaded = await self.nginx_service.reload_nginx(deployment_id)
                if nginx_reloaded:
                    await self.log_cleanup(deployment_id, "Nginx reloaded successfully")
                else:
                    await self.log_cleanup(deployment_id, "Failed to reload Nginx", LogLevel.ERROR)
                    success = False
            else:
                await self.log_cleanup(deployment_id, "Failed to remove Nginx config", LogLevel.ERROR)
                success = False
            
            # 4. Remove Cloudflare DNS record and tunnel route
            await self.log_cleanup(deployment_id, "Removing Cloudflare DNS record...")
            dns_removed = await self.cloudflare_service.remove_dns_record(deployment.subdomain, deployment_id)
            if dns_removed:
                await self.log_cleanup(deployment_id, "DNS record removed successfully")
            else:
                await self.log_cleanup(deployment_id, "Failed to remove DNS record", LogLevel.ERROR)
                success = False
            
            await self.log_cleanup(deployment_id, "Removing Cloudflare tunnel route...")
            tunnel_removed = await self.cloudflare_service.remove_tunnel_route(deployment.subdomain, deployment_id)
            if tunnel_removed:
                await self.log_cleanup(deployment_id, "Tunnel route removed successfully")
            else:
                await self.log_cleanup(deployment_id, "Failed to remove tunnel route", LogLevel.ERROR)
                success = False
            
            # 5. Free up port
            await self.log_cleanup(deployment_id, f"Releasing port {deployment.port}...")
            port_released = await self.port_service.release_port(deployment.port)
            if port_released:
                await self.log_cleanup(deployment_id, f"Port {deployment.port} released successfully")
            else:
                await self.log_cleanup(deployment_id, f"Failed to release port {deployment.port}", LogLevel.ERROR)
                success = False
            
            # 6. Remove from database (keep logs for reference)
            await self.log_cleanup(deployment_id, "Removing deployment from database...")
            delete_result = await db.deployments.delete_one({"_id": deployment_id})
            if delete_result.deleted_count > 0:
                await self.log_cleanup(deployment_id, "Deployment removed from database successfully")
            else:
                await self.log_cleanup(deployment_id, "Failed to remove deployment from database", LogLevel.ERROR)
                success = False
            
            if success:
                await self.log_cleanup(deployment_id, "Deployment cleanup completed successfully!")
            else:
                await self.log_cleanup(deployment_id, "Deployment cleanup completed with some errors", LogLevel.WARNING)
            
            return success
            
        except Exception as e:
            await self.log_cleanup(deployment_id, f"Cleanup failed with exception: {str(e)}", LogLevel.ERROR)
            return False
    
    async def cleanup_failed_deployment(self, deployment_id: str) -> bool:
        """
        Clean up a deployment that failed during creation.
        This is a more lenient cleanup that handles cases where resources may not exist.
        """
        try:
            db = get_database()
            
            deployment_doc = await db.deployments.find_one({"_id": deployment_id})
            if not deployment_doc:
                return True
            
            deployment = DeploymentModel(**deployment_doc)
            
            await self.log_cleanup(deployment_id, "Starting cleanup for failed deployment...")
            
            # Try to clean up any resources that might have been created
            if deployment.container_id:
                await self.docker_service.stop_container(deployment.container_id)
                await self.docker_service.remove_container(deployment.container_id)
            
            if deployment.docker_image:
                await self.docker_service.remove_image(deployment.docker_image)
            
            await self.nginx_service.remove_config(deployment.subdomain, deployment_id)
            await self.cloudflare_service.remove_dns_record(deployment.subdomain, deployment_id)
            await self.cloudflare_service.remove_tunnel_route(deployment.subdomain, deployment_id)
            await self.port_service.release_port(deployment.port)
            
            # Remove from database
            await db.deployments.delete_one({"_id": deployment_id})
            
            await self.log_cleanup(deployment_id, "Failed deployment cleanup completed")
            return True
            
        except Exception as e:
            print(f"Failed deployment cleanup error: {e}")
            return False