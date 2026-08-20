from app.db.database import SessionLocal
from app.core.security import hash_password
from app.models import Employee, EmployeeRole

db = SessionLocal()

def create_if_not_exists(email, password, role):
    existing = db.query(Employee).filter_by(email=email).first()
    if existing:
        print(f"{email} already exists, skipping.")
        return
    emp = Employee(
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(emp)
    print(f"{email} created.")

create_if_not_exists("admin@example.com", "JakaSifra123", EmployeeRole.admin)
create_if_not_exists("employee@example.com", "employee123", EmployeeRole.employee)

db.commit()
db.close()

print("Seed skripta zavrsena.")