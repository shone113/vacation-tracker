from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_current_employee
from app.api.routes.admin import router as admin_router
from app.db.database import get_db
from app.models.employee import Employee

app = FastAPI(title="Vacation Tracker API")
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}

@app.get("/me")
def read_current_employee(employee: Employee = Depends(get_current_employee)):
    return {"email": employee.email, "role": employee.role}