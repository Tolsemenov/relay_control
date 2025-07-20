# app/db/database.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect
from app.db.models import Base
from app.logs.logger_helper import log_event

DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "autowater.db")
DB_URI = f"sqlite+aiosqlite:///{DB_PATH}"

# Создаём асинхронный движок и сессию
engine: AsyncEngine = create_async_engine(DB_URI, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db():
    """Асинхронно инициализирует БД и таблицы."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    db_created = False

    if not os.path.exists(DB_PATH):
        print("[DB] База данных не найдена. Создаю...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        db_created = True
        print("[DB] База данных создана:", DB_PATH)
        await log_event("INFO", f"Создана новая база данных по пути: {DB_PATH}", action="DB_INIT")
    else:
        try:
            # Проверка таблиц (используем sync-инспектор через run_sync)
            async with engine.connect() as conn:
                def check_tables(sync_conn):
                    inspector = inspect(sync_conn)
                    existing_tables = set(inspector.get_table_names())
                    return existing_tables

                existing_tables = await conn.run_sync(check_tables)
                required_tables = {"schedule", "logs"}
                missing_tables = required_tables - existing_tables

                if missing_tables:
                    await conn.run_sync(Base.metadata.create_all)
                    await log_event("WARNING", f"Созданы отсутствующие таблицы: {', '.join(missing_tables)}", action="DB_FIX")
                else:
                    await log_event("INFO", f"База данных найдена. Все таблицы в порядке.", action="DB_OK")

            print("[DB] База данных найдена:", DB_PATH)

        except SQLAlchemyError as e:
            print("[DB] Ошибка при проверке таблиц:", e)
            await log_event("ERROR", f"Ошибка при инициализации БД: {e}", action="DB_ERROR")
