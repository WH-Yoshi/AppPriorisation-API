import logging

import psycopg2
from fastapi import Depends, HTTPException
from starlette import status

from app.auth import verify_token
from app.database.config import load_config
from app.pydantic_models import ProjectRequest

config = load_config()

def retrieve_owner(payload: dict = Depends(verify_token)):
    email = payload.get("sub")
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM Owner WHERE email = %s", (email,))
            owner = cur.fetchone()
            if not owner:
                logging.error("Owner not found for email: %s", email)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Owner not found."
                )
            return owner[0]

def insert_project(project_data: ProjectRequest):
    pass