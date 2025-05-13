from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    objectif_principal: str

class ProprietaireCreate(BaseModel):
    email: EmailStr
    password: str
    nom: str
    prenom: str

class ProprietaireLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
