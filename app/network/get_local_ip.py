# app/network/get_local_ip.py

import socket

def get_local_ip():
    try:
        # подключаемся к внешнему адресу, чтобы получить IP интерфейса
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # любой внешний адрес
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
