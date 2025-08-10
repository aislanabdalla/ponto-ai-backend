from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

DB_URL = os.getenv("DB_URL", "sqlite:///./ponto.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    document = Column(String, unique=True, nullable=True)  # CPF etc (optional)
    email = Column(String, unique=True, nullable=True)
    face_embedding = Column(String, nullable=True)  # JSON-encoded list[float]
    photo_path = Column(String, nullable=True)

    punches = relationship("Punch", back_populates="employee")

class Punch(Base):
    __tablename__ = "punches"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    similarity = Column(Float, nullable=True)
    photo_path = Column(String, nullable=True)

    employee = relationship("Employee", back_populates="punches")

def init_db():
    Base.metadata.create_all(bind=engine)
