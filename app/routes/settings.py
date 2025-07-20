# app/routes/settings.py

from quart import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.db.models import RelayName
from app.logs.logger_helper import log_event

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET", "POST"])
async def settings():
    async with AsyncSessionLocal() as session:
        if request.method == "POST":
            form = await request.form
            for relay_id in range(1, 5):
                new_name = form.get(f"name_{relay_id}")
                result = await session.execute(select(RelayName).where(RelayName.id == relay_id))
                relay = result.scalar()
                if relay:
                    relay.name = new_name
                else:
                    session.add(RelayName(id=relay_id, name=new_name))
            await session.commit()
            await flash("Названия реле обновлены", "success")
            await log_event("INFO", "Названия реле обновлены", action="SETTINGS_UPDATE")
            return redirect(url_for("settings.settings"))

        result = await session.execute(select(RelayName))
        relay_names = {r.id: r.name for r in result.scalars().all()}
        return await render_template("settings.html", relay_names=relay_names)
