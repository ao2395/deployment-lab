import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "deployment_lab")

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    # Fix SSL certificate issues for MongoDB Atlas
    if "mongodb+srv" in MONGODB_URL or "mongodb.net" in MONGODB_URL:
        mongodb.client = AsyncIOMotorClient(
            MONGODB_URL, 
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
    else:
        mongodb.client = AsyncIOMotorClient(MONGODB_URL)
    
    mongodb.database = mongodb.client[DATABASE_NAME]
    
async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()

def get_database():
    return mongodb.database

async def create_indexes():
    db = get_database()
    
    await db.deployments.create_index("subdomain", unique=True)
    await db.deployments.create_index("port", unique=True)
    await db.port_registry.create_index("port", unique=True)
    await db.users.create_index("username", unique=True)