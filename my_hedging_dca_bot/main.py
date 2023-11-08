import MetaTrader5 as mt5
import pandas as pd
from my_hedging_dca_bot import MyHedgingDCABot
from threading import Thread


bot1 = MyHedgingDCABot("EURAUD",0.01)
bot2 = MyHedgingDCABot("EURUSD",0.01)




def b1():
    bot1.run()
def b2():
    bot2.run()



thread1 = Thread(target=b1)
thread2 = Thread(target=b2)




mt5.initialize(login=51452573, server="ICMarketsSC-Demo", password="duHYAEaq")

thread1.start()
thread2.start()












