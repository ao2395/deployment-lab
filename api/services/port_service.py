import os
from datetime import datetime
from typing import Optional
from models import get_database, PortRegistryModel

class PortService:
    def __init__(self):
        self.min_port = int(os.getenv("MIN_PORT", "3000"))
        self.max_port = int(os.getenv("MAX_PORT", "8000"))
        
    async def find_available_port(self, deployment_id: str) -> Optional[int]:
        try:
            db = get_database()
            
            # Find all allocated ports
            allocated_ports = await db.port_registry.find(
                {"is_allocated": True}
            ).to_list(length=None)
            
            allocated_port_numbers = {port["port"] for port in allocated_ports}
            
            # Find first available port in range
            for port in range(self.min_port, self.max_port + 1):
                if port not in allocated_port_numbers:
                    # Reserve this port
                    port_record = PortRegistryModel(
                        port=port,
                        is_allocated=True,
                        deployment_id=deployment_id,
                        allocated_at=datetime.utcnow()
                    )
                    
                    await db.port_registry.insert_one(port_record.dict())
                    return port
            
            return None
            
        except Exception as e:
            print(f"Error finding available port: {e}")
            return None
    
    async def release_port(self, port: int) -> bool:
        try:
            db = get_database()
            
            result = await db.port_registry.update_one(
                {"port": port},
                {
                    "$set": {
                        "is_allocated": False,
                        "deployment_id": None,
                        "released_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error releasing port {port}: {e}")
            return False
    
    async def is_port_available(self, port: int) -> bool:
        try:
            db = get_database()
            
            port_record = await db.port_registry.find_one(
                {"port": port, "is_allocated": True}
            )
            
            return port_record is None
            
        except Exception as e:
            print(f"Error checking port availability: {e}")
            return False