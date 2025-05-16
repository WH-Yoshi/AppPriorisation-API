import logging
from datetime import datetime

import pymupdf
import psycopg2
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status
from starlette.responses import Response, JSONResponse

from app.auth import create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, hash_password, verify_token
from app.pydantic_models import ProprietaireCreate, ProprietaireLogin, HabitationCreate, ProjectRequest
from app.database.config import load_config
from app.simulation import prioritize

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Authentication
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

# Projets
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
        request: ProjectRequest,
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
            proprietaire = proprietaire[0]

    prioritize(request)

    #         cur.execute(
    #             """
    #             INSERT INTO habitation (nom, description, objectif, region, annee_construction, surface,
    #                                     type_habitation, label_peb, type_chauffage, temperature_moyenne,
    #                                     theromstat_programmable, type_fenetre, isolation_mur, isolation_toit,
    #                                     isolation_sol, revenu_menage, nombre_enfants, methode_renovation, proprietaire_id)
    #             """,
    #             (request.nom, request.description, request.objectif, request.region, request.annee_construction,
    #              request.surface, request.type_habitation, request.label_peb, request.type_chauffage,
    #              request.temperature_moyenne, request.thermostat_programmable, request.type_fenetre,
    #              request.isolation_mur, request.isolation_toit, request.isolation_sol, request.revenu_menage,
    #              request.nombre_enfants, request.methode_renovation, proprietaire[0])
    #         )
    #         now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    #         cur.execute(
    #             """
    #             INSERT INTO simulation (date, budget_max, liste_travaux_id, habitation_id)
    #             VALUES (%s, %s, %s, %s, %s)
    #             """,
    #             (now, request.budget_max, request.liste_travaux_id, request.habitation_id)
    #         )
    #     conn.commit()
    return {"message": "Projet créé avec succès."}

