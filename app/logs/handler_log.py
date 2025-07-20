# logs/handler_log.py
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.dirname(os.path.abspath(__file__))

APP_LOG = os.path.join(LOG_DIR, "app.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")

# Ограничения:
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 МБ
BACKUP_COUNT = 3  # Сколько копий хранить: app.log.1, app.log.2 и т.д.

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # INFO лог (ротация)
    app_handler = RotatingFileHandler(APP_LOG, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding='utf-8')
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    # ERROR лог (ротация)
    error_handler = RotatingFileHandler(ERROR_LOG, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Консоль (опционально)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Чтобы не дублировать обработчики
    if not logger.handlers:
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

    return logger
