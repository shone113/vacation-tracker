from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.routes.admin import router as admin_router
from app.api.routes.employee import router as employee_router
from app.db.database import get_db

app = FastAPI(title="Vacation Tracker API")
app.include_router(admin_router)
app.include_router(employee_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
