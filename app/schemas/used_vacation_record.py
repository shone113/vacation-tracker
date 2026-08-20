from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator


class UsedVacationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    start_date: date
    end_date: date


class UsedVacationRecordCreate(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_date_order(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self
