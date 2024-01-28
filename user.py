import requests
import websocket


BINANCE_FUTURES_END_POINT = "https://fapi.binance.com/fapi/v1/listenKey"

api_key=".."


def create_futures_listen_key(api_key):
    response = requests.post(url=BINANCE_FUTURES_END_POINT, headers={'X-MBX-APIKEY': api_key})
    return response.json()['listenKey']


FUTURES_STREAM_END_POINT_1 = "wss://fstream.binance.com"
listen_key = create_futures_listen_key(api_key)
url = f"{FUTURES_STREAM_END_POINT_1}/ws/{listen_key}"


def on_open(ws):
    print(f"Open: futures order stream connected")

def on_message(ws, message):
    print(f"Message: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Close: {close_status_code} {close_msg}")


ws = websocket.WebSocketApp(url=url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
ws.run_forever(ping_interval=300)