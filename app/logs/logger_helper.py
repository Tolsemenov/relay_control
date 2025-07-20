# app/logs/logger_helper.py

import os
from datetime import datetime
from app.db.models import Log

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Пути к БД и логам
DB_PATH = os.path.join("db", "autowater.db")
DB_URI = f"sqlite+aiosqlite:///{DB_PATH}"

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

general_log_path = os.path.join(LOG_DIR, "autowater.log")
error_log_path = os.path.join(LOG_DIR, "error.log")

# Создаём асинхронный engine и sessionmaker
engine = create_async_engine(DB_URI, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def log_event(level: str, message: str, action: str = "", target: str = None):
    timestamp = datetime.now()

    # 1. Записываем в файл
    log_line = f"[{timestamp:%Y-%m-%d %H:%M:%S}] [{level.upper()}] autowater: {message}\n"
    try:
        with open(general_log_path, "a", encoding="utf-8") as f:
            f.write(log_line)

        if level.upper() == "ERROR":
            with open(error_log_path, "a", encoding="utf-8") as ef:
                ef.write(log_line)
    except Exception as file_err:
        print(f"[WARNING] Ошибка записи в лог-файл: {file_err}")

    # 2. Записываем в БД
    try:
        async with AsyncSessionLocal() as session:
            log = Log(
                target=target,
                level=level.upper(),
                action=action,
                message=message,
                timestamp=timestamp
            )
            session.add(log)
            await session.commit()
    except SQLAlchemyError as db_err:
        print(f"[ERROR] Ошибка записи лога в БД: {db_err}")
