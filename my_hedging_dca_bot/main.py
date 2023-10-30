import MetaTrader5 as mt5
import pandas as pd
from my_hedging_dca_bot import MyHedgingDCABot
from threading import Thread


bot1 = MyHedgingDCABot("EURAUD",0.01)
bot2 = MyHedgingDCABot("EURUSD",0.01)
bot3 = MyHedgingDCABot("AUDCAD",0.01)
bot4 = MyHedgingDCABot("AUDNZD",0.01)



def b1():
    bot1.run()
def b2():
    bot2.run()
def b3():
    bot3.run()
def b4():
    bot4.run()


thread1 = Thread(target=b1)
thread2 = Thread(target=b2)
thread3 = Thread(target=b3)
thread4 = Thread(target=b4)



mt5.initialize(login=51452573, server="ICMarketsSC-Demo", password="duHYAEaq")

thread1.start()
thread2.start()
thread3.start()
thread4.start()











