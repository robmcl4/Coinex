"""
models.py
Contains models for the coinex API
"""

from decimal import *
import coinex_api


# set the decimal precision to 8
getcontext().prec = 8


class Balance:
    """
    A container for a balance of a given currency
    Attributes:
        currench: the Currency
        amount: a Decimal, the amount of currency
    Balance.get_own() : get a list of all own balances
    """

    next_id = 0

    def __init__(self, currency, amount):
        """
        Create a new Balance object.
        currency: either a currency object or an id
        amount: the amount, either a numeric or a string that parses to numeric
        """
        self.id = Balance.next_id
        Balance.next_id += 1
        if isinstance(currency, int):
            cur = Currency.get(currency)
            if cur is None:
                raise ValueError("currency id was not valid")
            self.currency = cur
        elif isinstance(currency, Currency):
            self.currency = currency
        else:
            raise ValueError(
                "currency was not valid, should be int or Currency"
            )
        self.amount = Decimal(amount)

    def __eq__(self, other):
        return isinstance(other, Balance) and other.id == self.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def get_own(cls):
        """
        Get all own balances
        """
        bals = coinex_api.balances()
        ret = []
        for bal in bals:
            curr = Currency.get(bal['currency_id'])
            amt = Decimal(bal['amount']) / pow(10, 8)
            b = Balance(curr, amt)
            ret.append(b)
            registry.put(b)
        return ret


class Currency:
    """
    A container for a currency
    Attributes:
        id: the currency ID
        abbreviation: the short name (ie 'BTC')
        name: the long name (ie 'Bitcoin')
    Currency.get(id_)  : get a currency that corresponds with the given ID
    Currency.get_all() : get all currencies available
    """

    _loaded = False

    def __init__(self, currency_id, abbreviation, name):
        self.id = int(currency_id)
        self.abbreviation = str(abbreviation)
        self.name = str(name)

    def __eq__(self, other):
        return isinstance(other, Currency) and other.id == self.id

    def __ne__(self, other):
        return not (self.__eq__(other))

    @classmethod
    def _refresh(cls):
        """
        Refresh all currencies, reloading from the API
        """
        registry.delete_all(cls)
        curs = coinex_api.currencies()
        for cur in curs:
            curncy = Currency(cur['id'], cur['name'], cur['desc'])
            registry.put(curncy)
        cls._loaded = True

    @classmethod
    def get(cls, id_):
        if not cls._loaded:
            cls._refresh()
        id_ = int(id_)
        return registry.get(Currency, id_)

    @classmethod
    def get_all(cls):
        """
        Returns a generator for all objects
        """
        if not cls._loaded:
            cls._refresh()
        return registry.get_all(Currency)


class Exchange:
    """
    A container for an exchange
    Attributes:
        id: the trade_pair_id
        from_currency: the Currency from which this trades (ie Bitcoin)
        to_currency: the Currency to which this trades (ie Mooncoin)
        get_orders() : get a list of all orders
        get_recent_trades() : get a list of recently executed trades
    Exchange.get(int_): get the Exchange for this ID
    Exchange.get_all(): get all Exchanges available
    """

    _loaded = False

    def __init__(self, trade_pair_id, from_currency, to_currency):
        """
        Construct a new exchange.
        from_currency: the Currency from which this is being transferred,
                       or the id of it
        to_currency: the currency to which this is being transferred,
                     or the id of it
        orders: a list of orders made on this exchange
        """
        self.id = int(trade_pair_id)

        if isinstance(from_currency, int):
            cur = Currency.get(from_currency)
            if cur is None:
                raise ValueError("The from id is invalid")
            self.from_currency = cur
        elif isinstance(from_currency, Currency):
            self.from_currency = from_currency
        else:
            raise ValueError("The from_currency was invalid")

        if isinstance(to_currency, int):
            cur = Currency.get(to_currency)
            if cur is None:
                raise ValueError("The to id is invalid")
        elif isinstance(to_currency, Currency):
            self.to_currency = to_currency
        else:
            raise ValueError("The to_currency was invalid")

    def get_orders(self):
        """
        Load / get all orders for the current exchange
        """
        # remove old ones if needed
        ords = coinex_api.orders(self.id)
        ret = []
        for order in ords:
            bal = Balance(
                self.to_currency,
                Decimal(order['amount']) / pow(10, 8)
            )
            o = Order(
                order['id'],
                self,
                order['bid'],
                bal
            )
            registry.put(bal)
            registry.put(o)
            ret.append(o)
        return ret

    def get_recent_trades(self):
        """
        Load / get all recent trades for this exchange
        """
        ords = coinex_api.last_trades(self.id)
        ret = []
        for order in ords:
            bal = Balance(
                self.to_currency,
                Decimal(order['amount']) / pow(10, 9)
            )
            o = Order(
                order['id'],
                self,
                order['bid'],
                bal
            )
            registry.put(bal)
            registry.put(o)
            ret.append(o)
        return ret

    @classmethod
    def _refresh(cls):
        """
        Refresh the registry's exchanges
        """
        if (cls._loaded):
            registry.delete_all(Exchange)
        excs = coinex_api.trade_pairs()
        for exc in excs:
            exchange = Exchange(
                exc['id'],
                Currency.get(exc['market_id']),
                Currency.get(exc['currency_id'])
            )
            registry.put(exchange)

        cls._loaded = True

    @classmethod
    def get(cls, id_):
        if not cls._loaded:
            cls._refresh()
        return registry.get(Exchange, id_)

    @classmethod
    def get_all(cls):
        if not cls._loaded:
            cls._refresh()
        return registry.get_all(Exchange)


class Order:
    """
    A container for an order
    Attributes:
        id: the order id
        exchange: the Exchange for this order
        bid: true if this is bid(buy), false for ask(sell)
        balalce: the Balance of this Order
    Order.get_own() : get all own orders
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

    @classmethod
    def get_own(cls):
        """
        Get all own orders
        """
        ords = coinex_api.open_orders()
        ret = []
        for ordr in ords:
            exc = Exchange.get(ordr['trade_pair_id'])
            bal = Balance(
                exc.to_currency,
                Decimal(ordr['amount']) / pow(10, 8)
            )
            ret.append(
                Order(
                    ordr['id'],
                    exc,
                    ordr['bid'],
                    bal
                )
            )
        return ret


class Wallet:
    """
    A container to represent total currency held
    """

    next_id = 0

    def __init__(self):
        self.id = Wallet.next_id
        Wallet.next_id += 1

    def get_balances(self):
        return Balance.get_own()

    def get_orders(self):
        return Order.get_own()


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

    def get_all(self, cls):
        """
        returns a list for all the objects in the registry
        """
        ret = []
        dct = self._dct[cls]
        if dct is not None:
            for key in dct:
                ret.append(dct[key])
        return ret

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

    def delete_all(self, cls):
        """
        Delete all of a certain class from the registry
        cls: the class to remove
        """
        self._dct[cls] = {}


registry = Registry()
