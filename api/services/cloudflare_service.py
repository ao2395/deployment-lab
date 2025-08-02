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
            
            # For now, just log that tunnel route creation is skipped
            # The tunnel is already configured via nginx proxy, so we don't need dynamic tunnel routes
            await self.log_operation(deployment_id, f"Tunnel route creation skipped - using nginx proxy instead")
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
            
            # Get current tunnel configuration
            current_config = await self._make_request(
                "GET",
                f"/accounts/{self.zone_id}/cfd_tunnel/{self.tunnel_id}/configurations"
            )
            
            if not current_config or not current_config.get("result"):
                if deployment_id:
                    await self.log_operation(deployment_id, "No tunnel configuration found")
                return True
            
            hostname = f"{subdomain}.{self.base_domain}"
            config = current_config["result"].get("config", {})
            ingress = config.get("ingress", [])
            
            # Remove the specific hostname from ingress rules
            updated_ingress = [rule for rule in ingress if rule.get("hostname") != hostname]
            
            # Update tunnel configuration
            data = {
                "config": {
                    "ingress": updated_ingress
                }
            }
            
            result = await self._make_request(
                "PUT",
                f"/accounts/{self.zone_id}/cfd_tunnel/{self.tunnel_id}/configurations",
                data
            )
            
            if result and result.get("success"):
                if deployment_id:
                    await self.log_operation(deployment_id, f"Tunnel route removed for {hostname}")
                return True
            else:
                if deployment_id:
                    await self.log_operation(deployment_id, f"Failed to remove tunnel route: {result}", LogLevel.ERROR)
                return False
                
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