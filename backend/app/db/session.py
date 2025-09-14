import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.settings import settings
DATABASE_URL = str(settings.DATABASE_URL)

# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/softball")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)