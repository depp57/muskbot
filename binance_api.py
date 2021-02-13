from binance.client import Client
from binance.enums import SIDE_BUY, ORDER_TYPE_LIMIT, SIDE_SELL, TIME_IN_FORCE_GTC
from binance.exceptions import BinanceAPIException


class BinanceApi():
    
    def __init__(self, api_key, api_key_secret) -> None:
        self.client = Client(api_key, api_key_secret)

    def is_close_to_average_price(_, highest_buy_order:float, average_price:float, acceptance:float=0.005) -> bool:
        return abs((average_price -highest_buy_order) / average_price) < acceptance

    def get_highest_buy_order(self, binance_pair:str) -> float:
        return float(self.client.get_order_book(symbol=binance_pair, limit=5)['bids'][0][0])

    def get_average_price(self, binance_pair:str) -> float:
        return float(self.client.get_avg_price(symbol=binance_pair)['price'])

    def place_buy_order(self, binance_pair:str, quantity:int, price:float, sell_price:float) -> None:
        try:
            self.client.create_test_order(
                symbol=binance_pair,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )

            print('''buy order successfully placed :
                     binance_pair -- {}
                     quantity -- {}
                     price -- {}'''.format(binance_pair, quantity, price)
            )

            self.place_sell_order(binance_pair, quantity, sell_price)

        except BinanceAPIException as e:
            print('Cannot place buy order, check the binance pair and the quantity/price')
            print(e)

    def place_sell_order(self, binance_pair:str, quantity:int, price:float) -> None:
        open_orders = self.client.get_open_orders(symbol=binance_pair)
        if len(open_orders) == 0: # if there is no open order, the buy order has been completed
            try:
                self.client.create_test_order(
                    symbol=binance_pair,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_LIMIT,
                    timeInForce=TIME_IN_FORCE_GTC,
                    quantity=quantity,
                    price=price
                )

                print('''sell order successfully placed :
                     binance_pair -- {}
                     quantity -- {}
                     sell_price -- {}'''.format(binance_pair, quantity, price)
                )

            except BinanceAPIException as e:
                print('Cannot place sell order, check the binance pair and the quantity/price')
                print(e)
