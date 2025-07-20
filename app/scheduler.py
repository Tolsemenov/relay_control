# app/scheduler.py

import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

from app.db.database import AsyncSessionLocal
from app.db.models import Schedule, RelayTarget
from app.gpio.relay_controller import RelayController
from app.logs.logger_helper import log_event

controller = RelayController()
scheduler = BackgroundScheduler()

def schedule_task(schedule: Schedule):
    """Создаёт задачу в планировщике по записи из БД"""

    async def task_on():
        await controller.turn_on(schedule.target)
        await log_event(
            "INFO",
            f"Реле {schedule.target.value} включено по расписанию (id={schedule.id})",
            target=schedule.target,
            action="SCHEDULE_ON"
        )

        # Планируем выключение через N минут
        scheduler.add_job(
            lambda: asyncio.create_task(task_off()),
            trigger='date',
            run_date=datetime.now() + timedelta(minutes=schedule.duration_min),
            id=f"off_{schedule.id}",
            replace_existing=True
        )

    async def task_off():
        await controller.turn_off(schedule.target)
        await log_event(
            "INFO",
            f"Реле {schedule.target.value} выключено автоматически (id={schedule.id})",
            target=schedule.target,
            action="SCHEDULE_OFF"
        )

    # Преобразуем дни недели
    day_map = {
        "Mon": "mon", "Tue": "tue", "Wed": "wed", "Thu": "thu",
        "Fri": "fri", "Sat": "sat", "Sun": "sun"
    }
    days = [day_map[d] for d in schedule.days.split(",") if d in day_map]

    # Настраиваем крон-триггер
    trigger = CronTrigger(
        day_of_week=",".join(days),
        hour=schedule.time_on.hour,
        minute=schedule.time_on.minute
    )

    # Добавляем задачу в планировщик как асинхронную
    scheduler.add_job(
        func=lambda: asyncio.create_task(task_on()),
        trigger=trigger,
        id=str(schedule.id),
        replace_existing=True
    )

async def load_schedules_from_db():
    """Загружает все активные расписания и регистрирует их в APScheduler"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Schedule.__table__.select().where(Schedule.enabled == True)
        )
        rows = result.fetchall()
        for row in rows:
            try:
                # Преобразуем в объект Schedule вручную (или используй ORM если нужно)
                sched = Schedule(**row._mapping)
                schedule_task(sched)
            except Exception as e:
                await log_event("ERROR", f"Ошибка при регистрации задачи {row.id}: {e}", target=row.target)

async def start_scheduler():
    """Запускает планировщик"""
    await load_schedules_from_db()
    scheduler.start()
    await log_event("INFO", "Планировщик задач запущен", action="SCHEDULER_START")
