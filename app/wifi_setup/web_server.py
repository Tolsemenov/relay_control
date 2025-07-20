# app/wifi_setup/web_server.py

import os
import json
import subprocess
from quart import Quart, render_template, request, redirect
from app.logs.logger_helper import log_event

app = Quart(__name__)
NETWORKS_FILE = os.path.join(os.path.dirname(__file__), 'known_networks.json')


async def load_networks():
    if not os.path.exists(NETWORKS_FILE):
        return []
    with open(NETWORKS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


async def save_networks(networks):
    with open(NETWORKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(networks, f, indent=2, ensure_ascii=False)


@app.route('/')
async def index():
    networks = await load_networks()
    return await render_template('index.html', networks=networks)


@app.route('/connect', methods=['POST'])
async def connect():
    form = await request.form
    ssid = form['ssid']
    password = form['password']

    await log_event("INFO", f"Пользователь выбрал сеть: {ssid}", action="WIFI_SELECT", target=ssid)

    networks = await load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    networks.append({'ssid': ssid, 'password': password})
    await save_networks(networks)

    await log_event("INFO", f"Сохранён Wi-Fi профиль: {ssid}", action="WIFI_SAVE", target=ssid)

    # subprocess остаётся синхронным
    subprocess.call(['sudo', 'bash', 'save_wifi.sh', ssid, password])
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])

    await log_event("INFO", f"Точка доступа выключена, попытка подключения к {ssid}", action="WIFI_CONNECT", target=ssid)

    subprocess.call(['/home/relay_control/.venv/bin/python', '/home/relay_control/app/main.py'])

    return "✅ Подключение запущено. Можно закрыть эту страницу."


@app.route('/delete/<ssid>')
async def delete(ssid):
    networks = await load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    await save_networks(networks)

    await log_event("INFO", f"Удалена сохранённая сеть: {ssid}", action="WIFI_DELETE", target=ssid)

    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
