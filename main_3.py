import MetaTrader5 as mt5
from hedging_dca import HedgingDCA
from threading import Thread

# Initialize the bots using HedgeDCA class
bot1 = HedgingDCA(symbol="EURUSD", volume=0.01,max_loss_pct =30)
bot2 = HedgingDCA(symbol="GBPUSD", volume=0.01,max_loss_pct =30)
bot3 = HedgingDCA(symbol="EURNZD", volume=0.01,max_loss_pct =30)

# bot1 = HedgedDCA(symbol="BTCUSD", volume=0.01, profit_target=2, no_of_safty_orders=4, direction="buy")
# bot2 = HedgedDCA(symbol="BNBUSD", volume=0.01, profit_target=2, no_of_safty_orders=4, direction="buy")
# bot3 = HedgedDCA(symbol="ETHUSD", volume=0.01, profit_target=2, no_of_safty_orders=4, direction="buy")


def b1():
    bot1.run()

def b2():
    bot2.run()

def b3():
    bot3.run()

# Create threads for the bots
thread1 = Thread(target=b1)
thread2 = Thread(target=b2)
thread3 = Thread(target=b3)

# Initialize MT5
mt5.initialize(login=51446835, server="ICMarketsSC-Demo", password="qwfgKZdZ")

# Start the bot threads
thread1.start()
thread2.start()
thread3.start()