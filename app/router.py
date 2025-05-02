import os
import asyncpg
from fastapi import APIRouter, Security, HTTPException
from fastapi.security import APIKeyHeader

DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

@router.get("/test-db", dependencies=[Security(verify_api_key)])
async def test_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "success", "message": "Connection to DB is OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}