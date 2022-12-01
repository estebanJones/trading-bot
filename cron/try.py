from datetime import datetime
now = datetime.now()
with open("/home/esteban/python-workspace/trading/binance_bot/log-cron.txt", "a") as text_file:
    text_file.write("Run at {}".format(now.strftime("%d-%m %H:%M:%S")))