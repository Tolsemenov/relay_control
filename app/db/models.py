# app/db/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class RelayTarget(str, enum.Enum):
    """Назначение каждого реле (реле1 = насос, реле2 = кран и т.д.)target """
    valve1 = "valve1"
    valve2 = "valve2"
    valve3 = "valve3"
    valve4 = "valve4"

class Schedule(Base):
    """Расписание для включения реле"""
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True)
    target = Column(Enum(RelayTarget), nullable=False)          # Насос, кран и т.п.
    days = Column(String, nullable=False)                       # Пример: "Mon,Wed,Fri"
    time_on = Column(Time, nullable=False)                      # Время включения
    duration_min = Column(Integer, nullable=False)              # Длительность в минутах
    enabled = Column(Boolean, default=True)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String, nullable=True)  # ✅ должен быть!
    level = Column(String, nullable=False)
    action = Column(String, nullable=True)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class RelayName(Base):
    __tablename__ = "relay_names"

    id = Column(Integer, primary_key=True, index=True)
    relay_key = Column(String, unique=True, nullable=False)  # valve1, valve2, ...
    name = Column(String, nullable=False)  # Название реле: "Насос", "Розетка"
    status = Column(Boolean, default=False)  # Включено или выключено