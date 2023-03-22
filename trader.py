from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

class Trader:
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is weighted mean, second is total volume of that mean.
    long_term_means = {}
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is mean of middle price from last x days and second is queue of middle price of from past x days.
    short_term_means = {}

    # past order depths
    historical_order_depths = []

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

    def find_short_term_means(self, product: str, order_depth: OrderDepth) -> int:
        price_queue: List = self.short_term_means[product][1]

        weighted_mean, total_volume = 0, 0
        for price, volume in order_depth.buy_orders.items():
            weighted_mean += price * volume
            total_volume += volume

        for price, volume in order_depth.sell_orders.items():
            weighted_mean += price * -volume
            total_volume += -volume
        
        price_queue.append(weighted_mean / total_volume)
        self.short_term_means[product][0] += weighted_mean / total_volume
        if len(price_queue) > 15:
            self.short_term_means[product][0] -= price_queue[0]
            price_queue.pop(0)
        return self.short_term_means[product][0]/len(price_queue)

    # quotes the greatest possible volume on both buy and sell sides for a set spread
    def order_at_order_limit(self, fair_price, order_depth, position, product) -> list[Order]:
        order_limit: tuple = (20 - position[product], -20 - position[product])
        orders: list[Order] = []
        if fair_price and len(order_depth.sell_orders) != 0:
                buy_limit = order_limit[0]
                #print("BUY", product, str(buy_limit) + "x", fair_price - 1)
                orders.append(Order(product, fair_price - 1, buy_limit))
            
        # Selling
        if fair_price and len(order_depth.buy_orders) != 0:
            sell_limit = order_limit[1]
            #print("SELL", product, str(sell_limit) + "x", fair_price + 1)
            orders.append(Order(product, fair_price + 1, sell_limit))
        
        return orders

    def order_from_last_price(self, order_depth, position, product, spread) -> list[Order]:
        product_position = position[product]
        orders: list[Order] = []
        buy_limit, sell_limit = 20 - product_position, -20 - product_position
        # skew = product_position * -0.1

        weighted_total, total_volume = 0, 0
        for price, volume in order_depth.buy_orders.items():
            weighted_total += price * volume
            total_volume += volume

        for price, volume in order_depth.sell_orders.items():
            weighted_total += price * -volume
            total_volume += -volume
        
        weighted_mean = weighted_total / total_volume

        mid_price = (max(order_depth.sell_orders.keys()) + min(order_depth.buy_orders.keys()))/2

        orders.append(Order(product, mid_price - spread, buy_limit))
        orders.append(Order(product, mid_price + spread, sell_limit))
        return orders
    
    def generate_pearls_order(self, position, order_depth) -> List[Order]:
        pearls_position = position["PEARLS"]
        orders: list[Order] = []
        buy_limit, sell_limit = 20 - pearls_position, -20 - pearls_position
        buy_amount, sell_amount = 0, 0
        buy_orders, sell_orders = order_depth.buy_orders, order_depth.sell_orders
        # orders.append(Order("PEARLS", 9998, buy_limit))
        # orders.append(Order("PEARLS", 10002, sell_limit))
        # orders.append(Order("PEARLS", 10000, -pearls_position))
        for k, v in buy_orders.items():
            if k >= 10001:
                orders.append(Order("PEARLS", k, -v))
                sell_amount -= v
        for k, v in sell_orders.items():
            if k <= 9999:
                orders.append(Order("PEARLS", k, -v))
                buy_amount += -v
        if 10000 in buy_orders and pearls_position > 0:
            orders.append(Order("PEARLS", 10000, -1 * min(buy_limit - buy_amount, pearls_position, buy_orders[10000])))
            sell_amount -= min(buy_limit - buy_amount, pearls_position, buy_orders[10000])
        if 10000 in sell_orders and pearls_position < 0:
            orders.append(Order("PEARLS", 10000, -1 * max(sell_limit - sell_amount, pearls_position, sell_orders[10000])))
            buy_amount += -max(sell_limit - sell_amount, pearls_position, sell_orders[10000])

        orders.append(Order("PEARLS", 9996.5, buy_limit - buy_amount))
        orders.append(Order("PEARLS", 10003.5, sell_limit - sell_amount))
        print("PEARL ORDERS: ", orders)
        return orders
    
    # def update_historical_order_depths(self, curr_order_depth):
    #     self.historical_order_depths.insert(0, curr_order_depth)
    #     if len(self.historical_order_depths) > 10:
    #         self.historical_order_depths.pop()
            
    
    # def time_market(self, order_depth, position) -> List[Order]:
    #     orders = []
    #     buy_limit, sell_limit = 20 - position["BANANAS"], -20 - position["BANANAS"]
    #     historical_order_depths = self.historical_order_depths
    #     if len(historical_order_depths) > 1:
    #         last_order_depth = historical_order_depths[1]
    #         last_mid_price = (min(last_order_depth.sell_orders.keys()) + max(last_order_depth.buy_orders.keys()))/2
    #         curr_mid_price = (min(order_depth.sell_orders.keys()) + max(order_depth.buy_orders.keys()))/2
    #         # sell
    #         if curr_mid_price - last_mid_price >= 4:
    #             bid_price = max(order_depth.buy_orders.keys())
    #             orders.append(Order("BANANAS", bid_price, max(order_depth.buy_orders[bid_price], sell_limit)))
    #         # buy
    #         elif curr_mid_price - last_mid_price <= -4:
    #             bid_price = min(order_depth.sell_orders.keys())
    #             orders.append(Order("BANANAS", bid_price, min(order_depth.sell_orders[bid_price], buy_limit)))
        
    #     print("Banana orders ", orders)
    #     return orders


        

    
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        fair_price = None
        position = state.position
        orders: list[Order] = []
        print("__________________________")
        print(".")
        print("position: ", position)
        print("own trades: ", state.own_trades)
        print("market trades: ", state.market_trades)

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():
            print(".")
            print("product: ", product)
            order_depth: OrderDepth = state.order_depths[product]

            if product not in position.keys():
                position[product] = 0


            # New product
            if product not in self.long_term_means.keys():
                self.long_term_means[product] = [0, 0]
                self.short_term_means[product] = [0, []]
            
            
            
            fair_price: int = (max(order_depth.sell_orders.keys()) + min(order_depth.buy_orders.keys()))/2
            # orders: list[Order] = self.order_at_order_limit(fair_price, order_depth, order_limit, product)

            if product == "PEARLS":
                orders = self.generate_pearls_order(position, order_depth)
            elif product == "BANANAS":
                orders = self.time_market(order_depth, position)


            # self.update_historical_order_depths(order_depth)

                        
            print("buy orders: ", order_depth.buy_orders)
            print("sell order: ", order_depth.sell_orders)
            print("fair price: ", fair_price)
            print("__________________________")
            print("QUOTES: ", orders)       

            result[product] = orders 
        print(".")
        return result


t: Trader = Trader()
order_depths = OrderDepth()
state = TradingState = TradingState(100, {}, {'sym':order_depths, 'bananas':order_depths}, {}, {}, {'sym':-3}, {})
#t.run(state)
