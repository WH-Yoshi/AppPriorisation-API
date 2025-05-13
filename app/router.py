import logging

import psycopg2
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status
from starlette.responses import Response

from app.auth import create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, hash_password
from app.pydantic_models import UserProfile, ProprietaireCreate
from app.database.config import load_config

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/api/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logging.error("Authentication failed for user: %s", form_data.username)
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

@router.get("/me")
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            logging.error("Token does not contain email")
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        logging.error("Token expired")
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email}

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