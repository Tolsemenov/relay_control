# app/network/get_local_ip.py

import socket

def get_local_ip():
    """Возвращает локальный IP-адрес устройства"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # внешний адрес, чтобы определить интерфейс
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Не удалось определить IP"
