# app/wifi_setup/wifi_manager.py

import asyncio
import os
import subprocess
import platform
from app.logs.logger_helper import log_event

IS_WINDOWS = platform.system() == "Windows"


def is_wifi_connected():
    result = os.system("ping -c 1 8.8.8.8 >nul 2>&1" if IS_WINDOWS else "ping -c 1 8.8.8.8 > /dev/null 2>&1")
    return result == 0


def log_async(level: str, message: str, action: str = "", target: str = None):
    """Безопасная обёртка для вызова асинхронного логирования из синхронного кода"""
    try:
        asyncio.run(log_event(level, message, action, target))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(log_event(level, message, action, target))


def start_access_point():
    if IS_WINDOWS:
        print("⚠️ Не могу запустить AP на Windows")
        log_async("WARNING", "Попытка запуска точки доступа на Windows", action="WIFI_AP_SKIP")
        return
    subprocess.call(['sudo', 'bash', 'setup_ap.sh'])


def stop_access_point():
    if IS_WINDOWS:
        return
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])


def run_flask_web():
    if IS_WINDOWS:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # app/wifi_setup
        path = os.path.join(base_dir, "web_server.py")
        cmd = ['python', path]
    else:
        cmd = ['sudo', 'python3', 'web_server.py']
    subprocess.call(cmd)
