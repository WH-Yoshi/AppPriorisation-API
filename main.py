import uvicorn
from app.database.create_tables import create_tables

if __name__ == "__main__":
    create_tables()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
