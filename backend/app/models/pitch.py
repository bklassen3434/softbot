from sqlalchemy import Date, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Pitch(Base):
    __tablename__ = "pitches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_date: Mapped[str] = mapped_column(Date, index=True)
    pitcher: Mapped[str] = mapped_column(String(80), index=True)
    batter: Mapped[str] = mapped_column(String(80), index=True)
    pitch_type: Mapped[str] = mapped_column(String(40), index=True)
    result: Mapped[str] = mapped_column(String(40), index=True)
