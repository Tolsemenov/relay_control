# app/routes/dashboard.py

from quart import request, redirect, url_for, flash, render_template, Blueprint
from datetime import datetime

from app.db.database import AsyncSessionLocal
from app.logs.logger_helper import log_event
from app.scheduler import load_schedules_from_db
from app.db.models import Schedule, RelayName, RelayTarget
from sqlalchemy.future import select

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
async def dashboard():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Schedule))
        schedules = result.scalars().all()

        relay_result = await session.execute(select(RelayName))
        relay_records = relay_result.scalars().all()
        relay_names = {r.relay_key: r.name for r in relay_records}
        relays = {r.relay_key: r for r in relay_records}

    day_map = {'Mon': 'пн', 'Tue': 'Вт', 'Wed': 'ср', 'Thu': 'чт', 'Fri': 'пт', 'Sat': 'сб', 'Sun': 'вс'}
    for s in schedules:
        s.days = ", ".join([day_map.get(day.strip(), day) for day in s.days.split(",")])

    return await render_template("dashboard.html", schedules=schedules, relay_names=relay_names, relays=relays)

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

            await load_schedules_from_db()
            await flash("Задача успешно добавлена", "success")
            return redirect(url_for("dashboard.dashboard"))

        except Exception as e:
            await flash("Ошибка при добавлении задачи", "danger")
            await log_event("ERROR", f"Ошибка при сохранении задачи: {e}", action="ADD_FAIL")

    # GET-запрос — загружаем имена реле
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RelayName))
        relay_names = {r.relay_key: r.name for r in result.scalars()}

    return await render_template("schedule_form.html", targets=RelayTarget, relay_names=relay_names)


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
                await load_schedules_from_db()
                await flash("Задача обновлена", "success")
                return redirect(url_for("dashboard.dashboard"))

            except Exception as e:
                await flash("Ошибка при обновлении задачи", "danger")
                await log_event("ERROR", f"Ошибка при обновлении задачи {schedule_id}: {e}", action="EDIT_FAIL")

        # 🧠 Для GET-запроса — подготовка формы
        days_selected = schedule.days.split(",") if schedule.days else []
        hour_on = schedule.time_on.hour
        minute_on = schedule.time_on.minute
        duration_hour = schedule.duration_min // 60
        duration_minute = schedule.duration_min % 60

        # ✅ Получаем пользовательские названия реле
        result = await session.execute(select(RelayName))
        relay_names = {r.relay_key: r.name for r in result.scalars()}

        return await render_template(
            "schedule_form.html",
            schedule=schedule,
            targets=RelayTarget,
            relay_names=relay_names,
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

    await load_schedules_from_db()
    await flash("Задача удалена", "info")
    return redirect(url_for("dashboard.dashboard"))

@dashboard_bp.route("/toggle_relay/<string:relay_key>", methods=["POST"])
async def toggle_relay(relay_key):
    if relay_key not in [r.value for r in RelayTarget]:
        await flash(f"Недопустимый ключ реле: {relay_key}", "danger")
        return redirect(url_for("dashboard.dashboard"))
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RelayName).where(RelayName.relay_key == relay_key))
        relay = result.scalar()

        if not relay:
            await flash(f"Реле '{relay_key}' не найдено", "danger")
            return redirect(url_for("dashboard.dashboard"))

        # Переключаем статус
        relay.status = not relay.status
        await session.commit()

        state = "включено" if relay.status else "выключено"
        await log_event("INFO", f"Реле '{relay.name}' вручную {state}", target=relay_key, action="MANUAL_SWITCH")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/settings", methods=["GET", "POST"])
async def settings():
    async with AsyncSessionLocal() as session:
        if request.method == "POST":
            form = await request.form
            for relay_key in RelayTarget.__members__:
                new_name = form.get(relay_key)
                result = await session.execute(
                    select(RelayName).where(RelayName.relay_key == relay_key)
                )
                record = result.scalar()
                if record:
                    record.name = new_name
                else:
                    session.add(RelayName(relay_key=relay_key, name=new_name))
            await session.commit()
            await flash("Названия реле обновлены", "success")
            return redirect(url_for("dashboard.settings"))

        # Для GET-запроса
        result = await session.execute(select(RelayName))
        names = {r.relay_key: r.name for r in result.scalars()}
        return await render_template("settings.html", names=names, targets=RelayTarget)


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