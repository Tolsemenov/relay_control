# app/logs/logger_helper.py

import os
from datetime import datetime
from app.db.models import Log

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError



# Указываем URI БД вручную — чтобы избежать импорта из database.py
DB_PATH = os.path.join("db", "autowater.db")
DB_URI = f"sqlite:///{DB_PATH}"

# Пути к лог-файлам
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

general_log_path = os.path.join(LOG_DIR, "autowater.log")
error_log_path = os.path.join(LOG_DIR, "error.log")


def log_event(level: str, message: str, action: str = "", target: str = None):
    timestamp = datetime.now()

    # 1. Лог в файл
    log_line = f"[{timestamp:%Y-%m-%d %H:%M:%S}] [{level.upper()}] autowater: {message}\n"
    with open(general_log_path, "a", encoding="utf-8") as f:
        f.write(log_line)

    if level.upper() == "ERROR":
        with open(error_log_path, "a", encoding="utf-8") as ef:
            ef.write(log_line)

    # 2. Лог в базу данных (локальный engine/sessionmaker)
    try:
        engine = create_engine(DB_URI, echo=False, future=True)
        SessionLocal = sessionmaker(bind=engine)
        with SessionLocal() as session:
            log = Log(
                target=target,
                level=level.upper(),
                action=action,
                message=message,
                timestamp=timestamp
            )
            session.add(log)
            session.commit()
    except SQLAlchemyError as e:
        print(f"[ERROR] Ошибка записи лога в БД: {e}")
