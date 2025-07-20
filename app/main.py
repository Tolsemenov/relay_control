

from flask import Flask, session, redirect, url_for, request
from app.db.database import init_db
from app.logs.logger_helper import log_event
from app.routes.logs import logs_bp
from app.scheduler import start_scheduler
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'замени_на_случайный_ключ'

# Blueprints  before_request
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(logs_bp)


@app.before_request
def require_login():
    if not session.get("logged_in") and not request.path.startswith("/login"):
        return redirect(url_for("auth.login"))

@app.route("/")
def home():
    return redirect(url_for("dashboard.dashboard"))  # позже создадим dashboard

def main():
    init_db()
    log_event("INFO", "Сервер стартует", action="APP_START")
    start_scheduler()
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
