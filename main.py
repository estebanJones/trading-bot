import sys
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/strategies/grid_spot")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/strategies/services")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/indirection")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/repositories")
from datetime import datetime
import pandas as pd
import grid_manager
import binance_api
import logging
import grid_binance

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("main.py")



def run():
    IS_TESTNET = False
    global_environment = "prod"
    global_pair = "BNBETH"
    global_coin1 = "BNB"
    global_coin2 = "ETH"
    fees_buy = 0.854

    last_data = grid_manager.get_last_data()
    now = datetime.now()

    logger.info("Binance Bot started !")
    logger.info("Today is the {}".format(now.strftime("%d-%m %H:%M:%S")))


    total_orders = 8
    currentPrice = binance_api.get_realtime_price(global_pair, global_environment, IS_TESTNET)
    currentPriceFloat = float(currentPrice)

    logger.info("Price: 1 BNB = {} ETH".format(currentPriceFloat))

    # , base_url='https://testnet.binance.vision'
    client = binance_api.get_spot_client(global_environment)

    trade_list_logs = grid_binance.run_grid_strategie(
        client, global_pair, global_coin1, global_coin2, global_environment, IS_TESTNET, fees_buy, currentPriceFloat, last_data, total_orders
    )

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

    writer = pd.ExcelWriter('./bnb-eth-production.xlsx')
    df_trades.to_excel(writer)
    writer.save()

run()