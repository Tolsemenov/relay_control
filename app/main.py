import asyncio
from quart import Quart, session, redirect, url_for, request

from app.db.database import init_db
from app.logs.logger_helper import log_event
from app.routes.logs import logs_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.scheduler import start_scheduler
from app.wifi_setup.wifi_manager import is_wifi_connected, stop_access_point, start_access_point, run_flask_web

app = Quart(__name__)
app.config['SECRET_KEY'] = 'замени_на_случайный_ключ'

# Регистрация blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(logs_bp)


@app.before_request
def require_login():
    if not session.get("logged_in") and not request.path.startswith("/login"):
        return redirect(url_for("auth.login"))


@app.route("/")
def home():
    return redirect(url_for("dashboard.dashboard"))


async def start_main_web_server():
    """
    Асинхронная инициализация БД и запуск Flask-приложения.
    """
    await init_db()
    await log_event("INFO", "Сервер стартует", action="APP_START")
    await start_scheduler()

    # Flask работает синхронно → запуск отдельно
    app.run(host="0.0.0.0", port=5000)


async def main():
    if is_wifi_connected():
        print("✅ Wi-Fi подключён")
        stop_access_point()
        await start_main_web_server()
    else:
        print("❌ Wi-Fi не подключён. Поднимаем точку доступа для настройки...")
        start_access_point()
        run_flask_web()  # отдельный Flask на порту 80 (может быть sync)


if __name__ == "__main__":
    asyncio.run(main())
