from pydantic import BaseModel, ConfigDict

from app.models.employee import EmployeeRole


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: EmployeeRole
