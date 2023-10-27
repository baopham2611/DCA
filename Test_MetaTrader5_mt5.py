import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HedgingDCA:
    def __init__(self, symbol, volume, max_loss_pct):
        self.symbol = symbol
        self.volume = volume
        self.max_loss_pct = max_loss_pct  # Maximum percentage loss before stopping the bot
        self.fibonacci_sequence = [1, 1]


    def market_order(self, symbol, volume, order_type):
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print("Failed to fetch tick for", symbol)
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
            print("Failed to send order:", order_result.comment if order_result else "Unknown error")
            return None
        
        return order_result

    def _get_positions_df(self, symbol):
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return pd.DataFrame()
        
        df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.drop(['time_update', 'time_msc', 'time_update_msc', 'external_id'], axis=1, inplace=True)
        return df

    def cal_profit(self, df, order_type=None):
        
        if df.empty:  # Check if DataFrame is empty
            return 0.0

        if order_type is not None:
            if "type" not in df.columns:
                print("The 'type' column is missing in the DataFrame.")
                return 0  # or handle this scenario in a way you see fit
            df = df[df['type'] == order_type]
        
        try:
            return float(df["profit"].sum())
        except KeyError:
            print("Error: 'profit' column not found in the DataFrame.")
            return 0.0
        
    def cal_margin(self, df, symbol, order_type):
        if "type" not in df.columns:
            print("The 'type' column is missing in the DataFrame.")
            return 0  # or handle this scenario in a way you see fit
        df = df[df["type"] == order_type]

        sum = 0
        for _, row in df.iterrows():
            margin = mt5.order_calc_margin(order_type, symbol, row['volume'], row['price_open'])
            if margin is None:
                print(f"Failed to calculate margin for {symbol}")
                continue
            sum += margin
        return sum
    
    def cal_pct_profit(self, symbol):
        df = self._get_positions_df(symbol)
        total_profit = self.cal_profit(df)
        buy_margin = self.cal_margin(df, symbol, mt5.ORDER_TYPE_BUY)
        sell_margin = self.cal_margin(df, symbol, mt5.ORDER_TYPE_SELL)
        
        total_margin = buy_margin + sell_margin
        if total_margin == 0:
            return 0
        return (total_profit / total_margin) * 100

    def close_position(self, position):
        tick = mt5.symbol_info_tick(position.symbol)
        if not tick:
            print(f"Failed to fetch tick for {position.symbol}")
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
        return result

    def close_all(self, symbol, order_type):
        """
        Closes all positions for the specified symbol.
        
        Parameters:
        - symbol: The trading pair symbol.
        - order_type (optional): The type of order to close ("buy" or "sell"). If not provided, all positions are closed.
        """
        positions = mt5.positions_get(symbol=symbol)
        
        # If order_type is specified, filter the positions based on the order type
        if order_type:
            order_dict = {'buy': mt5.ORDER_TYPE_BUY, 'sell': mt5.ORDER_TYPE_SELL}
            positions = [position for position in positions if position.type == order_dict[order_type]]

        for position in positions:
            self.close_position(position)


    
    def check_max_loss(self):
        """Checks if the bot has reached the maximum loss threshold."""
        pct_profit = self.cal_pct_profit(self.symbol)
        if pct_profit <= -self.max_loss_pct:
            print(f"Maximum loss threshold reached. Stopping the bot for {self.symbol}")
            self.close_all(self.symbol)
            exit()  # Stop the bot

    def has_open_orders(self, order_type):
        df = self._get_positions_df(self.symbol)
        if df.empty:  # Check if DataFrame is empty
            return False
        try:
            return not df[df["type"] == order_type].empty
        except KeyError:
            logging.error("Error: 'type' column not found in the DataFrame.")
            return False
    
    def next_fibonacci(self):
        next_value = self.fibonacci_sequence[-1] + self.fibonacci_sequence[-2]
        self.fibonacci_sequence.append(next_value)
        return next_value
    
    def get_current_price(self):
        """Fetches the current price for the given symbol."""
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            print(f"Failed to fetch tick for {self.symbol}")
            return None
        return tick.ask  # or tick.bid based on the requirement

    def get_dca_count_from_comment(self):
        """Retrieve the dca_count from order comments"""
        positions = mt5.positions_get(symbol=self.symbol)
        for position in positions:
            comment_parts = position.comment.split('-')
            if len(comment_parts) > 1 and comment_parts[0] == 'DCA':
                return int(comment_parts[1])
        return 0
    
    
    def run(self):
        logging.info(f"PROGRAM START")
        account_info = mt5.account_info()
        logging.info(f"Account Balance: {account_info.balance}")
        logging.info(f"Account Equity: {account_info.equity}")
        logging.info(f"Account Margin: {account_info.margin}")
        logging.info(f"Account Free Margin: {account_info.margin_free}")

        symbol_properties = mt5.symbol_info(self.symbol)
        if symbol_properties:
            logging.info(f"Symbol Margin Required for 1 lot: {symbol_properties.margin_hedged}")

        initial_price = self.get_current_price()
        logging.info("Placing entry BUY and SELL orders at")
        self.market_order(self.symbol, self.volume, 'buy')
        self.market_order(self.symbol, self.volume, 'sell')
        last_price = initial_price
        logging.info(f"Initial Price: {initial_price}")
        last_buy_price = initial_price
        last_sell_price = initial_price

        while True:
            current_price = self.get_current_price()
            
            # Calculate the next Fibonacci target price for both buy and sell
            fib_multiplier = self.next_fibonacci()
            target_price_up = last_price + (self.volume * fib_multiplier)
            target_price_down = last_price - (self.volume * fib_multiplier)

            logging.info(f"Target price up: {target_price_up}")
            logging.info(f"Target price down: {target_price_down}")
            
            if current_price >= target_price_up:
                logging.info(f"Target price upwards {target_price_up} reached!")
                
                # Close buy orders for profit
                self.close_all(self.symbol, 'buy')
                
                # Open new buy and sell orders at the new price
                self.market_order(self.symbol, self.volume, 'buy')
                self.market_order(self.symbol, self.volume, 'sell')
                
                # Update the last buy price
                last_buy_price = current_price
                last_price = current_price


            elif current_price <= target_price_down:
                logging.info(f"Target price downwards {target_price_down} reached!")
                
                # Close sell orders for profit
                self.close_all(self.symbol, 'sell')
                
                # Open new buy and sell orders at the new price
                self.market_order(self.symbol, self.volume, 'buy')
                self.market_order(self.symbol, self.volume, 'sell')
                
                # Update the last sell price
                last_sell_price = current_price
                last_price = current_price

            
            # Check for 30% drop from the last buy order to close all sell orders
            if current_price <= last_buy_price * 0.7:
                logging.warning(f"Price dropped by 30% from the last buy order. Closing all sell orders.")
                self.close_all(self.symbol, 'sell')

            # Check for 30% increase from the last sell order to close all buy orders
            if current_price >= last_sell_price * 1.3:
                logging.warning(f"Price increased by 30% from the last sell order. Closing all buy orders.")
                self.close_all(self.symbol, 'buy')
            
            # Check for maximum loss threshold
            self.check_max_loss()
            
            # Sleep for 20 seconds before next check
            time.sleep(20)



if __name__ == "__main__":
    hedging_dca = HedgingDCA(symbol="EURUSD", volume=0.01, max_loss_pct=30)
    mt5.initialize(login=51446835, server="ICMarketsSC-Demo", password="qwfgKZdZ")
    hedging_dca.run()