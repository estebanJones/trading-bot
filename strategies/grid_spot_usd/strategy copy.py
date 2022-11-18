import sys
sys.path.append('../')
# from utilities.get_data import get_historical_from_db
import pandas as pd
import ccxt
import matplotlib.pyplot as plt
import ta
import json

f = open(
    "./live_tools/strategies/grid_spot_usd/last_data.json",
)
last_data = json.load(f)
f.close()

def custom_grid(
    first_price = 16882, last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
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

symbol = "BTC/USD"
coin1 = "BTC"
coin2 = "USD"
total_orders = 10

current_price = 16898,882

orders_list = []
orders_list.append({
    "date": "2022-07-01 00:00:00",
    "side": "Buy",
    "price": 16898.882,
    "size": 0.009
})

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    df_order["price"] = pd.to_numeric(df_order["price"])
    df_order["size"] = pd.to_numeric(df_order["size"])
# print(df_order)

coin1_balance = 200
coin2_balance = 200 / 16898.882
# print(coin1_balance, coin2_balance)

if (
    df_order.empty
    or len(df_order.loc[df_order["side"] == "buy"]) == 0
    or len(df_order.loc[df_order["side"] == "sell"]) == 0
):
    print("create new grid")
    grid_buy, grid_sell = custom_grid(
        current_price,
        last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
    )
    for buy in grid_buy:
        # print(buy,(coin2_balance/buy)/len(grid_buy))
        orders_list.append({
            "date": "2022-07-01 00:00:00",
            "side": "Buy",
            "price": buy,
            "size": (coin2_balance / buy) / len(grid_buy)
        })

    for sell in grid_sell:
        # print(sell,coin1_balance/len(grid_sell))
        orders_list.append({
            "date": "2022-07-01 00:00:00",
            "side": "Sell",
            "price": sell,
            "size": coin1_balance / len(grid_sell)
        })

elif total_orders == len(df_order):
    print("no new orders")

else:
    buy_order_to_create = last_data["number_of_sell_orders"] - len(
        df_order.loc[df_order["side"] == "sell"]
    )
    sell_order_to_create = last_data["number_of_buy_orders"] - len(
        df_order.loc[df_order["side"] == "buy"]
    )
    print("Create", buy_order_to_create, "new buy orders")
    print("Create", sell_order_to_create, "new sell orders")
    last_buy_order = df_order.loc[df_order["side"] == "buy"]["price"].max()
    last_sell_order = df_order.loc[df_order["side"] == "sell"]["price"].min()

    diff_buy = (current_price - last_buy_order) / (buy_order_to_create + 1)
    diff_sell = (last_sell_order - current_price) / (sell_order_to_create + 1)

    for i in range(buy_order_to_create):
        # print("buy",current_price - diff_buy*(i+1))
        ftx.place_limit_order(
            symbol=symbol,
            side="buy",
            amount=(coin2_balance / current_price) / buy_order_to_create,
            price=current_price - diff_buy * (i + 1),
        )
    for i in range(sell_order_to_create):
        # print("sell",current_price + diff_sell*(i+1))
        ftx.place_limit_order(
            symbol=symbol,
            side="sell",
            amount=coin1_balance / sell_order_to_create,
            price=current_price + diff_sell * (i + 1),
        )

orders_list = []
for order in ftx.get_open_order():
    orders_list.append(order["info"])

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    last_data["number_of_buy_orders"] = len(df_order.loc[df_order["side"] == "buy"])
    last_data["number_of_sell_orders"] = len(df_order.loc[df_order["side"] == "sell"])
else:
    last_data["number_of_buy_orders"] = 0
    last_data["number_of_sell_orders"] = 0

with open("./live_tools/strategies/grid_spot_usd/last_data.json", "w") as outfile:
    json.dump(last_data, outfile)
