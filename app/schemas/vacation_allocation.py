from pydantic import BaseModel, ConfigDict


class VacationAllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_email: str
    year: int
    total_days: int
