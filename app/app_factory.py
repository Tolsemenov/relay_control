# app/app_factory.py

from flask import Flask, session, redirect, url_for, request
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.logs import logs_bp

def create_main_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'замени_на_секретный_ключ'

    # Роуты
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

    return app
