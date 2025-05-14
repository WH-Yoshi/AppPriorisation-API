import logging

import psycopg2
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status
from starlette.responses import Response

from app.auth import create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, hash_password, verify_token, \
    verify_expired_token
from app.pydantic_models import UserProfile, ProprietaireCreate, ProprietaireLogin, HabitationCreate
from app.database.config import load_config

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/api/auth/login")
def login(request: ProprietaireLogin):
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
def register_user(request: ProprietaireCreate):
    hashed_password = hash_password(request.password)

    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM Proprietaire WHERE email = %s", (request.email,))
            if cur.fetchone():
                logging.error("User already exists")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="L'utilisateur existe déjà."
                )

            cur.execute(
                "INSERT INTO Proprietaire (email, password, nom, prenom) VALUES (%s, %s, %s, %s)",
                (request.email, hashed_password, request.nom, request.prenom)
            )
            conn.commit()

    return {"message": "Utilisateur créé avec succès."}

@router.post("/api/auth/refresh")
def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalide.")

        new_token = create_access_token({"sub": email})
        return {"access_token": new_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Impossible de rafraîchir le token.")

@router.get("/api/projects/retrieve")
def get_projects(payload: dict = Depends(verify_token)):
    data = []
    email = payload.get("sub")
    config = load_config()

    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM habitation")
            rows = cur.fetchall()
            for row in rows:
                data.append({
                    "id": row[0],
                    "nom": row[1],
                    "description": row[2],
                    "date_debut": row[3],
                    "date_fin": row[4]
                })
    return data

@router.post("/api/projects/create")
def create_project(
        request: HabitationCreate,
        payload: dict = Depends(verify_token)
):
    config = load_config()
    email = payload.get("sub")
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM proprietaire WHERE email = %s", (email,))
            proprietaire = cur.fetchone()
            if not proprietaire:
                logging.error("Proprietaire not found for email: %s", email)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Propriétaire non trouvé."
                )

            cur.execute(
                "INSERT INTO habitation (nom, description, date_debut, date_fin) VALUES (%s, %s, %s, %s)",
                (request.nom, request.description, request.date_debut, request.date_fin)
            )
            conn.commit()
    return {"message": "Projet créé avec succès."}

@router.post("/profil-utilisateur")
async def create_user_profile(profil: UserProfile):

    print(profil)

    sql = """
        SELECT * FROM proprietaire
    """

    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
    except Exception as e:
        logging.error("Erreur lors de l'enregistrement: %s", e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement.")

    Response(content="Profil utilisateur enregistré avec succès.", status_code=200)