# app/main_simple.py

import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from app.app_factory import create_main_app

async def main():
    app = create_main_app()

    config = Config()
    config.bind = ["0.0.0.0:5000"]

    print("🌐 Пробуем запустить веб-сервер на http://127.0.0.1:5000 ...")
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())