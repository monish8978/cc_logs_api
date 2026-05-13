from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
    status,
    Depends
)
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from jose import jwt, JWTError
from datetime import datetime, timedelta

import boto3
from botocore.client import Config

import asyncio
import traceback
import re
import json
import redis.asyncio as redis

from services.elastic import ElasticsearchService
from utils.response import success_response, error_response
from logger import log
from db.db import init_db_pool, close_db_pool, get_db_conn
from config import *
from worker import insert_log_task

from pydantic import BaseModel, field_validator
from typing import Optional, Union, Any

# =========================================================
# REDIS CACHE INITIALIZATION
# =========================================================
redis_client = None

async def init_redis():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        log.info("✅ Redis connected successfully")
    except Exception as e:
        log.error(f"❌ Redis connection failed: {str(e)}")

# =========================================================
# LIFESPAN (Connection Management)
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize pools
    log.info(f"🔍 Starting API with DB_HOST={DB_HOST}, REDIS_URL={REDIS_URL}")
    await init_db_pool()
    await init_redis()
    # Note: Elasticsearch index is created in ElasticsearchService.__init__ (synchronously)
    log.info("🚀 API Services Started")
    yield
    # Shutdown: Close pools
    await close_db_pool()
    if redis_client:
        await redis_client.close()
    # es_service.es.close() # Synchronous close if needed
    log.info("🛑 API Services Stopped")

# =========================================================
# FASTAPI APP
# =========================================================
app = FastAPI(
    title="CC Logs API",
    description="Production Ready Logging API with Cache and Task Manager",
    version="1.2.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
es_service = ElasticsearchService()
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name="ap-south-1",
    config=Config(signature_version="s3v4", max_pool_connections=50)
)

# =========================================================
# PYDANTIC MODELS
# =========================================================
class CreateClientRequest(BaseModel):
    client_id: str
    access_key: str
    expiry_date: str
    status: Union[str, bool, int] = "1"

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Any) -> str:
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, int):
            return str(v) if v in [0, 1] else "1"
        if isinstance(v, str):
            if v.lower() in ["true", "1", "active"]: return "1"
            if v.lower() in ["false", "0", "inactive"]: return "0"
        return str(v)

class RotateKeyRequest(BaseModel):
    client_id: str
    new_key: str

class DisableClientRequest(BaseModel):
    client_id: str

class CheckVersionRequest(BaseModel):
    client_id: str
    current_version: str

class ValidateKeyRequest(BaseModel):
    access_key: str

# =========================================================
# UTILITIES (Async Wrappers for Sync Services)
# =========================================================
async def upload_to_s3(file_obj, bucket, key):
    return await asyncio.to_thread(s3_client.upload_fileobj, file_obj, bucket, key)

async def generate_s3_url(bucket, key):
    return await asyncio.to_thread(
        s3_client.generate_presigned_url,
        "get_object",
        Params={"Bucket": bucket, "Key": key, "ResponseContentDisposition": "attachment"},
        ExpiresIn=300
    )

async def es_fetch_logs(page, size):
    return await asyncio.to_thread(es_service.fetch_logs, page, size)

async def es_search_logs(agentId, macAddress, level, start_date, end_date, page, size):
    return await asyncio.to_thread(es_service.search_logs, agentId, macAddress, level, start_date, end_date, page, size)

# =========================================================
# ROUTES
# =========================================================

@app.get("/", tags=["Health"])
async def health():
    return success_response(message="API Running Successfully 🚀")

@app.post("/admin/create-client", tags=["Admin"])
async def create_client(data: CreateClientRequest, conn=Depends(get_db_conn)):
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("SELECT id FROM clients WHERE client_id=%s", (data.client_id,))
            if await cursor.fetchone():
                return error_response(message="Client ID already exists", status_code=409)

            await cursor.execute(
                "INSERT INTO clients (client_id, access_key, expiry_date, status) VALUES (%s,%s,%s,%s)",
                (data.client_id, data.access_key, data.expiry_date, data.status)
            )
            return success_response(message="Client created successfully")
        except Exception as e:
            log.error(f"Create client failed: {str(e)}", exc_info=True)
            return error_response(message="Failed to create client", status_code=500, error=e)

@app.post("/admin/rotate-key", tags=["Admin"])
async def rotate_key(data: RotateKeyRequest, conn=Depends(get_db_conn)):
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("UPDATE clients SET access_key=%s WHERE client_id=%s", (data.new_key, data.client_id))
            if cursor.rowcount == 0:
                return error_response(message="Client not found", status_code=404)
            return success_response(message="Access key rotated successfully")
        except Exception as e:
            log.error(f"Rotate key failed: {str(e)}", exc_info=True)
            return error_response(message="Failed to rotate key", status_code=500, error=e)

@app.post("/admin/disable-client", tags=["Admin"])
async def disable_client(data: DisableClientRequest, conn=Depends(get_db_conn)):
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("UPDATE clients SET status='0' WHERE client_id=%s", (data.client_id,))
            if cursor.rowcount == 0:
                return error_response(message="Client not found", status_code=404)
            return success_response(message="Client disabled successfully")
        except Exception as e:
            log.error(f"Disable client failed: {str(e)}", exc_info=True)
            return error_response(message="Failed to disable client", status_code=500, error=e)

@app.post("/admin/upload-version", tags=["Admin"])
async def upload_version(
    version: str = Form(...),
    client_id: str = Form(...),
    release_notes: str = Form(...),
    mandatory: bool = Form(...),
    file: UploadFile = File(...),
    conn=Depends(get_db_conn)
):
    try:
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", file.filename)
        s3_key = f"versions/{version}_{clean_name}"

        await upload_to_s3(file.file, BUCKET_NAME, s3_key)

        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO versions (version, client_id, release_notes, mandatory, file_path) VALUES (%s,%s,%s,%s,%s)",
                (version, client_id, release_notes, mandatory, s3_key)
            )
        
        if redis_client:
            await redis_client.delete(f"version_cache:{client_id}")

        return success_response(message="Version uploaded successfully")
    except Exception as e:
        log.error(f"Upload version failed: {str(e)}", exc_info=True)
        return error_response(message="Failed to upload version", status_code=500, error=e)

@app.post("/check-version", tags=["Version"])
async def check_version(data: CheckVersionRequest, conn=Depends(get_db_conn)):
    cache_key = f"version_cache:{data.client_id}"
    
    if redis_client:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            cached_json = json.loads(cached_data)
            latest_version = cached_json["version"]
            update_available = list(map(int, latest_version.split("."))) > list(map(int, data.current_version.split(".")))
            cached_json["update_available"] = update_available
            cached_json["current_version"] = data.current_version
            return success_response(message="Version checked (cached)", data=cached_json)

    async with conn.cursor() as cursor:
        try:
            await cursor.execute("SELECT * FROM versions WHERE client_id=%s ORDER BY id DESC LIMIT 1", (data.client_id,))
            version = await cursor.fetchone()

            if not version:
                return error_response(message="No version available", status_code=404)

            latest_version = version["version"]
            update_available = list(map(int, latest_version.split("."))) > list(map(int, data.current_version.split(".")))

            resp_data = {
                "client_id": data.client_id,
                "current_version": data.current_version,
                "latest_version": latest_version,
                "update_available": update_available,
                "mandatory": bool(version["mandatory"]),
                "release_notes": version["release_notes"],
                "version": latest_version
            }

            if redis_client:
                await redis_client.setex(cache_key, 3600, json.dumps(resp_data))

            return success_response(message="Version checked successfully", data=resp_data)
        except Exception as e:
            log.error(f"Check version failed: {str(e)}", exc_info=True)
            return error_response(message="Version check failed", status_code=500, error=e)

@app.post("/push-log/", tags=["Logs"])
async def push_log(request: Request):
    try:
        data = await request.json()
        insert_log_task.delay(data)
        return success_response(message="Log accepted for processing")
    except Exception as e:
        log.error(f"Push log failed: {str(e)}", exc_info=True)
        return error_response(message="Push log failed", status_code=500, error=e)

@app.post("/validate-key", tags=["Validation"])
async def validate_key(data: ValidateKeyRequest, request: Request, conn=Depends(get_db_conn)):
    async with conn.cursor() as cursor:
        try:
            await cursor.execute("SELECT * FROM clients WHERE access_key=%s", (data.access_key,))
            client = await cursor.fetchone()

            if not client or str(client["status"]) != "1" or client["expiry_date"] < datetime.now():
                return error_response(message="Invalid or inactive access key", status_code=401)

            await cursor.execute("SELECT * FROM versions ORDER BY id DESC LIMIT 1")
            version = await cursor.fetchone()

            if not version: return error_response(message="No version found", status_code=404)

            download_url = await generate_s3_url(BUCKET_NAME, version["file_path"])

            await cursor.execute(
                "INSERT INTO logs (client_id, version, ip) VALUES (%s,%s,%s)",
                (client["client_id"], version["version"], request.client.host)
            )

            return success_response(message="Access granted", data={
                "client_id": client["client_id"],
                "download_url": download_url,
                "expires_in": "5 minutes"
            })
        except Exception as e:
            log.error(f"Validate key failed: {str(e)}", exc_info=True)
            return error_response(message="Validation failed", status_code=500, error=e)

@app.get("/get-logs/", tags=["Logs"])
async def get_logs(page: int = 1, size: int = 100):
    try:
        result = await es_fetch_logs(page, size)
        return success_response(message="Logs fetched", data=result)
    except Exception as e:
        return error_response(message="Failed to fetch logs", status_code=500, error=e)

@app.get("/search-logs/", tags=["Logs"])
async def search_logs(agentId: str = None, macAddress: str = None, level: str = None, start_date: str = None, end_date: str = None, page: int = 1, size: int = 100):
    try:
        result = await es_search_logs(agentId, macAddress, level, start_date, end_date, page, size)
        return success_response(message="Logs fetched", data=result)
    except Exception as e:
        return error_response(message="Search failed", status_code=500, error=e)

if __name__ == "__main__":
    import uvicorn
    # Use standard asyncio loop as uvloop is not installed in the environment
    uvicorn.run("main:app", host=API_IP, port=API_PORT, workers=4, loop="asyncio")