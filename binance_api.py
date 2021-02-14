from binance.client import Client
from binance.enums import SIDE_BUY, ORDER_TYPE_LIMIT, SIDE_SELL, TIME_IN_FORCE_GTC
from binance.exceptions import BinanceAPIException
from threading import Thread
from time import sleep


class BinanceApi():
    
    def __init__(self, api_key, api_key_secret, notification_api) -> None:
        self.client = Client(api_key, api_key_secret)
        self.notify = notification_api

    def get_usdt_balance(self) -> float:
        """Returns the USDT balance of the account

        Returns:
            float: the USDT balance
        """
        return float(self.client.get_asset_balance(asset='USDT')['free'])

    def is_close_to_average_price(self, binance_pair:str, highest_buy_order:float, acceptance:float=0.006) -> bool:
        """Check if the current highest buy order price is close to the average price

        Args:
            binance_pair (str): the binance pair to check
            highest_buy_order (float): the current highest buy order price
            acceptance (float, optional): maximum difference between both prices. Defaults to 0.006.

        Returns:
            bool: true if the price is close
        """
        average_price = float(self.client.get_avg_price(symbol=binance_pair)['price'])
        return abs((average_price - highest_buy_order) / average_price) < acceptance

    def get_highest_buy_order(self, binance_pair:str) -> float:
        """Returns the highest buy order's price

        Args:
            binance_pair (str): the binance pair to check

        Returns:
            float: the highest buy order's price
        """
        return float(self.client.get_order_book(symbol=binance_pair, limit=5)['bids'][0][0])

    def place_buy_order(self, binance_pair:str, quantity:int, price:float, sell_price:float) -> None:
        """Try to place a buy order, and automaticaly a sell order when the buy order is completed

        Args:
            binance_pair (str): the binance pair to trade
            quantity (int): quantity of token to buy
            price (float): price to buy
            sell_price (float): price to sell
        """
        try:
            self.client.create_test_order(
                symbol=binance_pair,
                side=SIDE_BUY,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )

            self.notify.send('''buy order successfully placed :
                     binance_pair -- {}
                     quantity -- {}
                     price -- {}'''.format(binance_pair, quantity, price)
            )

            # Runs on another thread because it will wait until the buy order is completed
            thread = Thread(target=self.place_sell_order, args=(binance_pair, quantity, sell_price))
            thread.start()

        except BinanceAPIException as e:
            error_message = 'Cannot place buy order, check the binance pair and the quantity/price'
            if e.code == -1013:
                error_message += f'Not enough USDT to purchase ${binance_pair}'
            else:
                error_message += e

            self.notify.send(error_message)

    def place_sell_order(self, binance_pair:str, quantity:int, price:float) -> None:
        """Wait until the corresponding buy order is completed, and then try to place a sell order

        Args:
            binance_pair (str): the binance pair to trade
            quantity (int): quantity of token to sell
            price (float): price to sell
        """
        # waits for buy order to complete
        open_orders = self.client.get_open_orders(symbol=binance_pair)
        while len(open_orders) != 0: # if there is no open order, the buy order has been completed
            sleep(5)
            open_orders = self.client.get_open_orders(symbol=binance_pair)

        try:
            self.client.create_test_order(
                symbol=binance_pair,
                side=SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )

            self.notify.send('''sell order successfully placed :
                    binance_pair -- {}
                    quantity -- {}
                    sell_price -- {}'''.format(binance_pair, quantity, price)
            )

        except BinanceAPIException as e:
            self.notify.send('Cannot place sell order, check the binance pair and the quantity/price\n' + e)
