from datetime import date

from pydantic import BaseModel, ConfigDict


class UsedVacationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    start_date: date
    end_date: date
