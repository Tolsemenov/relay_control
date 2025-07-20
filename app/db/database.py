# app/db/database.py
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.logs.logger_helper import log_event

DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "autowater.db")
DB_URI = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URI, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Создание базы данных и таблиц, если они отсутствуют."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    db_created = False

    if not os.path.exists(DB_PATH):
        print("[DB] База данных не найдена. Создаю...")
        Base.metadata.create_all(bind=engine)
        db_created = True
        print("[DB] База данных создана:", DB_PATH)
        log_event("INFO", f"Создана новая база данных по пути: {DB_PATH}", action="DB_INIT")
    else:
        # Проверим наличие таблиц
        inspector = inspect(engine)
        required_tables = {"schedule", "logs"}

        existing_tables = set(inspector.get_table_names())

        missing_tables = required_tables - existing_tables

        if missing_tables:
            Base.metadata.create_all(bind=engine)
            log_event("WARNING", f"Созданы отсутствующие таблицы: {', '.join(missing_tables)}", action="DB_FIX")
        else:
            log_event("INFO", f"База данных найдена. Все таблицы в порядке.", action="DB_OK")

        print("[DB] База данных найдена:", DB_PATH)
