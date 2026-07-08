from fastapi import FastAPI

app = FastAPI(
    title="MusicAI API",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "status": "running",
        "project": "MusicAI"
    }