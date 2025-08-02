from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging
from models import connect_to_mongo, close_mongo_connection, create_indexes
from app.auth import router as auth_router
from app.deployments import router as deployments_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    await create_indexes()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Auto-Deployment API",
    description="API for managing automated deployments from GitHub repositories",
    version="1.0.0",
    lifespan=lifespan
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # Simple log: METHOD URL -> STATUS (TIME)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.3f}s)")
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://deployment-lab.ao2395.com"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(deployments_router)

@app.get("/")
async def read_root():
    return {"message": "Auto-Deployment API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}