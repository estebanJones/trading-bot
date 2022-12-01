import json
import math
import logging
logger = logging.getLogger("grid-manager.py")
PATH_OPEN_ORDERS = "/home/esteban/python-workspace/trading/binance_bot/strategies/grid_spot/last_data.json"

def custom_grid(
    first_price, last_order_down = 0.02, last_order_up = 0.02, down_grid_len=4, up_grid_len=4
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


def get_last_data() -> str:
    f = open(PATH_OPEN_ORDERS)
    last_data = json.load(f)
    f.close()
    return last_data

def print_open_orders(data: str):
    with open(PATH_OPEN_ORDERS, "w") as outfile:
        json.dump(data, outfile)
        
# Par defaut lors de l'achat, j'ai arrondi les quantités. Mais je dépasse le solde que je possède.
# Je décide donc de trunc deux chiffres après la virgule sans arrondir
# Il y aura un reste sur le compte. Tous les fonds ne seront pas utilisé
def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n