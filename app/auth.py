import datetime
import logging
import os
from datetime import timedelta

import psycopg2
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import EmailStr
from starlette import status

from app.database.config import load_config
from app.pydantic_models import TokenData

load_dotenv()

SECRET_KEY = os.getenv('POSTGRES_PASSWORD')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(email: str, password: str):
    user = get_user_with_role(email)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

def verify_user(email: EmailStr):
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM Owner WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")

        config = load_config()
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM Owner WHERE email = %s", (email,))
                user = cur.fetchone()
                if not user:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid.")

def verify_expired_token(token: str) -> bool:
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return False
    except ExpiredSignatureError:
        return True
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid.")

def get_user_with_role(email: str):
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email, password, is_admin FROM Owner WHERE email = %s", (email,))
            user = cur.fetchone()
            if user:
                return {
                    "email": user[0],
                    "password": user[1],
                    "is_admin": user[2]
                }
    return None

async def get_current_user(
        token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        if email is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        token_data = TokenData(email=email, is_admin=is_admin)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    return token_data

def check_admin(user: TokenData = Security(get_current_user)):
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Permission refusée : accès administrateur requis"
        )
    return user
