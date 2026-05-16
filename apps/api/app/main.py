from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings

from app.db.session import engine
from app.db.base import Base

from app.db.models import User


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Assistente IA modular"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(health.router)


@app.get("/")
def root():
    return {
        "project": settings.APP_NAME,
        "status": "online"
    }