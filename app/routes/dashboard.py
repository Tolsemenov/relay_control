# app/routes/dashboard.py

from quart import request, redirect, url_for, flash, render_template, Blueprint
from datetime import datetime

from app.db.database import AsyncSessionLocal
from app.logs.logger_helper import log_event
from app.scheduler import load_schedules_from_db
from app.db.models import RelayTarget, Schedule
from sqlalchemy.future import select

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
async def dashboard():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Schedule))
        schedules = result.scalars().all()

    day_map = {'Mon': 'пн', 'Tue': 'вт', 'Wed': 'ср', 'Thu': 'чт', 'Fri': 'пт', 'Sat': 'сб', 'Sun': 'вс'}
    for s in schedules:
        s.days = ", ".join([day_map.get(day.strip(), day) for day in s.days.split(",")])

    return await render_template("dashboard.html", schedules=schedules)

@dashboard_bp.route("/add", methods=["GET", "POST"])
async def add_schedule():
    if request.method == "POST":
        form = await request.form
        target = form.get("target")
        selected_days = form.getlist("days")
        days = ",".join(selected_days)
        hour_on = int(form.get("hour_on"))
        minute_on = int(form.get("minute_on"))
        time_on = datetime.strptime(f"{hour_on:02d}:{minute_on:02d}", "%H:%M").time()

        duration_hour = int(form.get("duration_hour", 0))
        duration_minute = int(form.get("duration_minute", 0))
        duration_min = duration_hour * 60 + duration_minute
        enabled = form.get("enabled") == "on"

        try:
            async with AsyncSessionLocal() as session:
                new_task = Schedule(
                    target=RelayTarget(target),
                    days=days,
                    time_on=time_on,
                    duration_min=duration_min,
                    enabled=enabled
                )
                session.add(new_task)
                await session.commit()

            await log_event("INFO", f"Добавлено расписание: {target} {days} {time_on}", target=target, action="ADD_TASK")
            load_schedules_from_db()
            await flash("Задача успешно добавлена", "success")
            return redirect(url_for("dashboard.dashboard"))

        except Exception as e:
            await flash("Ошибка при добавлении задачи", "danger")
            await log_event("ERROR", f"Ошибка при сохранении задачи: {e}", action="ADD_FAIL")

    return await render_template("schedule_form.html", targets=RelayTarget)

@dashboard_bp.route("/edit/<int:schedule_id>", methods=["GET", "POST"])
async def edit_schedule(schedule_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
        schedule = result.scalar()

        if not schedule:
            await flash("Задача не найдена", "warning")
            return redirect(url_for("dashboard.dashboard"))

        if request.method == "POST":
            form = await request.form
            try:
                schedule.target = RelayTarget(form.get("target"))
                selected_days = form.getlist("days")
                schedule.days = ",".join(selected_days)

                hour_on = int(form.get("hour_on"))
                minute_on = int(form.get("minute_on"))
                schedule.time_on = datetime.strptime(f"{hour_on:02d}:{minute_on:02d}", "%H:%M").time()

                duration_hour = int(form.get("duration_hour", 0))
                duration_minute = int(form.get("duration_minute", 0))
                schedule.duration_min = duration_hour * 60 + duration_minute

                schedule.enabled = form.get("enabled") == "on"

                await session.commit()
                await log_event("INFO", f"Расписание {schedule_id} обновлено", target=schedule.target.value, action="EDIT_TASK")
                load_schedules_from_db()
                await flash("Задача обновлена", "success")
                return redirect(url_for("dashboard.dashboard"))

            except Exception as e:
                await flash("Ошибка при обновлении задачи", "danger")
                await log_event("ERROR", f"Ошибка при обновлении задачи {schedule_id}: {e}", action="EDIT_FAIL")

    # Для GET-запроса — подготовка формы
    days_selected = schedule.days.split(",") if schedule.days else []
    hour_on = schedule.time_on.hour
    minute_on = schedule.time_on.minute
    duration_hour = schedule.duration_min // 60
    duration_minute = schedule.duration_min % 60

    return await render_template(
        "schedule_form.html",
        schedule=schedule,
        targets=RelayTarget,
        days_selected=days_selected,
        hour_on=hour_on,
        minute_on=minute_on,
        duration_hour=duration_hour,
        duration_minute=duration_minute
    )

@dashboard_bp.route("/delete/<int:schedule_id>")
async def delete_schedule(schedule_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
        schedule = result.scalar()
        if schedule:
            await log_event("INFO", f"Удалено расписание ID={schedule.id}", target=schedule.target.value, action="DELETE_TASK")
            await session.delete(schedule)
            await session.commit()

    load_schedules_from_db()
    await flash("Задача удалена", "info")
    return redirect(url_for("dashboard.dashboard"))

@dashboard_bp.route("/toggle_schedule/<int:schedule_id>")
async def toggle_schedule(schedule_id):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
        schedule = result.scalar()

        if schedule:
            schedule.enabled = not schedule.enabled
            await session.commit()

            action = "TASK_ENABLED" if schedule.enabled else "TASK_DISABLED"
            status = "включено" if schedule.enabled else "отключено"
            await log_event("INFO", f"Расписание ID={schedule.id} {status}", target=schedule.target.value, action=action)

    await load_schedules_from_db()
    return redirect(url_for("dashboard.dashboard"))