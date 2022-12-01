import  sys
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/strategies/services")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/indirection")
sys.path.append("/home/esteban/python-workspace/trading/binance_bot/repositories")
import grid_manager
import binance_api
import ordre_repositorie
from binance.spot import Spot
from binance import Client
import pandas as pd
from datetime import datetime
import logging


logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("grid_binance.py")
trade_list_logs = []

def add_to_excel_list(side: str, quantity: float, price: float):
    trade_list_logs.append({
        "date": datetime.now(),
        "side": side,
        "bnb_amount": quantity,
        "price": price
    })

def run_grid_strategie(
        client: Spot, global_pair: str, global_coin1: str, global_coin2: str, global_environment: str, IS_TESTNET: str, fees_buy: float,
        currentPriceFloat: float, last_data: str, total_orders: int
    ): 
    orders_list = []
    
    for order in client.get_open_orders(global_pair):
        orders_list.append(order)

    logger.info("Existing open orders:\n {}".format(orders_list))

    df_order = pd.DataFrame(orders_list)
    if df_order.empty == False:
        df_order["price"] = pd.to_numeric(df_order["price"])
        df_order["origQty"] = pd.to_numeric(df_order["origQty"])

    balances = binance_api.get_balance_eth_bnb(global_coin1, global_coin2, global_environment, IS_TESTNET)

    starting_bot_eth = 0.0226
    starting_bot_bnb = 1.023
    # coin1_balance = float(balances[global_coin1])
    # coin2_balance = float(balances[global_coin2])
    coin1_balance = starting_bot_bnb
    coin2_balance = starting_bot_eth

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
            currentPriceFloat,
            last_order_down = 0.02, last_order_up = 0.02, down_grid_len=4, up_grid_len=4
        )
        for price_buy in grid_buy:
            quantite_buy = (coin2_balance_with_fees / price_buy) / len(grid_buy)
            quantityTruncate = grid_manager.truncate(quantite_buy, 3)
            price = round(price_buy, 4)

            # binance_api.new_order(
            #     client, global_pair, Client.SIDE_BUY, quantityTruncate, price, IS_TESTNET
            # )
            # order_save = ordre_repositorie.saveOrdre("ACHAT", global_coin2, str(quantityTruncate), str(price))
            logger.warning("New orders buy save: Ordre={}".format(quantityTruncate))
            add_to_excel_list("Buy",quantityTruncate, price)

        for price_sell in grid_sell:
            quantity_sell = coin1_balance / len(grid_sell)
            quantityTruncate = grid_manager.truncate(quantity_sell, 3)
            price = round(price_sell, 4)
            # binance_api.new_order(
            #     client, global_pair, Client.SIDE_SELL, quantityTruncate, price, IS_TESTNET
            # )
            # order_save = ordre_repositorie.saveOrdre("VENTE", global_coin1, str(quantityTruncate), str(price))
            logger.warning("New orders sell save: Ordre={}".format(quantityTruncate))
            add_to_excel_list("Sell",quantityTruncate, price)
            

    elif total_orders == len(df_order):
        logger.info("Existing orders are always active. New orders: None")
    else:
        logger.info("Grid not full. Calculating grid completion...")
        buy_order_to_create = last_data["number_of_buy_orders"] - len(
            df_order.loc[df_order["side"] == "BUY"]
        )
        sell_order_to_create = last_data["number_of_sell_orders"] - len(
            df_order.loc[df_order["side"] == "SELL"]
        )
        logger.info("Total new orders buy {}".format(buy_order_to_create))
        logger.info("Total new orders sell {}".format(sell_order_to_create))
        logger.info("Grid {}".format(df_order))
        last_buy_order = df_order.loc[df_order["side"] == "BUY"]["price"].min()
        last_sell_order = df_order.loc[df_order["side"] == "SELL"]["price"].max()
        diff_buy = (currentPriceFloat - last_buy_order) / (buy_order_to_create + 1)
        diff_sell = (last_sell_order - currentPriceFloat) / (sell_order_to_create + 1)

        for i in range(buy_order_to_create):
            quantite_buy = (coin2_balance_with_fees / currentPriceFloat) / buy_order_to_create
            quantityTruncate = grid_manager.truncate(quantite_buy, 3)
            price = currentPriceFloat - diff_buy * (i + 1)
            priceRound = round(price, 4)
            # binance_api.new_order(
            #     client, global_pair, Client.SIDE_BUY, quantityTruncate, priceRound, IS_TESTNET
            # )
            # order_save = ordre_repositorie.saveOrdre("ACHAT", global_coin2, str(quantityTruncate), str(price))
            logger.warning("New orders buy save: Quantity={}".format(quantityTruncate))
            add_to_excel_list("Buy", quantityTruncate, priceRound)
        for i in range(sell_order_to_create):
            quantity_sell = coin1_balance / sell_order_to_create
            quantityTruncate = grid_manager.truncate(quantity_sell,  3)
            price = currentPriceFloat + diff_sell * (i + 1)
            priceRound = round(price, 4)
            # binance_api.new_order(
            #     client, global_pair, Client.SIDE_SELL, quantityTruncate, priceRound, IS_TESTNET
            # )
            # order_save = ordre_repositorie.saveOrdre("VENTE", global_coin1, str(quantityTruncate), str(price))
            logger.warning("New orders sell save: Quantity={} - Price={}".format(quantityTruncate, priceRound))
            add_to_excel_list("Sell", quantityTruncate, price)

    return trade_list_logs