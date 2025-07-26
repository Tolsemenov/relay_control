# app/main.py

import asyncio
import platform

from hypercorn.asyncio import serve
from hypercorn.config import Config

from app.db.database import init_db
from app.logs.logger_helper import log_event
from app.network.get_local_ip import get_local_ip
from app.network.monitor import internet_monitor
from app.scheduler import start_scheduler
from app.app_factory import create_main_app
from app.wifi_setup.button_listener import start_button_listener
from app.wifi_setup.wifi_manager import is_wifi_connected, start_access_point, run_flask_web


IS_WINDOWS = platform.system() == "Windows"

async def start_main_web_server():
    app = create_main_app()
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    await serve(app, config)

async def main():
    await init_db()
    await log_event("INFO", "Сервер стартует", action="APP_START")
    start_button_listener()
    await start_scheduler()

    # ✅ Запускаем отслеживание интернета
    asyncio.create_task(internet_monitor())

    ip = get_local_ip()
    print(f"[NET] IP-адрес устройства: {ip}")
    await log_event("INFO", f"IP-адрес устройства: {ip}", action="NET_INFO")

    if not is_wifi_connected() and not IS_WINDOWS:
        print("❌ Wi-Fi не подключён. Поднимаем точку доступа для настройки...")
        await start_access_point()
        await run_flask_web()  # порт 80
    else:
        print("✅ Wi-Fi подключён. Запускаем основное веб-приложение...")
        await start_main_web_server()

if __name__ == "__main__":
    asyncio.run(main())
