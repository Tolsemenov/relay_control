# app/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.db.models import Schedule, RelayTarget
from app.gpio.relay_controller import RelayController
from app.logs.logger_helper import log_event

controller = RelayController()
scheduler = BackgroundScheduler()

def schedule_task(schedule: Schedule):
    """Создаёт задачу в планировщике по записи из БД"""

    def task_on():
        controller.turn_on(schedule.target)
        log_event(
            "INFO",
            f"Реле {schedule.target.value} включено по расписанию (id={schedule.id})",
            target=schedule.target,
            action="SCHEDULE_ON"
        )

        # Планируем выключение через N минут
        scheduler.add_job(
            lambda: task_off(),
            trigger='date',
            run_date=datetime.now() + timedelta(minutes=schedule.duration_min),
            id=f"off_{schedule.id}",
            replace_existing=True
        )

    def task_off():
        controller.turn_off(schedule.target)
        log_event(
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

    scheduler.add_job(
        func=task_on,
        trigger=trigger,
        id=str(schedule.id),
        replace_existing=True
    )

def load_schedules_from_db():
    """Загружает все активные расписания и регистрирует их в APScheduler"""
    session = SessionLocal()
    schedules = session.query(Schedule).filter_by(enabled=True).all()
    session.close()

    for sched in schedules:
        try:
            schedule_task(sched)
        except Exception as e:
            log_event("ERROR", f"Ошибка при регистрации задачи {sched.id}: {e}", target=sched.target)

def start_scheduler():
    """Запускает планировщик"""
    load_schedules_from_db()
    scheduler.start()
    log_event("INFO", "Планировщик задач запущен", action="SCHEDULER_START")
