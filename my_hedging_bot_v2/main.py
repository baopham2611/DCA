import MetaTrader5 as mt5
from my_hedging_dca_bot import MyHedgingDCABot
from threading import Thread

# Initialize bots for each currency pair with specified volumes
bot1 = MyHedgingDCABot("EURAUD", 0.03)
bot2 = MyHedgingDCABot("EURUSD", 0.03)
bot4 = MyHedgingDCABot("EURGBP", 0.03)
bot5 = MyHedgingDCABot("AUDUSD", 0.03)
bot6 = MyHedgingDCABot("USDCAD", 0.03)


# Define functions to run each bot
def b1():
    bot1.run()
def b2():
    bot2.run()
def b4():
    bot4.run()
def b5():
    bot5.run()
def b6():
    bot6.run()


# Create and start a thread for each bot
thread1 = Thread(target=b1)
thread2 = Thread(target=b2)
thread4 = Thread(target=b4)
thread5 = Thread(target=b5)
thread6 = Thread(target=b6)


# Initialize MT5 connection
mt5.initialize(login=51460474, server="ICMarketsSC-Demo", password="nu13y5n9")

# Start all threads
thread1.start()
thread2.start()
thread4.start()
thread5.start()
thread6.start()

