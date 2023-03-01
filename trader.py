from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order

class Trader:
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is weighted mean, second is total volume of that mean.
    long_term_means = {}
    # Dictionary with product as keys and means as value. Means are lists with 2 elements, first element is mean of middle price from last x days and second is queue of middle price of from past x days.
    short_term_means = {}

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
        # First element is buy limit, second is sell limit
        order_limit: tuple = (20 - product_position, -20 - product_position)
        orders: list[Order] = []
        buy_limit, sell_limit = order_limit[0], order_limit[1]
        skew = product_position * -0.5


        weighted_total, total_volume = 0, 0
        for price, volume in order_depth.buy_orders.items():
            weighted_total += price * volume
            total_volume += volume

        for price, volume in order_depth.sell_orders.items():
            weighted_total += price * -volume
            total_volume += -volume
        
        weighted_mean = weighted_total / total_volume

        orders.append(Order(product, weighted_mean - spread + skew, buy_limit))
        orders.append(Order(product, weighted_mean + spread + skew, sell_limit))
        
        return orders
    
    

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        fair_price = None
        position = state.position
        print("__________________________")
        print(".")
        print("position: ", position)

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
            
            
            
            # fair_price: int = self.find_short_term_means(product, order_depth) if product == "BANANAS" else self.find_long_term_means(product, order_depth)
            # orders: list[Order] = self.order_at_order_limit(fair_price, order_depth, order_limit, product)

            orders: list[Order] = self.order_from_last_price(order_depth, position, product, 1)

        

            print("buy orders: ", order_depth.buy_orders)
            print("sell order: ", order_depth.sell_orders)
            print("fair price: ", fair_price)
            print("__________________________")
            print("QUOTES: ", orders)
            print("__________________________")
                
                    

            result[product] = orders 
              
        print("own trades: ", state.own_trades)
        print(".")
        return result


t: Trader = Trader()
order_depths = OrderDepth()
state = TradingState = TradingState(100, {}, {'sym':order_depths, 'bananas':order_depths}, {}, {}, {'sym':-3}, {})
#t.run(state)
