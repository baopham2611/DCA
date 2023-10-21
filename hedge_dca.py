import MetaTrader5 as mt5
import pandas as pd

class HedgedDCA:
    def __init__(self, symbol, volume, profit_target, no_of_safty_orders, direction):
        self.symbol = symbol
        self.volume = volume
        self.profit_target = profit_target
        self.no_of_safty_orders = no_of_safty_orders
        self.direction = direction

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
        if order_type is not None:
            df = df.loc[df.type == order_type]
        return float(df["profit"].sum())

    def cal_margin(self, df, symbol, order_type):
        df = df.loc[df.type == order_type]

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

    def run(self):
        fibonacci_sequence = [1, 1]  # Starting with the basic sequence
        
        while True:
            # Place both buy and sell orders
            self.market_order(self.symbol, self.volume, "buy")
            self.market_order(self.symbol, self.volume, "sell")

            curr_no_of_safty_orders = 0
            multiplied_volume = self.volume * fibonacci_sequence[-1]  # Using the latest Fibonacci number
            deviation = -1
            next_price_level = -1

            while curr_no_of_safty_orders < self.no_of_safty_orders:
                curr_price_deviation = self.cal_curr_price_deviation(self.symbol)
                if curr_price_deviation <= next_price_level:
                    self.market_order(self.symbol, multiplied_volume, "buy")
                    self.market_order(self.symbol, multiplied_volume, "sell")

                    fibonacci_sequence.append(fibonacci_sequence[-1] + fibonacci_sequence[-2])
                    multiplied_volume = self.volume * fibonacci_sequence[-1]
                    
                    deviation *= 2
                    next_price_level += deviation
                    curr_no_of_safty_orders += 1

                pct_profit = self.cal_pct_profit(self.symbol)
                if pct_profit >= self.profit_target:
                    self.close_all(self.symbol)
                    break
