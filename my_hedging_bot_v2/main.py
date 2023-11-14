import MetaTrader5 as mt5
from my_hedging_dca_bot import MyHedgingDCABot
from threading import Thread

# Initialize bots for each currency pair with specified volumes
bot1 = MyHedgingDCABot("EURAUD", 0.01, 0.002)
bot2 = MyHedgingDCABot("EURUSD", 0.02, 0.002)
bot3 = MyHedgingDCABot("EURGBP", 0.03, 0.002)
bot4 = MyHedgingDCABot("GBPUSD", 0.01, 0.002)
bot6 = MyHedgingDCABot("USDCAD", 0.02, 0.002)
bot7 = MyHedgingDCABot("USDCHF", 0.03, 0.002)


# Define functions to run each bot
def b1():
    bot1.run()
def b2():
    bot2.run()
def b3():
    bot3.run()
def b4():
    bot4.run()
def b6():
    bot6.run()
def b7():
    bot7.run()


# Create and start a thread for each bot
thread1 = Thread(target=b1)
thread2 = Thread(target=b2)
thread3 = Thread(target=b3)
thread4 = Thread(target=b4)
thread6 = Thread(target=b6)
thread7 = Thread(target=b7)


# Initialize MT5 connection
mt5.initialize(login=51469037, server="ICMarketsSC-Demo", password="fMybIXD8")

# Start all threads
thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread6.start()
thread7.start()



# TODO: Investigate no money bug