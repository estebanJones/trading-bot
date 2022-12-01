from binance import Client
from binance.spot import Spot
import json

PATH_KEYS = "/home/esteban/python-workspace/trading/binance_bot/environment.json"

def get_api_keys() -> str:
    f = open(PATH_KEYS)
    secret = json.load(f)
    f.close()
    return secret

apiKeys = get_api_keys()

def get_realtime_price(pair: str, global_environment: str, IS_TESTNET: bool):
    client = Client(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'], testnet=IS_TESTNET)
    last_trade = client.get_recent_trades(symbol=pair, limit=1)
    return last_trade[0]["price"]

def get_account_infos(global_environment: str, IS_TESTNET: bool):
    client = Client(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'], testnet=IS_TESTNET)
    accountInfos = client.get_account()
    return accountInfos

def get_spot_client(global_environment: str):
    return Spot(apiKeys[global_environment]['public'], apiKeys[global_environment]['private'])

def new_order(client: Spot, global_pair: str, side: enumerate, qty: float, price: float, IS_TESTNET):
    if(IS_TESTNET):
        return client.new_order_test(
            symbol=global_pair,
            side=side,
            type=Client.ORDER_TYPE_LIMIT_MAKER,
            quantity=qty,
            price=price
        )
    else:
        return client.new_order(
            symbol=global_pair,
            side=side,
            type=Client.ORDER_TYPE_LIMIT_MAKER,
            quantity=qty,
            price=price
        )

def get_balance_eth_bnb(global_coin1: float, global_coin2: float, global_environment: str, IS_TESTNET: bool):
    bnbBalance = ""
    ethBalance = ""
    balances = get_account_infos(global_environment, IS_TESTNET)['balances']
    for balance in balances:
        if balance["asset"] == global_coin1:
            bnbBalance = balance["free"]
        elif balance["asset"] == global_coin2:
            ethBalance = balance["free"]

    return {global_coin1: bnbBalance, global_coin2: ethBalance}