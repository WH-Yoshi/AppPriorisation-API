from pydantic import BaseModel, EmailStr

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

class HabitationCreate(BaseModel):
    nom: str
    description: str
    region: str
    annee_construction: int
    surface: int
    type_logement: str
    label_peb: str

class LogementData(BaseModel):
    heatingType: str
    averageTemperature: str
    programmableThermostat: str
    windowType: str
    wallInsulation: str
    roofInsulation: str
    floorInsulation: str

class BudgetData(BaseModel):
    totalBudget: str
    householdIncome: str
    householdSize: str
    propertyType: str
    renovationMethod: str

class ProjectRequest(BaseModel):
    name: str
    description: str
    profilData: str
    logementData: LogementData
    budgetData: BudgetData