# app/wifi_setup/button_listener.py

from app.logs.logger_helper import log_event

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    print("⚠️ GPIO недоступен (не Raspberry Pi / Orange Pi?). Работа кнопки отключена.")
    GPIO_AVAILABLE = False

import time
import threading
import asyncio

from app.wifi_setup.wifi_manager import (
    is_wifi_connected,
    start_access_point,
    run_flask_web
)

BUTTON_PIN = 17              # Пин, к которому подключена кнопка
HOLD_SECONDS = 3             # Время удержания для активации (в секундах)
CHECK_CLIENTS_EVERY = 10     # Не используется в этой версии
TIMEOUT_NO_CLIENTS = 300     # Не используется в этой версии

def monitor_button():
    if not GPIO_AVAILABLE:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("[INFO] Мониторинг кнопки запущен (pin {})".format(BUTTON_PIN))

    try:
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                press_time = time.time()
                print("[DEBUG] Кнопка нажата")
                while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                    time.sleep(0.1)
                release_time = time.time()
                duration = release_time - press_time

                if duration >= HOLD_SECONDS:
                    print("[INFO] Кнопка удерживалась достаточно долго, запускаем точку доступа")

                    # Асинхронно логируем и запускаем веб
                    try:
                        asyncio.run(log_event(
                            "INFO",
                            "Кнопка удерживалась {} сек. Запуск точки доступа.".format(int(duration)),
                            action="BUTTON_HOLD"
                        ))
                    except RuntimeError:
                        # если уже есть цикл — игнорируем
                        pass

                    start_access_point()
                    run_flask_web()
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[INFO] Мониторинг кнопки остановлен вручную")
    finally:
        GPIO.cleanup()

def start_button_listener():
    thread = threading.Thread(target=monitor_button, daemon=True)
    thread.start()
