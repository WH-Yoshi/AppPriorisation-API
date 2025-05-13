import logging
import os
import datetime
from datetime import timedelta

import psycopg2
from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext

from app.database.config import load_config

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(email: str, password: str):
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password FROM Proprietaire WHERE email = %s", (email,))
                user = cur.fetchone()
                if user and verify_password(password, user[1]):
                    return {"id": user[0], "email": email}
                return None
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Erreur lors de l'authentification.")