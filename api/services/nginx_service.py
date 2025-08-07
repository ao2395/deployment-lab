import os
import subprocess
from jinja2 import Template
from typing import Optional
from models import BuildLogModel, LogLevel, get_database

class NginxService:
    def __init__(self):
        self.config_path = os.getenv("NGINX_CONFIG_PATH", "/etc/nginx/sites-available")
        self.enabled_path = os.getenv("NGINX_ENABLED_PATH", "/etc/nginx/sites-enabled")
        self.base_domain = os.getenv("BASE_DOMAIN", "yourdomain.com")
        
    async def log_operation(self, deployment_id: str, message: str, level: LogLevel = LogLevel.INFO):
        db = get_database()
        log_entry = BuildLogModel(
            deployment_id=deployment_id,
            message=message,
            log_level=level
        )
        await db.build_logs.insert_one(log_entry.dict(by_alias=True))
    
    def generate_nginx_config(self, subdomain: str, port: int) -> str:
        """Generate nginx configuration for a deployment"""
        config = f"""server {{
    listen 80;
    server_name {subdomain}.{self.base_domain};

    # Handle Next.js static files with proper caching
    location /_next/static/ {{
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_buffering off;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        
        # Cache static files
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}

    # Handle all other requests
    location / {{
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
        proxy_buffering off;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
    }}
}}"""
        return config
    
    async def create_config(self, subdomain: str, port: int, deployment_id: str) -> bool:
        try:
            config_content = self.generate_nginx_config(subdomain, port)
            config_filename = f"{subdomain}.{self.base_domain}"
            config_file_path = os.path.join(self.config_path, config_filename)
            
            await self.log_operation(deployment_id, f"Creating nginx config for {subdomain}")
            
            # Write config to temporary file first
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as temp_file:
                temp_file.write(config_content)
                temp_file_path = temp_file.name
            
            # Use sudo to move the file to the nginx directory
            result = subprocess.run([
                'sudo', 'mv', temp_file_path, config_file_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                await self.log_operation(deployment_id, f"Failed to move config file: {result.stderr}", LogLevel.ERROR)
                return False
            
            await self.log_operation(deployment_id, f"Nginx config created at {config_file_path}")
            return True
            
        except Exception as e:
            await self.log_operation(deployment_id, f"Failed to create nginx config: {str(e)}", LogLevel.ERROR)
            return False
    
    async def enable_site(self, subdomain: str, deployment_id: str) -> bool:
        try:
            config_filename = f"{subdomain}.{self.base_domain}"
            available_path = os.path.join(self.config_path, config_filename)
            enabled_path = os.path.join(self.enabled_path, config_filename)
            
            if not os.path.exists(available_path):
                await self.log_operation(deployment_id, f"Config file not found: {available_path}", LogLevel.ERROR)
                return False
            
            await self.log_operation(deployment_id, f"Enabling nginx site: {subdomain}")
            
            # Use sudo to create the symlink
            result = subprocess.run([
                'sudo', 'ln', '-sf', available_path, enabled_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                await self.log_operation(deployment_id, f"Failed to enable site: {result.stderr}", LogLevel.ERROR)
                return False
                
            await self.log_operation(deployment_id, f"Site enabled: {subdomain}")
            return True
            
        except Exception as e:
            await self.log_operation(deployment_id, f"Failed to enable site: {str(e)}", LogLevel.ERROR)
            return False
    
    async def reload_nginx(self, deployment_id: str) -> bool:
        try:
            await self.log_operation(deployment_id, "Reloading nginx configuration")
            
            result = subprocess.run(['sudo', 'nginx', '-t'], capture_output=True, text=True)
            if result.returncode != 0:
                await self.log_operation(deployment_id, f"Nginx config test failed: {result.stderr}", LogLevel.ERROR)
                return False
            
            result = subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], capture_output=True, text=True)
            if result.returncode != 0:
                await self.log_operation(deployment_id, f"Nginx reload failed: {result.stderr}", LogLevel.ERROR)
                return False
            
            await self.log_operation(deployment_id, "Nginx reloaded successfully")
            return True
            
        except Exception as e:
            await self.log_operation(deployment_id, f"Failed to reload nginx: {str(e)}", LogLevel.ERROR)
            return False
    
    async def remove_config(self, subdomain: str, deployment_id: Optional[str] = None) -> bool:
        try:
            config_filename = f"{subdomain}.{self.base_domain}"
            available_path = os.path.join(self.config_path, config_filename)
            enabled_path = os.path.join(self.enabled_path, config_filename)
            
            if deployment_id:
                await self.log_operation(deployment_id, f"Removing nginx config for {subdomain}")
            
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
                if deployment_id:
                    await self.log_operation(deployment_id, f"Removed enabled site: {enabled_path}")
            
            if os.path.exists(available_path):
                os.remove(available_path)
                if deployment_id:
                    await self.log_operation(deployment_id, f"Removed config file: {available_path}")
            
            return True
            
        except Exception as e:
            if deployment_id:
                await self.log_operation(deployment_id, f"Failed to remove nginx config: {str(e)}", LogLevel.ERROR)
            else:
                print(f"Failed to remove nginx config: {e}")
            return False
    
    async def setup_deployment_nginx(self, subdomain: str, port: int, deployment_id: str) -> bool:
        try:
            success = await self.create_config(subdomain, port, deployment_id)
            if not success:
                return False
            
            success = await self.enable_site(subdomain, deployment_id)
            if not success:
                return False
            
            success = await self.reload_nginx(deployment_id)
            if not success:
                await self.remove_config(subdomain, deployment_id)
                return False
            
            await self.log_operation(deployment_id, f"Nginx setup completed for {subdomain}.{self.base_domain}")
            return True
            
        except Exception as e:
            await self.log_operation(deployment_id, f"Nginx setup failed: {str(e)}", LogLevel.ERROR)
            return False