# app/gpio/relay_state_manager.py

from app.db.database import AsyncSessionLocal
from app.db.models import RelayName
from app.gpio.relay_controller import RelayController
from app.logs.logger_helper import log_event
from sqlalchemy.future import select

from app.websockets.broadcaster import WebSocketBroadcaster

controller = RelayController()


class RelayStateManager:
    @staticmethod
    async def set_status(relay_key: str, status: bool, source="MANUAL"):
        async with AsyncSessionLocal() as session:
            print("RelayStateManager.set_status")
            result = await session.execute(select(RelayName).where(RelayName.relay_key == relay_key))
            relay = result.scalar_one_or_none()
            if not relay:
                return False

            if relay.status == status:
                return True  # Ничего не меняем, уже в нужном состоянии

            relay.status = status
            await session.commit()

            if status:
                await controller.turn_on(relay_key)
                await log_event("INFO", f"Реле '{relay.name}' включено через {source}", target=relay_key,
                                action="SWITCH_ON")
            else:
                await controller.turn_off(relay_key)
                await log_event("INFO", f"Реле '{relay.name}' выключено через {source}", target=relay_key,
                                action="SWITCH_OFF")

            # ⚡ Уведомляем через WebSocket
            await WebSocketBroadcaster.broadcast_status(relay_key, status)

            return True
