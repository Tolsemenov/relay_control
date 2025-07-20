# app/network/monitor.py

import aiohttp
import asyncio
from app.logs.logger_helper import log_event

async def internet_monitor(interval=60):
    internet_was_up = True

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://1.1.1.1", timeout=5):
                    if not internet_was_up:
                        await log_event("INFO", "Интернет восстановлен", action="NET_UP")
                        internet_was_up = True
        except:
            if internet_was_up:
                await log_event("WARNING", "Интернет пропал", action="NET_DOWN")
                internet_was_up = False
        await asyncio.sleep(interval)
