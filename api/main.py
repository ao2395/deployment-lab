from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models import connect_to_mongo, close_mongo_connection, create_indexes
from app.auth import router as auth_router
from app.deployments import router as deployments_router

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
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