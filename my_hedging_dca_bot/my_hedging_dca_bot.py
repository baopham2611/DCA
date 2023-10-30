import pandas as pd 
import time 
import datetime 
import MetaTrader5 as mt5
import  logging
import os


class MyHedgingDCABot:
    def __init__(self, symbol,volume):
        self.symbol = symbol
        self.volume = volume

        # Set up logger for this instance
        self.logger = logging.getLogger(self.symbol)  # Logger named after the symbol
        self.logger.setLevel(logging.INFO)
        
        log_filename = f"{self.symbol}_bot_log.log"
        file_handler = logging.FileHandler(log_filename, 'a', 'utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        
    def create_trade_history_df(self,symbol):
        cols = [    
                    "trade_date_id",
                    "create_order_date",
                    "buy_ticket",
                    "sell_ticket",
                    "account_balance",
                    "account_equity",
                    "account_margin",
                    "current_market_price",
                    "buy_volume",
                    "sell_volume",
                    "buy_at",
                    "sell_at",
                    "first_buy_at",
                    "first_sell_at",
                    "buy_status",
                    "sell_status",
                    "fib_number",
                    "next_fib_number",
                    "next_volume",
                    "next_buy_at",
                    "next_sell_at",
                    "market_direction",
                    "close_all_order_type",
                    "max_buy_direction_price",
                    "max_sell_direction_price",
                    "close_all_when_market_reverse_price_at",
                    "is_first_order_of_sequence",
                ]
        df_file_name = f"{symbol}_trade_history_df.csv"
        
        # Check if the file already exists
        if os.path.exists(df_file_name):
            self.logger.info(f"File {df_file_name} already exists. Skipping creation.")
            return

        trade_history_df = pd.DataFrame(columns=cols)
        trade_history_df.to_csv(df_file_name, index=None)
        self.logger.info(f"Data frame has been created. File name: {df_file_name}")


    def make_order(self, symbol, volume, order_type):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            self.logger.info("Failed to fetch tick for", symbol)
            return None
        
        order_dict = {'buy': 0, 'sell': 1}
        price_dict = {'buy': tick.ask, 'sell': tick.bid}

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_dict[order_type],
            "price": price_dict[order_type],
            "deviation": 20,
            "magic": 100,
            "comment": "python market order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        order_result = mt5.order_send(request)
        if not order_result or order_result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.info("Failed to send order:", order_result.comment if order_result else "Unknown error")
            return None
        self.logger.info(f"order_result: {order_result}")
        return order_result
    

    def close_last_order(self, symbol,type,ticket,volume):
        tick = mt5.symbol_info_tick(symbol)
        trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
        
        if not tick:
            self.logger.info(f"Failed to fetch tick for {symbol}")
            return None
        if type == "buy":
              last_order_price = float(trade_history_df["buy_at"].iloc[-1])
              order_type = mt5.ORDER_TYPE_SELL           
        elif type == "sell":
              last_order_price = float(trade_history_df["sell_at"].iloc[-1])
              order_type = mt5.ORDER_TYPE_BUY
              

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": int(ticket),
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": last_order_price,
            "deviation": 20,
            "magic": 100,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            # Update the status in the DataFrame
            if type == "buy":
                trade_history_df["buy_status"].iloc[-1] = "close"
            elif type == "sell":
                trade_history_df["sell_status"].iloc[-1] = "close"

            # Write the updated DataFrame back to the CSV file
            trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)
        else:
            self.logger.info("Failed to send order. Return code:", result.retcode if result else "No result")
            self.logger.info("Error:", mt5.last_error())  # This will print the last error from MT5

        return result
    


    def has_open_orders(self,symbol):
        trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
        if trade_history_df.empty:
            return False
        
        last_trade_buy_status = trade_history_df["buy_status"].iloc[-1]
        last_trade_sell_status = trade_history_df["sell_status"].iloc[-1]
        self.logger.info(f"last_trade_buy_status : {last_trade_buy_status}")
        self.logger.info(f"last_trade_sell_status : {last_trade_sell_status}")
        
        if last_trade_buy_status == "open" and last_trade_sell_status == "open":
            return True
        elif last_trade_buy_status == "close" and last_trade_sell_status == "close":
            return False
        else:
            # Handle other cases here, or raise an exception if these cases shouldn't occur
            self.logger.info("Unexpected trade status combination.")
            return False  # or raise an exception
        

    def get_current_market_price(self,symbol):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            self.logger.info(f"Failed to fetch tick for {symbol}")
            return None
        return tick.ask  # or tick.bid based on the requirement
    

    def make_first_order(self,symbol,volume):
        account_info = mt5.account_info()
        first_fib_number = 1
        next_fib_number = 1
        
        self.logger.info(f"Account Balance: {account_info.balance}")
        self.logger.info(f"Account Equity: {account_info.equity}")
        self.logger.info(f"Account Margin: {account_info.margin}")
        self.logger.info(f"Account Free Margin: {account_info.margin_free}")
        self.logger.info(f"fib number :{first_fib_number}")

        symbol_properties = mt5.symbol_info(symbol)
        if symbol_properties:
            self.logger.info(f"Symbol Margin Required for 1 lot: {symbol_properties.margin_hedged}")
        
        self.create_trade_history_df(symbol)

        current_market_price = self.get_current_market_price(symbol)

        make_buy_order = self.make_order(symbol,volume,"buy")
        make_sell_order = self.make_order(symbol,volume,"sell")

        next_buy_volume = volume * float(make_buy_order.price)
        next_sell_volume = volume * float(make_sell_order.price)
        
        # Create a new row with the values you want to append
        first_trade_row = {
            "trade_date_id": pd.Timestamp.now().strftime("%d%m%y%H%M%S"),
            "buy_ticket":make_buy_order.order,
            "sell_ticket":make_sell_order.order,
            "create_order_date": pd.Timestamp.now(),  # Current timestamp
            "account_balance": account_info.balance,
            "account_equity": account_info.equity,
            "account_margin": account_info.margin,
            "current_market_price" : current_market_price,
            "buy_volume": make_buy_order.volume,
            "sell_volume": make_sell_order.volume,
            "buy_at": make_buy_order.price,
            "sell_at": make_sell_order.price,
            "first_buy_at": make_buy_order.price,
            "first_sell_at": make_sell_order.price,
            "buy_status": "open",
            "sell_status": "open",
            "fib_number": first_fib_number,
            "next_fib_number": next_fib_number,
            "next_volume": next_fib_number * volume,
            "next_buy_at": make_buy_order.price + next_buy_volume,
            "next_sell_at": make_sell_order.price - next_sell_volume,
            "market_direction": None,
            "close_all_order_type": None,
            "max_buy_direction_price": make_buy_order.price,
            "max_sell_direction_price": make_sell_order.price,
            "close_all_when_market_reverse_price_at": None,
            "is_first_order_of_sequence": True  # Assuming this is the first order of the sequence
        }
        trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
        # Append the new row to the DataFrame
        trade_history_df = pd.concat([trade_history_df, pd.DataFrame([first_trade_row])], ignore_index=True)

        # Save the updated DataFrame back to the CSV
        trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)

        self.logger.info(f"Data frame has been updated. File name: {symbol}_trade_history_df.csv")



    def make_next_buy_sell_order(self,symbol,volume,market_direction):
        # Get dataframe
        trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
        
        last_fib_number = float(trade_history_df["fib_number"].iloc[-1])
        fib_number = float(trade_history_df["next_fib_number"].iloc[-1])
        next_fib_number = last_fib_number + fib_number
        first_buy_at = trade_history_df["first_buy_at"].iloc[0]
        first_sell_at = trade_history_df["first_sell_at"].iloc[0]
        
        buy_volume = fib_number * volume
        sell_volume = fib_number * volume
        next_volume = next_fib_number * volume
        # get account info
        account_info = mt5.account_info()
        self.logger.info(f"Account Balance: {account_info.balance}")
        self.logger.info(f"Account Equity: {account_info.equity}")
        self.logger.info(f"Account Margin: {account_info.margin}")
        self.logger.info(f"Account Free Margin: {account_info.margin_free}")

        
        # Get current market price
        current_market_price = self.get_current_market_price(symbol)


        make_buy_order = self.make_order(symbol,buy_volume,"sell")
        make_sell_order = self.make_order(symbol,sell_volume,"buy")

        

        if market_direction == "buy":
            close_all_order_type = "sell"
            close_all_when_market_reverse_price_at = make_buy_order.price - 0.30 * (make_buy_order.price - first_buy_at)

        elif market_direction == "sell":
            close_all_order_type = "buy"
            close_all_when_market_reverse_price_at = make_sell_order.price + 0.30 * (first_sell_at - make_sell_order.price)

        
        # Create a new row with the values you want to append
        next_trade_row = {
            "trade_date_id": pd.Timestamp.now().strftime("%d%m%y%H%M%S"),
            "buy_ticket":make_buy_order.order,
            "sell_ticket":make_sell_order.order,
            "create_order_date": pd.Timestamp.now(),  # Current timestamp
            "account_balance": account_info.balance,
            "account_equity": account_info.equity,
            "account_margin": account_info.margin,
            "current_market_price" : current_market_price,
            "buy_volume": make_buy_order.volume,
            "sell_volume": make_sell_order.volume,
            "buy_at": make_buy_order.price,
            "sell_at": make_sell_order.price,
            "first_buy_at": first_buy_at,
            "first_sell_at": first_sell_at,
            "buy_status": "open",
            "sell_status": "open",
            "fib_number": int(fib_number),
            "next_fib_number": next_fib_number,
            "next_volume": next_volume,
            "next_buy_at": make_buy_order.price + next_volume,
            "next_sell_at": make_sell_order.price - next_volume,
            "market_direction": market_direction,
            "close_all_order_type": close_all_order_type,
            "max_buy_direction_price": make_buy_order.price,
            "max_sell_direction_price": make_sell_order.price,
            "close_all_when_market_reverse_price_at": close_all_when_market_reverse_price_at,
            "is_first_order_of_sequence": False  # Assuming this is the first order of the sequence
        }
        
        # Append the new row to the DataFrame
        trade_history_df = pd.concat([trade_history_df, pd.DataFrame([next_trade_row])], ignore_index=True)

        # Save the updated DataFrame back to the CSV
        trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)

        self.logger.info(f"Data frame has been updated. File name: {symbol}_trade_history_df.csv")


    def close_position(self,position,symbol):
        trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
        tick = mt5.symbol_info_tick(position.symbol)
        if not tick:
            self.logger.info(f"Failed to fetch tick for {position.symbol}")
            return None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,  
            "price": tick.ask if position.type == 1 else tick.bid,
            "deviation": 20,
            "magic": 100,
            "comment": "python script close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            # Update the status in the DataFrame
            if type == "buy":
                trade_history_df["buy_status"].iloc[-1] = "close"
            elif type == "sell":
                trade_history_df["sell_status"].iloc[-1] = "close"

            # Write the updated DataFrame back to the CSV file
            trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)
        else:
            self.logger.info("Failed to send order. Return code:", result.retcode if result else "No result")
            self.logger.info("Error:", mt5.last_error())  # This will print the last error from MT5
        
        return result
    

    def close_all_when_market_reverse_price_at_30pct(self,symbol):
        position = mt5.positions_get(symbol=symbol)
        for position in position:
            self.close_position(position,symbol)


    def run(self):
        symbol = self.symbol
        volume = self.volume
        self.logger.info(f"PROGRAM START")
        self.create_trade_history_df(symbol)
        is_has_open_orders = self.has_open_orders(symbol)
        self.logger.info(is_has_open_orders)
        
        if is_has_open_orders == False:
            self.logger.info(f"Make first trade")
            self.make_first_order(symbol,volume)
        
        elif is_has_open_orders == True:
            self.logger.info(f"Already has opened order")

        while True:
            trade_history_df = pd.read_csv(f"{symbol}_trade_history_df.csv")
            current_market_price = float(self.get_current_market_price(symbol))
            next_buy_at = float(trade_history_df["next_buy_at"].iloc[-1])
            next_sell_at = float(trade_history_df["next_sell_at"].iloc[-1])
            trade_current_direction = trade_history_df["market_direction"].iloc[-1]
            close_all_when_market_reverse_price_at = float(trade_history_df["close_all_when_market_reverse_price_at"].iloc[-1])
            max_buy_direction_price = float(trade_history_df["max_buy_direction_price"].iloc[-1])
            max_sell_direction_price = float(trade_history_df["max_sell_direction_price"].iloc[-1])
            first_buy_at = float(trade_history_df["first_buy_at"].iloc[0])
            first_sell_at = float(trade_history_df["first_sell_at"].iloc[0])
            
            # DCA for Buy direction
            if current_market_price >= next_buy_at: 
                self.logger.info("current_market_price >= next_buy_at")
                buy_ticket = trade_history_df["buy_ticket"].iloc[-1]
                buy_volume = trade_history_df["buy_volume"].iloc[-1]
                self.close_last_order(symbol,"buy",buy_ticket,buy_volume)
                self.logger.info(f"Close last buy order: COMPLETED")
                self.make_next_buy_sell_order(symbol,volume,"buy")
                self.logger.info(f"Make next buy and sell orders: COMPLETED")
            
            # DCA for Sell direction
            elif current_market_price <= next_sell_at: 
                self.logger.info("current_market_price <= next_sell_at")
                sell_ticket = trade_history_df["sell_ticket"].iloc[-1]
                sell_volume = trade_history_df["sell_volume"].iloc[-1]
                self.close_last_order(symbol,"sell",sell_ticket,sell_volume)
                self.logger.info(f"Close last sell order: COMPLETED")
                self.make_next_buy_sell_order(symbol,volume,"sell")
                self.logger.info(f"Make next buy and sell orders: COMPLETED")

            
            # Keep holding when not hit the next buy or next sell price
            elif current_market_price >= next_sell_at and current_market_price <= next_buy_at:
                if trade_current_direction == "buy" and current_market_price > max_buy_direction_price:
                    self.logger.info(f"Current market buy price: {current_market_price} > max buy price {max_buy_direction_price}")
                    max_buy_price = current_market_price
                    trade_history_df["max_buy_direction_price"].iloc[-1] = float(max_buy_price)
                    trade_history_df["close_all_when_market_reverse_price_at"].iloc[-1]  = float(max_buy_price) - 0.30 * (max_buy_price - first_buy_at)
                    # Write the updated DataFrame back to the CSV file
                    trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)
                elif trade_current_direction == "sell" and current_market_price < max_sell_direction_price:
                    self.logger.info(f"Current market buy price: {current_market_price} < max sell price {max_sell_direction_price}")
                    max_sell_price = current_market_price 
                    trade_history_df["max_sell_direction_price"].iloc[-1] = float(max_sell_price)
                    trade_history_df["close_all_when_market_reverse_price_at"].iloc[-1] = float(max_sell_price) - 0.30 * (first_sell_at - max_sell_price)
                    # Write the updated DataFrame back to the CSV file
                    trade_history_df.to_csv(f"{symbol}_trade_history_df.csv", index=False)
                

                self.logger.info(f"Current current_market_price: {current_market_price} | next buy price: {next_buy_at} | next sell price: {next_sell_at}")
                self.logger.info(f"Keep holding...")


            elif trade_current_direction == "buy" and current_market_price < close_all_when_market_reverse_price_at:
                self.logger.info(f"Market reverse 30% from buy direction to sell")
                self.close_all_when_market_reverse_price_at_30pct(symbol)
                self.logger.info(f"Close all of the orders: SUCCESSFULLY")
                self.logger.info(f"Bot existing ...")
                exit()
            elif trade_current_direction == "sell" and current_market_price > close_all_when_market_reverse_price_at:
                self.logger.info(f"Market reverse 30% from sell direction to buy") 
                self.close_all_when_market_reverse_price_at_30pct(symbol)
                self.logger.info(f"Close all of the orders: SUCCESSFULLY")
                self.logger.info(f"Bot existing ...")
                exit()
            
            time.sleep(30)
        

