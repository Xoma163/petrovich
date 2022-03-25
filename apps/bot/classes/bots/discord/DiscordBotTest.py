import json
import threading
import time

import websocket

from petrovich.settings import env


class DiscordBot:
    def __init__(self):
        pass


def send_json_request(ws, request):
    ws.send(json.dumps(request))


def recieve_json_response(ws):
    response = ws.recv()
    if response:
        return json.loads(response)


def heartbeat(interval, ws):
    print("Heartbeat begin")
    while True:
        time.sleep(interval)
        heartbeatJSON = {
            "op": 1,
            "d": "null"
        }
        send_json_request(ws, heartbeatJSON)
        print("Heartbeat sent")


ws = websocket.WebSocket()
ws.connect("wss://gateway.discord.gg/?v=7&encoding=json")
event = recieve_json_response(ws)
heartbeat_interval = event['d']['heartbeat_interval'] / 100

threading.Thread(target=heartbeat, args=(heartbeat_interval, ws)).start()

token = env.str("DISCORD_TOKEN")
payload = {
    'op': 2,
    "d": {
        "token": token,
        "properties": {
            "$os": "windows",
            "$browser": "chrome",
            "$device": "pc"
        }
    }
}
send_json_request(ws, payload)

while True:
    event = recieve_json_response(ws)
    try:
        print(f"{event['d']['author']['username']}: {event['d']['content']}")
        op_code = event('op')
        if op_code == 1:
            print('heartbeat received')
    except Exception as e:
        print('error')
        pass

# url = 'https://discord.com/api/v7/users/@me'
# headers = {
#         'User-Agent': 'DiscordBot (https://github.com/Rapptz/discord.py 1.7.3) Python/3.8 aiohttp/3.7.4.post0',
#         'X-Ratelimit-Precision': 'millisecond',
#         'Authorization': f'Bot {TOKEN}'
# }
#
# r = requests.get(url, headers=headers)
