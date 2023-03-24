import json
from typing import Any, List, Dict
from datamodel import OrderDepth, TradingState, Order, ProsperityEncoder, Symbol

class Logger:
    def __init__(self) -> None:
        self.logs = ""

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]]) -> None:
        print(json.dumps({
            "state": state,
            "orders": orders,
            "logs": self.logs,
        }, cls=ProsperityEncoder, separators=(",", ":"), sort_keys=True))

        self.logs = ""

logger = Logger()

class Trader:
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is weighted mean, second is total volume of that mean.
    long_term_means = {}
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is mean of middle price from last x days and second is queue of middle price of from past x days.
    short_term_means = {}

    # queue of past mid prices
    banana_past_mid_prices = []

    # Dict with product as keys and corresponding dict for various smas with their time frame as key
    smas = {}

    # Similar to smas
    channels = {}

    # last 5 most recent differences between sma250 and sma10
    last_sma_diffs = []

    position_limit_pearls = position_limit_bananas = 20
    position_limit_pina_coladas, position_limit_coconuts = 300, 600

    exponential_buy_amount, exponential_sell_amount = 1, -1

    def find_long_term_means(self, product: str, order_depth: OrderDepth) -> int:
        product_mean: List = self.long_term_means[product]
        weighted_mean, total_volume = 0, 0
        for price, volume in order_depth.buy_orders.items():
            weighted_mean += price * volume
            total_volume += volume

        for price, volume in order_depth.sell_orders.items():
            weighted_mean += price * -volume
            total_volume += -volume
        
        if (product_mean[1] + total_volume) != 0:
            product_mean[0] = ((product_mean[0] * product_mean[1]) + weighted_mean)/(product_mean[1] + total_volume)
            product_mean[1] = (product_mean[1] + total_volume)
        return product_mean[0]

    def find_short_term_means(self, product: str, order_depth: OrderDepth, max_queue_length) -> int:
        curr_mid_price = (max(order_depth.sell_orders.keys()) + min(order_depth.buy_orders.keys()))/2
        sum_past_prices = curr_mid_price
        for price in self.banana_past_mid_prices:
            sum_past_prices += price
        mean = sum_past_prices / (len(self.banana_past_mid_prices) + 1)

        self.banana_past_mid_prices.insert(0, curr_mid_price)
        if len(self.banana_past_mid_prices) > max_queue_length:
            self.banana_past_mid_prices.pop()

        return mean

    # quotes the greatest possible volume on both buy and sell sides for a set spread
    def order_at_order_limit(self, fair_price, order_depth, position, product) -> list[Order]:
        order_limit: tuple = (20 - position[product], -20 - position[product])
        product_orders: list[Order] = []
        if fair_price and len(order_depth.sell_orders) != 0:
                buy_limit = order_limit[0]
                #logger.print("BUY", product, str(buy_limit) + "x", fair_price - 1)
                product_orders.append(Order(product, fair_price - 1, buy_limit))
            
        # Selling
        if fair_price and len(order_depth.buy_orders) != 0:
            sell_limit = order_limit[1]
            #logger.print("SELL", product, str(sell_limit) + "x", fair_price + 1)
            product_orders.append(Order(product, fair_price + 1, sell_limit))
        
        return product_orders

    def set_and_get_sma(self, curr_mid_price, product, time_frame):
        if product not in self.smas:
            self.smas[product] = {}
        if time_frame not in self.smas[product]:
            self.smas[product][time_frame] = []   
        self.smas[product][time_frame].insert(0, curr_mid_price)
        if len(self.smas[product][time_frame]) > time_frame:
            self.smas[product][time_frame].pop()
        return round(sum(self.smas[product][time_frame]) / len(self.smas[product][time_frame]), 2)
    
    # work on this strategy for market neutral but high volatility products
    def arb_off_sma(self, order_depth, position, product, time_frame, position_limit):
        curr_mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
        sma = self.set_and_get_sma(curr_mid_price, product, time_frame)
        logger.print("sma: ", sma)
        product_position = position[product]
        product_orders: list[Order] = []
        buy_limit, sell_limit = position_limit - product_position, -position_limit - product_position

        if curr_mid_price - sma > 10:
            product_orders.append(Order(product, min(order_depth.buy_orders.keys()), sell_limit // 2))
        elif sma - curr_mid_price > 10:
            product_orders.append(Order(product, max(order_depth.sell_orders.keys()), buy_limit // 2))
        elif abs(curr_mid_price - sma) < 3:
            if product_position < 0:
                product_orders.append(Order(product, max(order_depth.sell_orders.keys()), min(-product_position, buy_limit // 2)))
            elif product_position > 0:
                product_orders.append(Order(product, min(order_depth.buy_orders.keys()), max(-product_position, sell_limit // 2)))
        return product_orders
    

    def set_and_get_channel_max_min(self, curr_mid_price, product, time_frame):
        if product not in self.channels:
            self.channels[product] = {}
        if time_frame not in self.channels[product]:
            self.channels[product][time_frame] = []   
        res = (min(self.channels[product][time_frame], default=0), max(self.channels[product][time_frame], default=0))
        self.channels[product][time_frame].insert(0, curr_mid_price)
        if len(self.channels[product][time_frame]) > time_frame:
            self.channels[product][time_frame].pop()
        return res
    
    # channel trading directional
    def channel_trade(self, order_depth, position, product, time_frame, position_limit):
        curr_mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
        product_position = position[product]
        buy_limit, sell_limit = position_limit - product_position, -position_limit - product_position
        product_orders: list[Order] = []
        # tuple (channel min, channel max)
        channel_min_max = self.set_and_get_channel_max_min(curr_mid_price, product, time_frame)
        logger.print("channel min max ", channel_min_max)
        # logger.print("curr mid price", curr_mid_price)
        if len(self.channels[product][time_frame]) == time_frame:
            if curr_mid_price < channel_min_max[0] and sell_limit:
                product_orders.append(Order(product, min(order_depth.buy_orders.keys()), max(sell_limit, self.exponential_sell_amount)))
                self.exponential_sell_amount *= 20
            elif curr_mid_price > channel_min_max[1] and buy_limit:
                product_orders.append(Order(product, max(order_depth.sell_orders.keys()), min(self.exponential_buy_amount, buy_limit)))
                self.exponential_buy_amount *= 20
            else:
                self.exponential_buy_amount, self.exponential_sell_amount = 1, -1
        
        return product_orders

    
    # directional strategy
    def swing_off_sma(self, order_depth, position, product, position_limit):
        product_position = position[product]
        product_orders: list[Order] = []
        buy_limit, sell_limit = position_limit - product_position, -position_limit - product_position

        curr_mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
        sma250 = self.set_and_get_sma(curr_mid_price, product, 250)
        sma10 = self.set_and_get_sma(curr_mid_price, product, 10)
        sma_diff = sma250 - sma10
        if sma_diff > 0:
            if len(self.last_sma_diffs) == 5:
                if self.last_sma_diffs[0] < 0:
                    # sma10 crossing under sma250 -> sell signal
                    product_orders.append(Order(product, min(order_depth.buy_orders.keys()), sell_limit // 2))
                    self.last_sma_diffs = []
            elif len(self.last_sma_diffs) > 0:
                if self.last_sma_diffs[0] < 0:
                    self.last_sma_diffs = []
                elif self.last_sma_diffs[0] > 0:
                    self.last_sma_diffs.append(sma_diff)
            else:
                self.last_sma_diffs.append(sma_diff)
        elif sma_diff < 0:
            if len(self.last_sma_diffs) == 5:
                if self.last_sma_diffs[0] > 0:
                    # sma10 crossing over sma250 -> buy signal
                    product_orders.append(Order(product, max(order_depth.sell_orders.keys()), buy_limit // 2))
                    self.last_sma_diffs = []
            elif len(self.last_sma_diffs) > 0:
                if self.last_sma_diffs[0] > 0:
                    self.last_sma_diffs = []
                elif self.last_sma_diffs[0] < 0:
                    self.last_sma_diffs.append(sma_diff)
            else:
                self.last_sma_diffs.append(sma_diff)

        return product_orders

    def order_from_last_price(self, order_depth, position, product, spread, position_limit) -> list[Order]:
        product_position = position[product]
        product_orders: list[Order] = []
        buy_limit, sell_limit = position_limit - product_position, -position_limit - product_position
        # skew = product_position * -0.1

        curr_mid_price = (max(order_depth.sell_orders.keys()) + min(order_depth.buy_orders.keys()))/2

        # mean = self.find_short_term_means("BANANA", order_depth, 10)

        product_orders.append(Order(product, curr_mid_price - spread, buy_limit))
        product_orders.append(Order(product, curr_mid_price + spread, sell_limit))
        return product_orders
    
    def generate_pearls_order(self, position, order_depth) -> List[Order]:
        pearls_position = position["PEARLS"]
        product_orders: list[Order] = []
        buy_limit, sell_limit = 20 - pearls_position, -20 - pearls_position
        buy_amount, sell_amount = 0, 0
        buy_orders, sell_orders = order_depth.buy_orders, order_depth.sell_orders
        # product_orders.append(Order("PEARLS", 9998, buy_limit))
        # product_orders.append(Order("PEARLS", 10002, sell_limit))
        # product_orders.append(Order("PEARLS", 10000, -pearls_position))
        for k, v in buy_orders.items():
            if k >= 10001:
                product_orders.append(Order("PEARLS", k, -v))
                sell_amount -= v
        for k, v in sell_orders.items():
            if k <= 9999:
                product_orders.append(Order("PEARLS", k, -v))
                buy_amount += -v
        if 10000 in buy_orders and pearls_position > 0:
            product_orders.append(Order("PEARLS", 10000, -1 * min(buy_limit - buy_amount, pearls_position, buy_orders[10000])))
            sell_amount -= min(buy_limit - buy_amount, pearls_position, buy_orders[10000])
        if 10000 in sell_orders and pearls_position < 0:
            product_orders.append(Order("PEARLS", 10000, -1 * max(sell_limit - sell_amount, pearls_position, sell_orders[10000])))
            buy_amount += -max(sell_limit - sell_amount, pearls_position, sell_orders[10000])

        product_orders.append(Order("PEARLS", 9996.5, buy_limit - buy_amount))
        product_orders.append(Order("PEARLS", 10003.5, sell_limit - sell_amount))
        # logger.print("PEARL ORDERS: ", product_orders)
        # logger.print("buy limit %d, buy amount %d, sell limit %d, sell amount %d", buy_limit, buy_amount, sell_limit, sell_amount)
        return product_orders
    
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell product_orders for all symbols as an input,
        and outputs a list of product_orders to be sent
        """
        # Initialize the method output dict as an empty dict
        orders = {}
        fair_price = None
        position = state.position
        product_orders: list[Order] = []
        logger.print("__________________________")
        logger.print("__________________________")
        logger.print("\n")
        logger.print("position: ", position)
        logger.print("own trades: ", state.own_trades)
        logger.print("market trades: ", state.market_trades)

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():
            logger.print(".")
            logger.print("product: ", product)
            order_depth: OrderDepth = state.order_depths[product]

            if product not in position.keys():
                position[product] = 0


            # New product
            if product not in self.long_term_means.keys():
                self.long_term_means[product] = [0, 0]
                self.short_term_means[product] = [0, []]
            
            
            
            fair_price: int = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
            # product_orders: list[Order] = self.order_at_order_limit(fair_price, order_depth, order_limit, product)

            if product == "PEARLS":
                product_orders = self.generate_pearls_order(position, order_depth)
            elif product == "BANANAS":
                product_orders = self.order_from_last_price(order_depth, position, product, 2, self.position_limit_bananas)
            elif product == "COCONUTS":
                product_orders = self.channel_trade(order_depth, position, product, 50, self.position_limit_coconuts)
            elif product == "PINA_COLADAS":
                product_orders = self.channel_trade(order_depth, position, product, 50, self.position_limit_pina_coladas)
                        
            logger.print("buy product_orders: ", order_depth.buy_orders)
            logger.print("sell order: ", order_depth.sell_orders)
            logger.print("fair price: ", fair_price)
            logger.print("__________________________")
            logger.print("QUOTES: ", product_orders)       

            orders[product] = product_orders

        logger.flush(state, orders)
        return orders


t: Trader = Trader()
order_depths = OrderDepth()
state = TradingState = TradingState(100, {}, {'sym':order_depths, 'bananas':order_depths}, {}, {}, {'sym':-3}, {})
#t.run(state)