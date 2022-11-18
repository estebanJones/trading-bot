import sys
from binance import Client
from binance.spot import Spot
sys.path.append("./live_tools")
import pandas as pd
from datetime import datetime
import json
import requests

def get_api_keys():
    f = open("/home/esteban/Documents/trading/binance_bot/secret.json")
    secret = json.load(f)
    f.close()
    return secret

def get_last_data():
    f = open("/home/esteban/Documents/trading/binance_bot/strategies/grid_spot_usd/last_data.json")
    last_data = json.load(f)
    f.close()
    return last_data

def get_realtime_price_testnet(pair: str):
    client = Client(apiKeys['prod-public'], apiKeys['prod-private'], testnet=True)
    last_trade = client.get_recent_trades(symbol=pair, limit=1)
    return last_trade[0]["price"]

def test():
    print("test")

apiKeys = get_api_keys()
last_data = get_last_data()

print("Binance Bot launch !")

def custom_grid(
    first_price, last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
):
    down_pct_unity = last_order_down / down_grid_len
    up_pct_unity = last_order_up / up_grid_len

    grid_sell = []
    grid_buy = []

    for i in range(down_grid_len):
        grid_buy.append(first_price - first_price * down_pct_unity * (i + 1))

    for i in range(up_grid_len):
        grid_sell.append(first_price + first_price * up_pct_unity * (i + 1))

    return grid_buy, grid_sell


now = datetime.now()
print(now.strftime("%d-%m %H:%M:%S"))

symbol = "BTC/USD"
coin1 = "BTC"
coin2 = "USD"
total_orders = 10

current_price = get_realtime_price_testnet("BTCUSDT")
print("current_price: {}".format(current_price))

client = Spot(apiKeys['testnet-public'], apiKeys['testnet-private'], base_url='https://testnet.binance.vision')
orders_list = client.get_orders("BTCUSDT")
print("orders_list: {}".format(orders_list))





