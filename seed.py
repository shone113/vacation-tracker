from app.db.database import SessionLocal
from app.core.security import hash_password
from app.models import Employee

db = SessionLocal()

admin = Employee(
    email="admin@example.com",
    hashed_password=hash_password("admin123"),
    role="admin",
    # dodaj i ostala obavezna polja tvog modela, npr. name="Admin"
)

employee = Employee(
    email="employee@example.com",
    hashed_password=hash_password("employee123"),
    role="employee",
    # dodaj i ostala obavezna polja tvog modela, npr. name="Test Employee"
)

db.add(admin)
db.add(employee)
db.commit()
db.close()

print("Admin i employee nalozi kreirani.")