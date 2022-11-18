import sys
from binance import Client
from binance.spot import Spot
sys.path.append("./live_tools")
import pandas as pd
from datetime import datetime
import json
import requests

environment = "test"

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

def new_order(c: Spot, side: enumerate, q: float, p: float):
    # response_order = new_order_testnet(client, Client.SIDE_BUY, 1.0, 4000.0)
    print("client {}".format(c))
    response = c.new_order(
        symbol='BTCUSDT',
        side=side,
        type=Client.ORDER_TYPE_LIMIT_MAKER,
        quantity=q,
        price=p
    )
    return response
    
def get_exchange_info():
    exchangeInfo = client.exchange_info("BTCUSDT")
    print("exchangeInfo: {}".format(exchangeInfo))

def new_order_testnet(c: Spot, side: enumerate, q: float, p: float):
    # response_order = new_order_testnet(client, Client.SIDE_BUY, 1.0, 4000.0)
    print("client {}".format(c))
    response = c.new_order_test(
        symbol='BTCUSDT',
        side=side,
        type=Client.ORDER_TYPE_LIMIT_MAKER,
        quantity=q,
        price=p
    )
    return response

def get_account_infos():
    client = Client(apiKeys[environment]['public'], apiKeys[environment]['private'], testnet=True)
    accountInfos = client.get_account()
    return accountInfos

def get_balance_usdt_btc():
    usdtBalance = ""
    btcBalance = ""

    balances = get_account_infos()['balances']
    for balance in balances:
        if balance["asset"] == "USDT":
            usdtBalance = balance["free"]
        elif balance["asset"] == "BTC":
            btcBalance = balance["free"]

    return {"USDT": usdtBalance, "BTC": btcBalance}

apiKeys = get_api_keys()
last_data = get_last_data()

def get_realtime_price_testnet(pair: str):
    client = Client(apiKeys[environment]['public'], apiKeys[environment]['private'], testnet=True)
    last_trade = client.get_recent_trades(symbol=pair, limit=1)
    return last_trade[0]["price"]

print("Binance Bot launch !")

def custom_grid(
    first_price, last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
):
    print("Price {}".format(first_price))
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

symbol = "BTC/USDT"
coin1 = "BTC"
coin2 = "USDT"
total_orders = 10

currentPrice = get_realtime_price_testnet("BTCUSDT")
print("current_price: {}".format(currentPrice))

client = Spot(apiKeys[environment]['public'], apiKeys[environment]['private'], base_url='https://testnet.binance.vision')
orders_list = []
print("orders_list avant: {}".format(orders_list))
# response_order = new_order_testnet(client, Client.SIDE_BUY, 1, 4000.0000)

for order in client.get_orders("BTCUSDT"):
    orders_list.append(order)

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    df_order["price"] = pd.to_numeric(df_order["price"])
    df_order["executedQty"] = pd.to_numeric(df_order["executedQty"])
# print(df_order)

print("{}".format(get_account_infos()))
balances = get_balance_usdt_btc()

coin1_balance = float(balances[coin1])
coin2_balance = float(balances[coin2])
print("coin1_balance: {}".format(coin1_balance))
print("coin2_balance: {}".format(coin2_balance))

if (
    df_order.empty
    or len(df_order.loc[df_order["side"] == "buy"]) == 0
    or len(df_order.loc[df_order["side"] == "sell"]) == 0
):
    print("create new grid")
    grid_buy, grid_sell = custom_grid(
        int(float(currentPrice)),
        last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
    )

    for buy in grid_buy:
        quantity = round((coin2_balance / buy) / len(grid_buy), 8)
        print("buy: {}".format(buy))
        print("quantite rounded {}".format(quantity))
        get_exchange_info()
        new_order_testnet(
            client, Client.SIDE_BUY, quantity, buy
        )

    for sell in grid_sell:
        # print(sell,coin1_balance/len(grid_sell))
        quantity = round(coin1_balance / len(grid_sell), 8)
        print("sell: {}".format(sell))
        print("quantite rounded {}".format(quantity))
        new_order_testnet(
            client, Client.SIDE_SELL, quantity, sell
        )

elif total_orders == len(df_order):
    print("no new orders")
else:
    print("else")