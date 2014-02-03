"""
models.py
Contains models for the coinex API
"""

from decimal import *


# set the decimal precision to 8
getcontext().prec = 8


class Balance:
    """
    A container for a balance of a given currency
    """

    next_id = 0

    def __init__(self, currency, amount):
        self.id = Balance.next_id
        Balance.next_id += 1
        self.currency = currency
        self.amount = Decimal(amount)

    def __eq__(self, other):
        return isinstance(other, Balance) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)


class Currency:
    """
    A container for a currency
    """

    def __init__(self, currency_id, abbreviation, name):
        self.id = int(currency_id)
        self.abbreviation = str(abbreviation)
        self.name = str(name)

    def __eq__(self, other):
        return isinstance(other, Currency) and other.id == self.id

    def __ne__(self, other):
        return not (self.__eq__(other))


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
        self.id = int(trade_pair_id)
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
        self.id = int(order_id)
        self.exchange = exchange
        self.bid = bool(bid)
        self.balance = bal


class Wallet:
    """
    A container to represent total currency held
    """

    next_id = 0

    def __init__(self, balances=[], orders=[]):
        self.id = Wallet.next_id
        Wallet.next_id += 1
        self.balances = balances
        self.orders = orders


class Registry:
    """
    Maintains a registry of all models
    """

    def __init__(self):
        self._dct = {}

    def get(self, model, id_):
        """
        Get a model from the registry by ID
        model: the class of model to get
        id_: the id of the model to get
        """
        if model in self._dct and id_ in self._dct[model]:
            return self._dct[model][id_]
        else:
            return None

    def put(self, model):
        """
        Put a model into the registry
        """
        cls = model.__class__
        if not (cls in self._dct):
            self._dct[cls] = {}
        self._dct[cls][model.id] = model

    def delete(self, obj, model=None):
        """
        Delete from the registry
        obj: either int, the object's id, or the model itself
        model: if an int supplied, this is the class of the model to delete
        returns the model that was deleted, or null if none was found
        """
        if isinstance(obj, int):
            if model in self._dct:
                if obj in self._dct[model]:
                    ret = self._dct[model][obj]
                    self._dct[model][obj] = None
                    return ret
        else:
            cls = obj.__class__
            if cls in self._dct:
                if obj.id in self._dct[cls]:
                    ret = self._dct[cls][obj.id]
                    self._dct[cls][obj.id] = None
                    return ret
        return None


registry = Registry()
