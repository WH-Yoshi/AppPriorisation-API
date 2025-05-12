from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.router import router


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://app-priorisation.vercel.app","http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]
app = FastAPI(middleware=middleware)

app.include_router(router=router)