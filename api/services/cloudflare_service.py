import os
import httpx
from typing import Optional, Dict, Any
from models import BuildLogModel, LogLevel, get_database

class CloudflareService:
    def __init__(self):
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        self.tunnel_id = os.getenv("CLOUDFLARE_TUNNEL_ID")
        self.base_domain = os.getenv("BASE_DOMAIN", "yourdomain.com")
        self.base_url = "https://api.cloudflare.com/client/v4"
        
        if not all([self.api_token, self.zone_id, self.tunnel_id]):
            print("Warning: Cloudflare credentials not fully configured")
    
    async def log_operation(self, deployment_id: str, message: str, level: LogLevel = LogLevel.INFO):
        db = get_database()
        log_entry = BuildLogModel(
            deployment_id=deployment_id,
            message=message,
            log_level=level
        )
        await db.build_logs.insert_one(log_entry.dict(by_alias=True))
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    return None
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    print(f"Cloudflare API error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Cloudflare API request failed: {e}")
            return None
    
    async def create_dns_record(self, subdomain: str, deployment_id: str) -> bool:
        try:
            await self.log_operation(deployment_id, f"Creating DNS record for {subdomain}")
            
            record_name = f"{subdomain}.{self.base_domain}"
            
            # Check if record already exists
            existing_records = await self._make_request(
                "GET", 
                f"/zones/{self.zone_id}/dns_records?name={record_name}"
            )
            
            if existing_records and existing_records.get("result"):
                await self.log_operation(deployment_id, f"DNS record already exists for {record_name}")
                return True
            
            # Create new CNAME record pointing to tunnel
            data = {
                "type": "CNAME",
                "name": subdomain,
                "content": f"{self.tunnel_id}.cfargotunnel.com",
                "ttl": 1,  # Auto TTL
                "proxied": True
            }
            
            result = await self._make_request(
                "POST",
                f"/zones/{self.zone_id}/dns_records",
                data
            )
            
            if result and result.get("success"):
                await self.log_operation(deployment_id, f"DNS record created for {record_name}")
                return True
            else:
                await self.log_operation(deployment_id, f"Failed to create DNS record: {result}", LogLevel.ERROR)
                return False
                
        except Exception as e:
            await self.log_operation(deployment_id, f"DNS record creation failed: {str(e)}", LogLevel.ERROR)
            return False
    
    async def create_tunnel_route(self, subdomain: str, port: int, deployment_id: str) -> bool:
        try:
            await self.log_operation(deployment_id, f"Creating tunnel route for {subdomain}")
            
            hostname = f"{subdomain}.{self.base_domain}"
            config_path = os.path.expanduser("~/.cloudflared/config.yml")
            
            # Read current config as text
            with open(config_path, 'r') as f:
                lines = f.readlines()
            
            # Check if hostname already exists
            hostname_exists = any(f"hostname: {hostname}" in line for line in lines)
            
            if not hostname_exists:
                # Find the last service line (before catch-all)
                insert_index = -1
                for i, line in enumerate(lines):
                    if 'service: http_status:404' in line:
                        insert_index = i
                        break
                
                if insert_index > 0:
                    # Insert new route before catch-all
                    new_lines = [
                        f"  - hostname: {hostname}\n",
                        f"    service: http://localhost:80\n"
                    ]
                    lines[insert_index:insert_index] = new_lines
                    
                    # Write updated config
                    with open(config_path, 'w') as f:
                        f.writelines(lines)
                
                await self.log_operation(deployment_id, f"Added tunnel route for {hostname}")
                
                # Restart tunnel to apply changes
                import subprocess
                subprocess.run(['pkill', 'cloudflared'], check=False)
                subprocess.Popen([
                    'cloudflared', 'tunnel', '--config', config_path, 'run'
                ], stdout=open('logs/tunnel.log', 'w'), stderr=subprocess.STDOUT)
                
                await self.log_operation(deployment_id, f"Tunnel restarted with new route for {hostname}")
            else:
                await self.log_operation(deployment_id, f"Tunnel route already exists for {hostname}")
            
            return True
                
        except Exception as e:
            await self.log_operation(deployment_id, f"Tunnel route creation failed: {str(e)}", LogLevel.ERROR)
            return False
    
    async def remove_dns_record(self, subdomain: str, deployment_id: Optional[str] = None) -> bool:
        try:
            if deployment_id:
                await self.log_operation(deployment_id, f"Removing DNS record for {subdomain}")
            
            record_name = f"{subdomain}.{self.base_domain}"
            
            # Find the record
            records = await self._make_request(
                "GET",
                f"/zones/{self.zone_id}/dns_records?name={record_name}"
            )
            
            if not records or not records.get("result"):
                if deployment_id:
                    await self.log_operation(deployment_id, f"DNS record not found for {record_name}")
                return True
            
            # Delete each matching record
            for record in records["result"]:
                result = await self._make_request(
                    "DELETE",
                    f"/zones/{self.zone_id}/dns_records/{record['id']}"
                )
                
                if result and result.get("success"):
                    if deployment_id:
                        await self.log_operation(deployment_id, f"DNS record deleted for {record_name}")
                else:
                    if deployment_id:
                        await self.log_operation(deployment_id, f"Failed to delete DNS record: {result}", LogLevel.ERROR)
                    return False
            
            return True
            
        except Exception as e:
            if deployment_id:
                await self.log_operation(deployment_id, f"DNS record removal failed: {str(e)}", LogLevel.ERROR)
            else:
                print(f"DNS record removal failed: {e}")
            return False
    
    async def remove_tunnel_route(self, subdomain: str, deployment_id: Optional[str] = None) -> bool:
        try:
            if deployment_id:
                await self.log_operation(deployment_id, f"Removing tunnel route for {subdomain}")
            
            hostname = f"{subdomain}.{self.base_domain}"
            config_path = os.path.expanduser("~/.cloudflared/config.yml")
            
            # Read current config as text
            with open(config_path, 'r') as f:
                lines = f.readlines()
            
            # Remove lines that contain this hostname
            original_length = len(lines)
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                if f"hostname: {hostname}" in line:
                    skip_next = True  # Skip the service line too
                    continue
                elif skip_next and "service:" in line:
                    skip_next = False
                    continue
                else:
                    filtered_lines.append(line)
            
            if len(filtered_lines) < original_length:
                # Write updated config
                with open(config_path, 'w') as f:
                    f.writelines(filtered_lines)
                
                if deployment_id:
                    await self.log_operation(deployment_id, f"Removed tunnel route for {hostname}")
                
                # Restart tunnel to apply changes
                import subprocess
                subprocess.run(['pkill', 'cloudflared'], check=False)
                subprocess.Popen([
                    'cloudflared', 'tunnel', '--config', config_path, 'run'
                ], stdout=open('logs/tunnel.log', 'w'), stderr=subprocess.STDOUT)
                
                if deployment_id:
                    await self.log_operation(deployment_id, f"Tunnel restarted after removing route for {hostname}")
            else:
                if deployment_id:
                    await self.log_operation(deployment_id, f"No tunnel route found for {hostname}")
            
            return True
        except Exception as e:
            if deployment_id:
                await self.log_operation(deployment_id, f"Tunnel route removal failed: {str(e)}", LogLevel.ERROR)
            else:
                print(f"Tunnel route removal failed: {e}")
            return False
    
    async def setup_deployment_cloudflare(self, subdomain: str, port: int, deployment_id: str) -> bool:
        try:
            # Create DNS record
            dns_success = await self.create_dns_record(subdomain, deployment_id)
            if not dns_success:
                return False
            
            # Create tunnel route
            tunnel_success = await self.create_tunnel_route(subdomain, port, deployment_id)
            if not tunnel_success:
                # Cleanup DNS record if tunnel fails
                await self.remove_dns_record(subdomain, deployment_id)
                return False
            
            await self.log_operation(deployment_id, f"Cloudflare setup completed for {subdomain}.{self.base_domain}")
            return True
            
        except Exception as e:
            await self.log_operation(deployment_id, f"Cloudflare setup failed: {str(e)}", LogLevel.ERROR)
            return False