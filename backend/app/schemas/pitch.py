from pydantic import BaseModel, field_validator
from datetime import date

class PitchIn(BaseModel):
    game_date: date
    pitcher: str
    batter: str
    pitch_type: str
    result: str

    @field_validator("result")
    @classmethod
    def valid_result(cls, v: str) -> str:
        allowed = {"swing_miss","foul","in_play","ball","called_strike"}
        if v not in allowed:
            raise ValueError(f"result must be one of {allowed}")
        return v

class PitchOut(PitchIn):
    id: int
