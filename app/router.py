import os
from fastapi import APIRouter, HTTPException
from .pydantic_models import UserProfile

DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter()


@router.post("/profil-utilisateur")
async def create_user_profile(profil: UserProfile):
    try:
        # Insertion dans la base de données
        cursor.execute("INSERT INTO user_profiles (objectif_principal) VALUES (?)", (profil.objectif_principal,))
        conn.commit()
        return {"message": "Profil utilisateur enregistré avec succès."}
    except Exception as e:
        print(f"Erreur lors de l'enregistrement: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement.")



@router.get("/test-db")
async def test_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        return {"status": "success", "message": "Connection to DB is OK"}
    except Exception as e:
        return {"status": "error", "message": str(e)}