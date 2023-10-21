import MetaTrader5 as mt5
from hedge_dca import HedgedDCA 
from threading import Thread

# Initialize the bots using HedgeDCA class
bot1 = HedgedDCA(symbol="EURUSD", volume=0.01, profit_target=2, no_of_safty_orders=4, direction="buy")
bot2 = HedgedDCA(symbol="GBPUSD", volume=0.01, profit_target=2, no_of_safty_orders=4, direction="buy")

def b1():
    bot1.run()

def b2():
    bot2.run()

# Create threads for the bots
thread1 = Thread(target=b1)
thread2 = Thread(target=b2)

# Initialize MT5
mt5.initialize(login=51439413, server="ICMarketsSC-Demo", password="9JjRQcsn")

# Start the bot threads
thread1.start()
thread2.start()
