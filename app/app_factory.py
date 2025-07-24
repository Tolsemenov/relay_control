# app/app_factory.py
import os
from pathlib import Path

from quart import Quart, session, redirect, url_for, request
#from quart_session import Session
from datetime import timedelta
from dotenv import load_dotenv

from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.logs import logs_bp
from app.routes.settings import settings_bp

load_dotenv()

def create_main_app():
    app = Quart(__name__)

    BASE_DIR = Path(__file__).resolve().parent.parent
    SESSION_DIR = os.path.join(BASE_DIR, ".quart_session")
    os.makedirs(SESSION_DIR, exist_ok=True)  # Создаём, если не существует

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = SESSION_DIR
    app.config["SESSION_PERMANENT"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=100)

    #Session(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(settings_bp)

    @app.before_request
    async def require_login():
        if not session.get("logged_in") and not request.path.startswith("/login"):
            return redirect(url_for("auth.login"))

    @app.route("/")
    async def home():
        return redirect(url_for("dashboard.dashboard"))

    return app
