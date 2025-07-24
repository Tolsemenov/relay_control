# app/routes/auth.py
import os
from quart import Blueprint, render_template, request, redirect, url_for, session
# from dotenv import load_dotenv
#
# load_dotenv()

auth_bp = Blueprint("auth", __name__)

USERNAME = os.getenv("APP_USERNAME", "admin")
PASSWORD = os.getenv("APP_PASSWORD", "1234")
# # Можно заменить на загрузку из .env
# USERNAME = "admin"
# PASSWORD = "1234"

@auth_bp.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        password = form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            #session.permanent = True
            return redirect(url_for("dashboard.dashboard"))
        else:
            return await render_template("login.html", error="Неверный логин или пароль")

    return await render_template("login.html")


@auth_bp.route("/logout")
async def logout():
    session.clear()
    return redirect(url_for("auth.login"))
