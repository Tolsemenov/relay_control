# app/gpio/relay_controller.py

try:
    import orangepi.pi_pc as OPi
    import OPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("[DEBUG] GPIO не поддерживается в этой системе (Windows?)")
    GPIO_AVAILABLE = False

from app.db.models import RelayTarget
from app.logs.logger_helper import log_event


class RelayController:
    """
    Контроллер управления несколькими реле по GPIO.
    """

    # Настройка соответствия: RelayTarget → GPIO-пин (BOARD)
    relay_pins = {
        RelayTarget.PUMP: 11,
        RelayTarget.VALVE1: 13,
        RelayTarget.VALVE2: 15,
        RelayTarget.VALVE3: 16,
    }

    def __init__(self):
        if GPIO_AVAILABLE:
            GPIO.setboard(OPi.PC)
            GPIO.setmode(GPIO.BOARD)
            for pin in self.relay_pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)  # Отключаем по умолчанию

            log_event("INFO", "GPIO инициализирован, все реле выключены", action="INIT")
        else:
            log_event("WARNING", "GPIO недоступен — реле не будут управляться", action="INIT")

    def turn_on(self, target: RelayTarget):
        pin = self.relay_pins.get(target)
        if pin is None:
            log_event("ERROR", f"Неизвестная цель: {target}", target=target, action="ON")
            return

        if GPIO_AVAILABLE:
            GPIO.output(pin, GPIO.LOW)
        log_event("INFO", f"{target.value.upper()} включен", target=target, action="ON")

    def turn_off(self, target: RelayTarget):
        pin = self.relay_pins.get(target)
        if pin is None:
            log_event("ERROR", f"Неизвестная цель: {target}", target=target, action="OFF")
            return

        if GPIO_AVAILABLE:
            GPIO.output(pin, GPIO.HIGH)
        log_event("INFO", f"{target.value.upper()} выключен", target=target, action="OFF")

    def cleanup(self):
        if GPIO_AVAILABLE:
            GPIO.cleanup()
            log_event("INFO", "GPIO очищен", action="CLEANUP")
