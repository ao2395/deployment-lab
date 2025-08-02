from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, Annotated
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_json_schema__(cls, _source_type, _handler):
        return {"type": "string"}
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    BUILDING = "building"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class LogLevel(str, Enum):
    INFO = "info"
    ERROR = "error"
    DEBUG = "debug"
    WARNING = "warning"

class UserModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeploymentModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    github_url: str
    subdomain: str
    port: int
    status: DeploymentStatus = DeploymentStatus.PENDING
    container_id: Optional[str] = None
    docker_image: Optional[str] = None
    user_id: str = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    env_vars: Dict[str, Any] = Field(default_factory=dict)

class PortRegistryModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    port: int
    is_allocated: bool = False
    deployment_id: Optional[str] = None
    allocated_at: Optional[datetime] = None
    released_at: Optional[datetime] = None

class BuildLogModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    deployment_id: str
    log_level: LogLevel = LogLevel.INFO
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DeploymentCreate(BaseModel):
    github_url: str
    subdomain: str
    env_vars: Dict[str, Any] = Field(default_factory=dict)

class DeploymentResponse(BaseModel):
    model_config = ConfigDict(json_encoders={ObjectId: str})
    
    id: str
    name: str
    github_url: str
    subdomain: str
    port: int
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime