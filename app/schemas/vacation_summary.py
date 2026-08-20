from pydantic import BaseModel


class VacationSummaryOut(BaseModel):
    year: int
    total_days: int
    used_days: int
    available_days: int
