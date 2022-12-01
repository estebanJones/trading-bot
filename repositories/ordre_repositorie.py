import requests
import datetime


def saveOrdre(side: str, token: str, quantity: str, price: str):
    jsonLogs = {
            "date": datetime.datetime.now().isoformat(),
            "side": side,
            "token": token,
            "quantity": quantity,
            "price": price,
        }
    r = requests.post('http://localhost:3000/api/ordersave', json=jsonLogs)
    return r.json()