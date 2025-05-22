from pydantic import BaseModel, EmailStr

class OwnerCreate(BaseModel):
    email: EmailStr
    password: str
    nom: str
    prenom: str

class OwnerLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DwellingCreate(BaseModel):
    nom: str
    description: str
    region: str
    constructionYear: int
    surface: int
    housingType: str
    pebLabel: str

class HousingData(BaseModel):
    surface: str
    roofType: str
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
    childNumber: str
    propertyType: str
    renovationMethod: str
    floorNumber: str

class TechnicalData(BaseModel):
    hasSolarPanels: str
    hasWaterHeater: str
    boilerType: str
    ventilationType: str

class ProjectRequest(BaseModel):
    name: str
    description: str
    profilData: str
    region: str
    housingData: HousingData
    budgetData: BudgetData
    technicalData: TechnicalData