import json
import logging
import os

import psycopg2
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status

from app.auth import create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, hash_password, verify_user, \
    check_admin, verify_token
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["email"], "is_admin": user["is_admin"]}
    )
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user["is_admin"]}


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
            cur.execute("SELECT * FROM test where owner_id = %s", (owner,))
            rows = cur.fetchall()
            for row in rows:
                project = {
                    "id": row[0],
                    "name": row[1],
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
            INSERT INTO test (name, description, details, owner_id) VALUES (%s, %s, %s, %s)
            """, (request.name, request.description, dataframe.to_json(orient="records")), owner)

    return dataframe.to_json(orient="records")

@router.get("/api/admin/weighting", dependencies=[Depends(check_admin)])
def get_weighting_files():
    try:
        weighting_path = "app/weighting"
        json_files = []

        for filename in os.listdir(weighting_path):
            if filename.endswith('.json'):
                file_path = os.path.join(weighting_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    json_files.append({
                        "filename": filename,
                        "content": content
                    })

        return json_files
    except Exception as e:
        logging.error(f"Erreur lors de la lecture des fichiers JSON : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des fichiers de pondération"
        )

@router.get("/api/auth/check-admin")
async def check_admin_status(payload: dict = Depends(verify_token)):
    try:
        is_admin = payload.get("is_admin", False)
        return {"is_admin": is_admin}
    except JWTError as e:
        logging.error("Token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )