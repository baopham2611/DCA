import MetaTrader5 as mt5
import pandas as pd
from classes import Bot
from threading import Thread

bot1 = Bot("EURUSD",0.01,2,4,"sell")
bot2 = Bot("EURUSD",0.01,2,4,"buy")

bot3 = Bot("GBPUSD",0.01,2,4,"sell")
bot4 = Bot("GBPUSD",0.01,2,4,"buy")

bot5 = Bot("EURCHF",0.01,2,4,"sell")
bot6 = Bot("EURCHF",0.01,2,4,"buy")

def b1():
    bot1.run()
def b2():
    bot2.run()

def b3():
    bot3.run()
def b4():
    bot4.run()

def b5():
    bot5.run()
def b6():
    bot6.run()

thread1 = Thread(target=b1)
thread2 = Thread(target=b2)
thread3 = Thread(target=b3)
thread4 = Thread(target=b4)
thread5 = Thread(target=b5)
thread6 = Thread(target=b6)


mt5.initialize(login=51446835, server="ICMarketsSC-Demo", password="qwfgKZdZ")

thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()
thread6.start()





