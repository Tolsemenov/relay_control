try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO_AVAILABLE = True
except ImportError:
    print("[DEBUG] GPIO не поддерживается в этой системе (возможно, не Raspberry Pi)")
    GPIO_AVAILABLE = False

from app.db.models import RelayTarget
from app.logs.logger_helper import log_event


class RelayController:
    relay_pins = {
        RelayTarget.valve1: 11,
        RelayTarget.valve2: 13,
        RelayTarget.valve3: 15,
        RelayTarget.valve4: 16,
    }

    def __init__(self):
        if GPIO_AVAILABLE:
            for pin in self.relay_pins.values():
                try:
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.HIGH)  # OFF
                except Exception as e:
                    print(f"[ERROR] Не удалось инициализировать пин {pin}: {e}")

    async def async_init(self):
        if GPIO_AVAILABLE:
            await log_event("INFO", "GPIO инициализирован, все реле выключены", action="INIT")
        else:
            await log_event("WARNING", "GPIO недоступен — реле не будут управляться", action="INIT")

    async def turn_on(self, target: RelayTarget):
        pin = self.relay_pins.get(target)
        if pin is None:
            await log_event("ERROR", f"Неизвестная цель: {target}", target=target, action="ON")
            return

        if GPIO_AVAILABLE:
            GPIO.output(pin, GPIO.LOW)
        await log_event("INFO", f"{target.value.upper()} включен", target=target, action="ON")

    async def turn_off(self, target: RelayTarget):
        pin = self.relay_pins.get(target)
        if pin is None:
            await log_event("ERROR", f"Неизвестная цель: {target}", target=target, action="OFF")
            return

        if GPIO_AVAILABLE:
            GPIO.output(pin, GPIO.HIGH)
        await log_event("INFO", f"{target.value.upper()} выключен", target=target, action="OFF")

    async def cleanup(self):
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        await log_event("INFO", "GPIO очищен", action="CLEANUP")
