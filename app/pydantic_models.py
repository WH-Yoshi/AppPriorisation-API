from pydantic import BaseModel


class UserProfile(BaseModel):
    objectif_principal: str