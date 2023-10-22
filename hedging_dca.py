import MetaTrader5 as mt5
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class HedgingDCA:
    def __init__(self, symbol, volume, profit_target, no_of_safty_orders, direction, max_loss_pct):
        self.symbol = symbol
        self.volume = volume
        self.profit_target = profit_target
        self.no_of_safty_orders = no_of_safty_orders
        self.direction = direction
        self.max_loss_pct = max_loss_pct  # Maximum percentage loss before stopping the bot

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
            df_filtered = df[df["type"] == order_type]

            def calc_row_margin(row):
                return mt5.order_calc_margin(order_type, symbol, row['volume'], row['price_open'])

            margins = df_filtered.apply(calc_row_margin, axis=1)
            return margins.sum()
    
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

    def close_all(self, symbol):
        positions = mt5.positions_get(symbol=symbol)
        for position in positions:
            self.close_position(position)

    def cal_curr_price_deviation(self, symbol):
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return 0
        position = positions[-1]
        initial_price = position.price_open
        current_price = mt5.symbol_info_tick(symbol).ask
        if not current_price:
            print(f"Failed to fetch current price for {symbol}")
            return 0
        deviation = ((current_price - initial_price) / initial_price) * 100
        return -deviation if self.direction == "buy" else deviation
    
    def check_max_loss(self):
        """Checks if the bot has reached the maximum loss threshold."""
        pct_profit = self.cal_pct_profit(self.symbol)
        if pct_profit <= -self.max_loss_pct:
            print("Maximum loss threshold reached. Stopping the bot.")
            self.close_all(self.symbol)
            exit()  # Stop the bot

    def has_open_orders(self, order_type):
        df = self._get_positions_df(self.symbol)
        return not df[df["type"] == order_type].empty
    
    def next_fibonacci(self):
        next_value = self.fibonacci_sequence[-1] + self.fibonacci_sequence[-2]
        self.fibonacci_sequence.append(next_value)
        return next_value


    def run(self):
        self.fibonacci_sequence = [1, 1]

        # Entry
        self.market_order(self.symbol, self.volume, "buy")
        self.market_order(self.symbol, self.volume, "sell")

        dca_count = 0
        current_fib_volume = self.volume * self.next_fibonacci()
        while True:
            positions_df = self._get_positions_df(self.symbol)

            current_buy_profit = self.cal_profit(positions_df, "buy")
            current_sell_profit = self.cal_profit(positions_df, "sell")

            # Profit Taking
            if current_buy_profit >= self.profit_target or current_sell_profit >= self.profit_target:
                self.close_all(self.symbol)
                break

            # DCA Logic if there are no other open orders of the same type
            if not self.has_open_orders("buy") and dca_count < self.no_of_safty_orders:
                self.market_order(self.symbol, current_fib_volume, "buy")
                dca_count += 1
                current_fib_volume = self.volume * self.next_fibonacci()


            if not self.has_open_orders("sell") and dca_count < self.no_of_safty_orders:
                self.market_order(self.symbol, current_fib_volume, "sell")
                dca_count += 1
                current_fib_volume = self.volume * self.next_fibonacci()


            self.check_max_loss()
            time.sleep(20)
