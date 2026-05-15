from fastapi import FastAPI

app = FastAPI(
    title="Fyde Jarvis API"
)

@app.get("/")
def home():
    return {
        "status": "online"
    }
