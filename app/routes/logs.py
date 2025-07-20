# app/routes/logs.py

from flask import Blueprint, render_template, request
from app.db.database import SessionLocal
from app.db.models import Log
from sqlalchemy import desc

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs")
def logs():
    session = SessionLocal()

    # Фильтрация по уровню, действию и цели (если переданы в URL)
    level = request.args.get("level")
    action = request.args.get("action")
    target = request.args.get("target")

    query = session.query(Log)

    if level:
        query = query.filter(Log.level == level)
    if action:
        query = query.filter(Log.action == action)
    if target:
        query = query.filter(Log.target == target)

    logs = query.order_by(desc(Log.timestamp)).limit(100).all()
    session.close()

    return render_template("logs.html", logs=logs)
