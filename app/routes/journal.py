from datetime import date, datetime, timedelta
from sqlalchemy import not_

from quart import render_template, Blueprint, request
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Log

journal_bp = Blueprint("journal", __name__)

excluded_actions = ["DB_INIT", "SCHEDULER_START", "NET_INFO", "DB_OK"]

# Мапа дней недели на русском
DAY_NAMES = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье",
}

@journal_bp.route("/journal", methods=["GET"])
async def journal():
    selected_date = request.args.get("date")  # "2025-07-27"
    if selected_date:
        current = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        current = date.today()

    start = datetime.combine(current, datetime.min.time())
    end = datetime.combine(current, datetime.max.time())

    prev_date = (current - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (current + timedelta(days=1)).strftime("%Y-%m-%d")

    # Форматирование даты + русское имя дня
    weekday = DAY_NAMES[current.weekday()]
    display_date = f"{current.strftime('%d.%m.%Y')} ({weekday})"

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Log)
            .where(
                Log.timestamp.between(start, end),
                not_(Log.action.in_(excluded_actions))
            )
            .order_by(Log.timestamp.desc())
        )
        logs = result.scalars().all()

    return await render_template(
        "journal.html",
        logs=logs,
        selected_date=current.strftime("%Y-%m-%d"),
        display_date=display_date,
        prev_date=prev_date,
        next_date=next_date
    )
