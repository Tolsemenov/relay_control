# app/websockets/broadcaster.py

class WebSocketBroadcaster:
    clients = set()

    @classmethod
    async def register(cls, ws):
        cls.clients.add(ws)

    @classmethod
    async def unregister(cls, ws):
        cls.clients.discard(ws)

    @classmethod
    async def broadcast_status(cls, relay_key: str, status: bool):
        message = {"type": "status_update", "relay_key": relay_key, "status": status}
        for client in cls.clients:
            try:
                await client.send_json(message)
            except Exception:
                pass  # клиент отключился
