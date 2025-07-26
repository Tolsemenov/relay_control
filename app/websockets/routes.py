# app/websockets/routes.py
from quart import websocket, Blueprint
from app.websockets.broadcaster import WebSocketBroadcaster

ws_bp = Blueprint("ws", __name__)


@ws_bp.websocket("/ws")
async def status_socket():
    await WebSocketBroadcaster.register(websocket._get_current_object())
    try:
        while True:
            await websocket.receive()
    finally:
        await WebSocketBroadcaster.unregister(websocket._get_current_object())
