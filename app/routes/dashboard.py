# app/routes/dashboard.py

from flask import request, redirect, url_for, flash, render_template, Blueprint
from datetime import datetime

from app.db.database import SessionLocal
from app.logs.logger_helper import log_event
from app.scheduler import load_schedules_from_db
from app.db.models import RelayTarget, Schedule

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    session = SessionLocal()
    schedules = session.query(Schedule).all()
    session.close()

    # локализуем дни недели
    day_map = {'Mon': 'пн', 'Tue': 'вт', 'Wed': 'ср', 'Thu': 'чт', 'Fri': 'пт', 'Sat': 'сб', 'Sun': 'вс'}
    for s in schedules:
        s.days = ", ".join([day_map.get(day.strip(), day) for day in s.days.split(",")])

    return render_template("dashboard.html", schedules=schedules)

@dashboard_bp.route("/add", methods=["GET", "POST"])
def add_schedule():
    if request.method == "POST":
        target = request.form.get("target")
        selected_days = request.form.getlist("days")
        days = ",".join(selected_days)
        hour_on = int(request.form.get("hour_on"))
        minute_on = int(request.form.get("minute_on"))
        time_on = datetime.strptime(f"{hour_on:02d}:{minute_on:02d}", "%H:%M").time()

        duration_hour = int(request.form.get("duration_hour", 0))
        duration_minute = int(request.form.get("duration_minute", 0))
        duration_min = duration_hour * 60 + duration_minute
        enabled = request.form.get("enabled") == "on"

        try:
            session = SessionLocal()
            new_task = Schedule(
                target=RelayTarget(target),
                days=days,
                time_on=time_on,
                duration_min=duration_min,
                enabled=enabled
            )
            session.add(new_task)
            session.commit()
            session.close()

            log_event("INFO", f"Добавлено расписание: {target} {days} {time_on}", target=target, action="ADD_TASK")
            load_schedules_from_db()
            flash("Задача успешно добавлена", "success")
            return redirect(url_for("dashboard.dashboard"))
        except Exception as e:
            flash("Ошибка при добавлении задачи", "danger")
            log_event("ERROR", f"Ошибка при сохранении задачи: {e}", action="ADD_FAIL")

    return render_template("schedule_form.html", targets=RelayTarget)

@dashboard_bp.route("/edit/<int:schedule_id>", methods=["GET", "POST"])
def edit_schedule(schedule_id):
    session = SessionLocal()
    schedule = session.query(Schedule).filter_by(id=schedule_id).first()

    if not schedule:
        session.close()
        flash("Задача не найдена", "warning")
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        try:
            schedule.target = RelayTarget(request.form.get("target"))

            selected_days = request.form.getlist("days")
            schedule.days = ",".join(selected_days)

            hour_on = int(request.form.get("hour_on"))
            minute_on = int(request.form.get("minute_on"))
            schedule.time_on = datetime.strptime(f"{hour_on:02d}:{minute_on:02d}", "%H:%M").time()

            duration_hour = int(request.form.get("duration_hour", 0))
            duration_minute = int(request.form.get("duration_minute", 0))
            schedule.duration_min = duration_hour * 60 + duration_minute

            schedule.enabled = request.form.get("enabled") == "on"

            session.commit()
            log_event("INFO", f"Расписание {schedule_id} обновлено", target=schedule.target.value, action="EDIT_TASK")
            load_schedules_from_db()
            flash("Задача обновлена", "success")
            return redirect(url_for("dashboard.dashboard"))
        except Exception as e:
            flash("Ошибка при обновлении задачи", "danger")
            log_event("ERROR", f"Ошибка при обновлении задачи {schedule_id}: {e}", action="EDIT_FAIL")
        finally:
            session.close()

    # передаём данные для формы
    days_selected = schedule.days.split(",") if schedule.days else []
    hour_on = schedule.time_on.hour
    minute_on = schedule.time_on.minute
    duration_hour = schedule.duration_min // 60
    duration_minute = schedule.duration_min % 60

    session.close()
    return render_template(
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
def delete_schedule(schedule_id):
    session = SessionLocal()
    schedule = session.query(Schedule).filter_by(id=schedule_id).first()
    if schedule:
        log_event("INFO", f"Удалено расписание ID={schedule.id}", target=schedule.target.value, action="DELETE_TASK")
        session.delete(schedule)
        session.commit()
    session.close()
    load_schedules_from_db()
    flash("Задача удалена", "info")
    return redirect(url_for("dashboard.dashboard"))
