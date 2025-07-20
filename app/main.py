import asyncio
from app.db.database import init_db
from app.wifi_setup.button_listener import start_button_listener
from app.wifi_setup.web_server import app

from app.wifi_setup.wifi_manager import is_wifi_connected, start_access_point, run_flask_web

from hypercorn.asyncio import serve
from hypercorn.config import Config




async def start_main_web_server():
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    await serve(app, config)


async def main():

    await init_db()
    start_button_listener()

    # if not is_wifi_connected():
    #     print("❌ Wi-Fi не подключён. Поднимаем точку доступа для настройки...")
    #     await start_access_point()
    #     await run_flask_web()  # Flask-сервер на порту 80
    # else:
    #     await start_main_web_server()  # Quart-сервер на порту 5000
    await start_main_web_server()  # Quart-сервер на порту 5000

if __name__ == "__main__":
    asyncio.run(main())
