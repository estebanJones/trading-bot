from binance import Client
from binance.spot import Spot
import pandas as pd
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.NOTSET)
context = "strategy-binance.py"
logger = logging.getLogger(context)

IS_TESTNET = False
global_environment = "prod"

global_pair = "BNBETH"
global_symbol = "BNB/ETH"
global_coin1 = "BNB"
global_coin2 = "ETH"
PATH_KEYS = "/home/esteban/python-workspace/trading/binance_bot/secret.json"
PATH_OPEN_ORDERS = "/home/esteban/python-workspace/trading/binance_bot/strategies/grid_spot/last_data.json"

def get_api_keys() -> str:
    f = open(PATH_KEYS)
    secret = json.load(f)
    f.close()
    return secret

def get_last_data() -> str:
    f = open(PATH_OPEN_ORDERS)
    last_data = json.load(f)
    f.close()
    return last_data

def new_order(c: Spot, side: enumerate, q: float, p: float):
    if(IS_TESTNET):
        return c.new_order_test(
            symbol=global_pair,
            side=side,
            type=Client.ORDER_TYPE_LIMIT_MAKER,
            quantity=q,
            price=p
        )
    else:
        return c.new_order(
            symbol=global_pair,
            side=side,
            type=Client.ORDER_TYPE_LIMIT_MAKER,
            quantity=q,
            price=p
        )

def get_realtime_price(pair: str):
    client = Client(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'], testnet=IS_TESTNET)
    last_trade = client.get_recent_trades(symbol=pair, limit=1)
    return last_trade[0]["price"]

# Not Already used
def get_exchange_info():
    exchangeInfo = client.exchange_info(global_pair)
    logger.info("BINANCE INFOS:\n {}".format(exchangeInfo))

def get_account_infos():
    client = Client(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'], testnet=IS_TESTNET)
    accountInfos = client.get_account()
    return accountInfos

def get_balance_eth_btc():
    bnbBalance = ""
    ethBalance = ""

    balances = get_account_infos()['balances']
    for balance in balances:
        if balance["asset"] == global_coin1:
            bnbBalance = balance["free"]
        elif balance["asset"] == global_coin2:
            ethBalance = balance["free"]

    return {global_coin1: bnbBalance, global_coin2: ethBalance}


apiKeys = get_api_keys()
last_data = get_last_data()


def custom_grid(
    first_price, last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
):
    logger.info("Starting price to analyze {}".format(first_price))
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

logger.debug("Binance Bot started !")
logger.info("Today is the {}".format(now.strftime("%d-%m %H:%M:%S")))


total_orders = 10
currentPrice = get_realtime_price(global_pair)

logger.info("Price: 1 BNB = {} ETH".format(currentPrice))

# , base_url='https://testnet.binance.vision'
client = Spot(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'])
orders_list = []

for order in client.get_open_orders(global_pair):
    orders_list.append(order)

logger.info("Existing open orders:\n {}".format(orders_list))

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    df_order["price"] = pd.to_numeric(df_order["price"])
    df_order["origQty"] = pd.to_numeric(df_order["origQty"])

balances = get_balance_eth_btc()

coin1_balance = float(balances[global_coin1])
coin2_balance = float(balances[global_coin2])
logger.info("BNB balance: {}".format(coin1_balance))
logger.info("ETH  balance: {}".format(coin2_balance))

if (
    df_order.empty
    or len(df_order.loc[df_order["side"] == "BUY"]) == 0
    or len(df_order.loc[df_order["side"] == "SELL"]) == 0
):
    logger.info("Creating new grid...")
    grid_buy, grid_sell = custom_grid(
        float(currentPrice),
        last_order_down = 0.02, last_order_up = 0.02, down_grid_len=10, up_grid_len=20
    )
    logger.debug("grid_buy={}".format(grid_buy))
    logger.debug("grid_sell={}".format(grid_sell))
    logger.debug("float(currentPrice)={}".format(float(currentPrice)))
    for price_buy in grid_buy:
        logger.debug("coin2_balance / price_buy)={} - len(grid_buy)={}".format(coin2_balance / price_buy, len(grid_buy)))
        quantity_buy = round((coin2_balance / price_buy) / len(grid_buy), 8)
        # new_order(
        #     client, Client.SIDE_BUY, quantity_buy, price_buy
        # )
        logger.info("New orders buy done: Quantity={} - Price={}".format(quantity_buy, price_buy))

    for price_sell in grid_sell:
        quantity_sell = round(coin1_balance / len(grid_sell), 8)
        # new_order(
        #     client, Client.SIDE_SELL, quantity_sell, price_sell
        # )
        logger.info("New orders sell done: Quantity={} - Price={}".format(quantity_sell, price_sell))

elif total_orders == len(df_order):
    logger.info("Existing orders are always active. New orders: None")
else:
    logger.info("Grid not full. Calculating grid completion...")
    buy_order_to_create = last_data["number_of_sell_orders"] - len(
        df_order.loc[df_order["side"] == "SELL"]
    )
    sell_order_to_create = last_data["number_of_buy_orders"] - len(
        df_order.loc[df_order["side"] == "BUY"]
    )
    logger.info("Total new orders buy {}".format(buy_order_to_create))
    logger.info("Total new orders sell {}".format(sell_order_to_create))

    last_buy_order = df_order.loc[df_order["side"] == "BUY"]["price"].max()
    logger.debug("Last max buy: {}".format(last_buy_order))
    last_sell_order = df_order.loc[df_order["side"] == "SELL"]["price"].min()
    logger.debug("Last min sell: {}".format(last_sell_order))
    diff_buy = (currentPrice - last_buy_order) / (buy_order_to_create + 1)
    logger.debug("diff_buy: {}".format(diff_buy))
    logger.debug("currentPrice: {}".format(currentPrice))
    logger.debug("last_buy_order: {}".format(last_buy_order))
    logger.debug("buy_order_to_create: {}".format(buy_order_to_create))
    diff_sell = (last_sell_order - currentPrice) / (sell_order_to_create + 1)
    logger.debug("diff_sell: {}".format(diff_sell))
    logger.debug("currentPrice: {}".format(currentPrice))
    logger.debug("last_sell_order: {}".format(last_sell_order))
    logger.debug("sell_order_to_create: {}".format(sell_order_to_create))

    for i in range(buy_order_to_create):
        quantity = round((coin2_balance / currentPrice) / buy_order_to_create,  8)
        buy = currentPrice - diff_buy * (i + 1)
        # new_orde(
        #     client, Client.SIDE_BUY, quantity, buy
        # )
    for i in range(sell_order_to_create):
        quantity = round(coin1_balance / sell_order_to_create,  8)
        sell = currentPrice + diff_sell * (i + 1)
        # new_order(
        #     client, Client.SIDE_SELL, quantity, sell
        # )

orders_list = []
for order in client.get_open_orders(global_pair):
    orders_list.append(order)

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    last_data["number_of_buy_orders"] = len(df_order.loc[df_order["side"] == "BUY"])
    last_data["number_of_sell_orders"] = len(df_order.loc[df_order["side"] == "SELL"])
else:
    last_data["number_of_buy_orders"] = 0
    last_data["number_of_sell_orders"] = 0

with open(PATH_OPEN_ORDERS, "w") as outfile:
    json.dump(last_data, outfile)
