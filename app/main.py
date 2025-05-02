import os
import asyncpg
from fastapi import FastAPI

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API OK"}

@app.get("/test-db")
async def test_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "success", "message": "Connection to DB is OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}