# app/routes/logs.py

from quart import Blueprint, render_template, request
from sqlalchemy import select, desc
from app.db.database import AsyncSessionLocal
from app.db.models import Log

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/logs")
async def logs():
    # Получаем фильтры из запроса
    level = request.args.get("level")
    action = request.args.get("action")
    target = request.args.get("target")

    async with AsyncSessionLocal() as session:
        stmt = select(Log)

        if level:
            stmt = stmt.where(Log.level == level)
        if action:
            stmt = stmt.where(Log.action == action)
        if target:
            stmt = stmt.where(Log.target == target)

        stmt = stmt.order_by(desc(Log.timestamp)).limit(100)

        result = await session.execute(stmt)
        logs = result.scalars().all()

    return await render_template("logs.html", logs=logs)
