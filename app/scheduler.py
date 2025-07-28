from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import asyncio

from app.db.database import AsyncSessionLocal
from app.db.models import Schedule, RelayTarget
from app.gpio.relay_controller import RelayController
from app.gpio.relay_state_manager import RelayStateManager
from app.logs.logger_helper import log_event

controller = RelayController()
scheduler = AsyncIOScheduler()

def schedule_task(schedule: Schedule):
    """Создаёт задачу в планировщике по записи из БД"""

    async def task_on():
        print(f"[SCHEDULER] ⏰ Включение реле по задаче ID={schedule.id}")
        await log_event("DEBUG", f"Запуск включения реле {schedule.target.value}", target=schedule.target, action="SCHEDULE_DEBUG_ON")

        await RelayStateManager.set_status(schedule.target.value, True, source="SCHEDULE")
        await log_event("INFO", f"Реле {schedule.target.value} включено (ID={schedule.id})", target=schedule.target, action="SCHEDULE_ON")

        # Планируем выключение через N минут
        off_time = datetime.now() + timedelta(minutes=schedule.duration_min)
        print(f"[SCHEDULER] ⏲ Планируем выключение ID={schedule.id} в {off_time}")
        scheduler.add_job(
            func=task_off,
            trigger='date',
            run_date=off_time,
            id=f"off_{schedule.id}",
            replace_existing=True
        )

    async def task_off():
        print(f"[SCHEDULER] ⏰ Выключение реле по задаче ID={schedule.id}")
        await log_event("DEBUG", f"Запуск выключения реле {schedule.target.value}", target=schedule.target, action="SCHEDULE_DEBUG_OFF")

        # 💡 Правильно: централизованное отключение с обновлением базы и WebSocket
        await RelayStateManager.set_status(schedule.target.value, False, source="SCHEDULE")
        await log_event("INFO", f"Реле {schedule.target.value} выключено (ID={schedule.id})", target=schedule.target, action="SCHEDULE_OFF")

    # Преобразуем дни недели
    day_map = {
        "Mon": "mon", "Tue": "tue", "Wed": "wed", "Thu": "thu",
        "Fri": "fri", "Sat": "sat", "Sun": "sun"
    }
    days = [day_map[d.strip()] for d in schedule.days.split(",") if d.strip() in day_map]

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


async def load_schedules_from_db():
    """Загружает все активные расписания и регистрирует их в APScheduler"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Schedule.__table__.select().where(Schedule.enabled == True)
        )
        rows = result.fetchall()
        for row in rows:
            try:
                sched = Schedule(**row._mapping)
                schedule_task(sched)
            except Exception as e:
                print(f"[ERROR] ❌ Ошибка регистрации задачи ID={row.id}: {e}")
                await log_event("ERROR", f"Ошибка при регистрации задачи {row.id}: {e}", target=row.target)

async def start_scheduler():
    """Запускает планировщик"""
    await load_schedules_from_db()
    scheduler.start()
    print("[SCHEDULER] ✅ Планировщик задач запущен")
    await log_event("INFO", "Планировщик задач запущен", action="SCHEDULER_START")
