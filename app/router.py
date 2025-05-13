import os
from fastapi import APIRouter, HTTPException
import psycopg2
from .pydantic_models import UserProfile

DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter()


@router.post("/profil-utilisateur")
async def create_user_profile(profil: UserProfile):
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)

        return {"message": "Profil utilisateur enregistré avec succès."}
    except Exception as e:
        print(f"Erreur lors de l'enregistrement: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement.")
