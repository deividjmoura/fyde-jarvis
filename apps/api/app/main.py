from fastapi import FastAPI
from app.api.routes import health
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Assistente IA modular"
)

# Rotas
app.include_router(health.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "project": "Fyde Jarvis",
        "status": "online"
    }