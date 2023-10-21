import MetaTrader5 as mt5
import pandas as pd
from classes import Bot
from threading import Thread

bot1 = Bot("EURUSD",0.01,2,4,"buy")
bot2 = Bot("GBPUSD",0.01,2,4,"buy")

def b1():
    bot1.run()
def b2():
    bot2.run()

thread1 = Thread(target=b1)
thread2 = Thread(target=b2)


mt5.initialize(login = 51071567,server = "ICMarketsSC-Demo",password ="nXpV6Hr9")

thread1.start()
thread2.start()











