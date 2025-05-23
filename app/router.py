import logging

import psycopg2
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status

from app.auth import create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, hash_password, verify_user
from app.database.calls import retrieve_owner
from app.database.config import load_config
from app.pydantic_models import OwnerCreate, OwnerLogin, ProjectRequest
from app.simulation import prioritize

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Authentication
@router.post("/api/auth/login")
def login(request: OwnerLogin):
    user = authenticate_user(request.email, request.password)
    if not user:
        logging.error("Authentication failed for user: %s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/auth/register", status_code=201)
def register_user(request: OwnerCreate):
    hashed_password = hash_password(request.password)

    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Owner WHERE email = %s", (request.email,))
            if cur.fetchone():
                logging.error("User already exists")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists",
                )

            cur.execute(
                "INSERT INTO Owner (email, password, name, firstname) VALUES (%s, %s, %s, %s)",
                (request.email, hashed_password, request.nom, request.prenom)
            )
            conn.commit()
    logging.info("User registered successfully: %s", request.email)

@router.post("/api/auth/refresh")
def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token.")
        verify_user(email)

        new_token = create_access_token({"sub": email})
        return {"access_token": new_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Cannot refresh token.")


# Project Management
@router.get("/api/projects/retrieve")
def get_projects(owner: int = Depends(retrieve_owner)):
    data = []

    # TODO: Change this as well as the database
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM test")
            rows = cur.fetchall()
            for row in rows:
                project = {
                    "id": row[0],
                    "nom": row[1],
                    "description": row[2],
                    "details": row[3]
                }
                data.append(project)
    return data

@router.get("/api/projects/{project_id}")
def get_project(project_id: int, owner: int = Depends(retrieve_owner)):
    # TODO: Change this as well as the database
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM test WHERE id = %s", (project_id,))
            row = cur.fetchone()
            if not row:
                logging.error("Project not found: %s", project_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Projet non trouvé."
                )
            project = {
                "id": row[0],
                "nom": row[1],
                "description": row[2],
                "details": row[3]
            }
    return project

@router.post("/api/projects/create")
def create_project(
        request: ProjectRequest,
        owner: int = Depends(retrieve_owner)
):
    dataframe = prioritize(request)
    config = load_config()

    # TODO: Change this as well as the database
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO test (name, description, details) VALUES (%s, %s, %s)
            """, (request.name, request.description, dataframe.to_json(orient="records")))

    return dataframe.to_json(orient="records")
