from fastapi import FastAPI

app = FastAPI(title="Vacation Tracker API")

@app.get("/health")
def health_check():
    return {"status": "ok"}