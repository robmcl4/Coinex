"""
coin.py
"""

from decimal import *


class Balance:
    """
    A container for a balance of a given currency
    """

    def __init__(self, currency, amount):
        self.currency = currency
        self.amount = Decimal(amount)


class Currency:
    """
    A container for a currency
    """

    def __init__(self, currency_id, abbreviation, name):
        self.currency_id = int(currency_id)
        self.abbreviation = str(abbreviation)
        self.name = str(name)


class Exchange:
    """
    A container for an exchange
    """

    def __init__(self, trade_pair_id, from_currency, to_currency, orders=[]):
        """
        Construct a new exchange.
        from_currency: the Currency from which this is being transferred
        to_currency: the currency to which this is being transferred
        orders: a list of orders made on this exchange
        """
        self.trade_pair_id = int(trade_pair_id)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.orders = orders


class Order:
    """
    A container for an order
    """

    def __init__(self, order_id, exchange, bid, bal):
        """
        Construct a new order
        exchange: an Exchange on which this order was placed
        bid: true if this is a bid(buy), false for ask(sell)
        bal: a Balance object representing the balance on this order
        """
        self.order_id = int(order_id)
        self.exchange = exchange
        self.bid = bool(bid)
        self.balance = bal


class Wallet:
    """
    A container to represent total currency held
    """

    def __init__(self, balances=[], orders=[]):
        self.balances = balances
        self.orders = orders
