import  sys
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/strategies/services")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/indirection")

from binance import Client
import pandas as pd
from datetime import datetime
import logging
import grid_manager
import binance_api

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("strategy-binance.py")

IS_TESTNET = False
global_environment = "prod"
global_pair = "BNBETH"
global_symbol = "BNB/ETH"
global_coin1 = "BNB"
global_coin2 = "ETH"
fees_buy = 0.854

def add_to_excel_list(side: str, quantity: float, price: float):
    trade_list_logs.append({
        "date": now,
        "side": side,
        "bnb_amount": quantity,
        "price": price
    })


last_data = grid_manager.get_last_data()
now = datetime.now()

logger.info("Binance Bot started !")
logger.info("Today is the {}".format(now.strftime("%d-%m %H:%M:%S")))


total_orders = 8
currentPrice = binance_api.get_realtime_price(global_pair, global_environment, IS_TESTNET)

logger.info("Price: 1 BNB = {} ETH".format(currentPrice))

# , base_url='https://testnet.binance.vision'
client = binance_api.get_spot_client(global_environment)

orders_list = []
trade_list_logs = []
for order in client.get_open_orders(global_pair):
    orders_list.append(order)

logger.info("Existing open orders:\n {}".format(orders_list))

df_order = pd.DataFrame(orders_list)
if df_order.empty == False:
    df_order["price"] = pd.to_numeric(df_order["price"])
    df_order["origQty"] = pd.to_numeric(df_order["origQty"])

balances = binance_api.get_balance_eth_bnb(global_coin1, global_coin2, global_environment, IS_TESTNET)

coin1_balance = float(balances[global_coin1])
coin2_balance = float(balances[global_coin2])
logger.info("BNB balance: {}".format(coin1_balance))
logger.info("ETH  balance: {}".format(coin2_balance))
coin2_balance_with_fees = coin2_balance * (1 - fees_buy / 100)
logger.info("ETH  balance avec fees: {}".format(coin2_balance_with_fees))
if (
    df_order.empty
    or len(df_order.loc[df_order["side"] == "BUY"]) == 0
    or len(df_order.loc[df_order["side"] == "SELL"]) == 0
):
    logger.info("Creating new grid...")
    grid_buy, grid_sell = grid_manager.custom_grid(
        float(currentPrice),
        last_order_down = 0.02, last_order_up = 0.02, down_grid_len=4, up_grid_len=4
    )
    for price_buy in grid_buy:
        # quantity_buy = round((coin2_balance_with_fees / price_buy) / len(grid_buy), 3)
        quantite_buy = (coin2_balance_with_fees / price_buy) / len(grid_buy)
        quantity_truncate = grid_manager.truncate(quantite_buy, 3)
        price = round(price_buy, 4)
        binance_api.new_order(
            client, global_pair, Client.SIDE_BUY, quantity_truncate, price, IS_TESTNET
        )
        logger.info("New orders buy done: Quantity={} - Price={}".format(quantity_truncate, price))
        add_to_excel_list("Buy",quantity_truncate, price)

    for price_sell in grid_sell:
        # quantity_sell = round(coin1_balance / len(grid_sell), 3)
        quantity_sell = coin1_balance / len(grid_sell)
        quantity_truncate = grid_manager.truncate(quantity_sell, 3)
        logger.info("Before sell done: Quantity={} - Price={}".format(quantity_truncate, price))
        price = round(price_sell, 4)
        binance_api.new_order(
            client, global_pair, Client.SIDE_SELL, quantity_truncate, price, IS_TESTNET
        )
        logger.info("New orders sell done: Quantity={} - Price={}".format(quantity_truncate, price))
        add_to_excel_list("Sell",quantity_truncate, price)
        

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
    last_sell_order = df_order.loc[df_order["side"] == "SELL"]["price"].min()
    diff_buy = (currentPrice - last_buy_order) / (buy_order_to_create + 1)
    diff_sell = (last_sell_order - currentPrice) / (sell_order_to_create + 1)

    for i in range(buy_order_to_create):
        quantity = round((coin2_balance_with_fees / currentPrice) / buy_order_to_create,  8)
        buy = currentPrice - diff_buy * (i + 1)
        binance_api.new_order(
            client, global_pair, Client.SIDE_BUY, quantity, buy, IS_TESTNET
        )
        logger.info("New orders buy done: Quantity={} - Price={}".format(quantity, buy))
        add_to_excel_list("Buy", quantity, buy)
    for i in range(sell_order_to_create):
        quantity = round(coin1_balance / sell_order_to_create,  8)
        sell = currentPrice + diff_sell * (i + 1)
        binance_api.new_order(
            client, global_pair, Client.SIDE_SELL, quantity, sell, IS_TESTNET
        )
        logger.info("New orders sell done: Quantity={} - Price={}".format(quantity, sell))
        add_to_excel_list("Sell", quantity, sell)


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

grid_manager.print_open_orders(last_data)


df_trades = pd.DataFrame(trade_list_logs).iloc[:]
# df_trades['wallet_ath'] = df_trades['wallet'].cummax()
# df_trades['price_ath'] = df_trades['price'].cummax()
# df_trades['wallet_drawdown_pct'] = (df_trades['wallet_ath'] - df_trades['wallet']) / df_trades['wallet_ath']
# df_trades['price_drawdown_pct'] = (df_trades['price_ath'] - df_trades['price']) / df_trades['price_ath']
# max_trades_drawdown = df_trades['wallet_drawdown_pct'].max()
# max_price_drawdown = df_trades['price_drawdown_pct'].max()
# wallet_perf = (df_trades.iloc[-1]['wallet'] - df_trades.iloc[0]['wallet']) / df_trades.iloc[0]['wallet']
# price_perf = (df_trades.iloc[-1]['price'] - df_trades.iloc[0]['price']) / df_trades.iloc[0]['price']

writer = pd.ExcelWriter('/home/esteban/python-workspace/trading/binance_bot/logs/bnb-eth-production.xlsx')
df_trades.to_excel(writer)
writer.save()