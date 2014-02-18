"""
models.py
Contains models for the coinex API
"""

from decimal import *
import coinex_api
from datetime import datetime


# set the decimal precision to 8
getcontext().prec = 8


class Balance:
    """
    A container for a balance of a given currency
    Attributes:
        currency: the Currency
        amount: a Decimal, the amount of currency
    Balance.get_own() : get a list of all own balances
    """

    next_id = 0

    def __init__(self, currency, amount, held=Decimal(0)):
        """
        Create a new Balance object.
        currency: either a currency object or an id
        amount: the amount, either a numeric or a string that parses to numeric
        held: an optional Decimal of how much is being held
        """
        self.held = Decimal(held)
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
            held = Decimal(bal['held']) / pow(10, 8)
            b = Balance(curr, amt, held=held)
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
            o = Order(API_resp=order)
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
            o = Order(API_resp=order)
            registry.put(o)
            ret.append(o)
        return ret

    def get_highest_bid(self):
        """
        Get order of the highest price that someone is bidding
        (willing to buy for)
        """
        ords = self.get_orders()
        ords = [ordr for ordr in ords if ordr.bid is True]
        best = max(ords, key=lambda x: x.rate)
        return best

    def get_lowest_ask(self):
        """
        Get order of the lowest price that someone is asking
        (willing to sell for)
        """
        ords = self.get_orders()
        ords = [ordr for ordr in ords if ordr.bid is False]
        best = min(ords, key=lambda x: x.rate)
        return best

    def get_best_offer(self, target_cur):
        """
        Get the best offer (order) for the given currency.
        NOTE: this may be highest bid or lowest ask
        """
        if target_cur == self.to_currency:
            return self.get_lowest_ask()
        elif target_cur == self.from_currency:
            return self.get_highest_bid()
        raise ValueError(
            'Unsupported currency for this exchange ' +
            target_cur.abbreviation
        )

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
        order_id: the order id
        exchange: the Exchange for this order
        bid: true if this is bid(buy), false for ask(sell)
        rate: Decimal rate at from_currency per to_currency
        amount: the amount of this Order
        filled: the amount of this order that has been filled
        cancelled: true if this order is cancelled
        complete: true if this order is completed
    Order.get_own() : get all own orders
    """

    def __init__(self,
                 API_resp=None,
                 order_id=None,
                 exchange=None,
                 bid=None,
                 amount=None,
                 filled=None,
                 cancelled=None,
                 complete=None,
                 rate=None,
                 created_at=None,
                 completed_at=None):
        """
        Construct a new order
        NOTE: either pass the response from coinex_api into API_resp or
        manually add each property
        """
        if API_resp is not None:
            order = API_resp
            self.id = order['id']
            self.exchange = Exchange.get(API_resp['trade_pair_id'])
            self.amount = Decimal(order['amount']) / pow(10, 8)
            self.rate = Decimal(order['rate']) / pow(10, 8)
            self.bid = order['bid']
            # if this is a pending order do this
            if 'filled' in order:
                self.filled = Decimal(order['filled']) / pow(10, 8)
                self.cancelled = order['cancelled']
                self.complete = order['complete']
                self.created_at = datetime.strptime(
                    order['created_at'],
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                )
                self.complete_at = None
            # else this order was already done, has some different keys
            else:
                self.filled = self.amount
                self.cancelled = False
                self.complete = True
                self.created_at = None
                self.completed_at = datetime.strptime(
                    order['created_at'],
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                )
        else:
            self.id = int(order_id)
            self.exchange = exchange
            self.bid = bool(bid)
            self.amount = amount
            self.rate = Decimal(rate)
            self.filled = filled
            self.cancelled = cancelled
            self.complete = complete
            self.created_at = created_at
            self.completed_at = completed_at

    @classmethod
    def get_own(cls):
        """
        Get all own orders
        """
        ords = coinex_api.open_orders()
        ret = []
        for ordr in ords:
            exc = Exchange.get(ordr['trade_pair_id'])
            amt = Decimal(ordr['amount']) / pow(10, 8)
            rate = Decimal(ordr['rate']) / pow(10, 8)
            ret.append(
                Order(
                    API_resp=ordr
                )
            )
        return ret

    def get_compliment(self, transac_fee=Decimal('0.002'), max_amt=None):
        """
        Get the compliment for this order which, when submitted,
        will fulfill the other order.
        """
        amt = (self.amount - self.filled) / Decimal(1 - transac_fee)
        if max_amt is not None:
            amt = min(max_amt, amt)
        other = Order(
            order_id=-1,
            exchange=self.exchange,
            amount=amt,
            bid=not self.bid,
            rate=self.rate
        )
        return other

    def submit(self):
        """
        Submit this order to the coinex api.
        Resets this object's properties to reflect
        the new ones reported by coinex_api, and
        also returns the parsed JSON returned by coinex
        """
        ordr = coinex_api.submit_order(
            trade_pair_id=self.exchange.id,
            amount=self.amount,
            bid=self.bid,
            rate=self.rate
        )
        self.__init__(API_resp=ordr)
        return ordr


class Wallet:
    """
    A container to represent total currency held
    """

    next_id = 0

    def __init__(self):
        self.id = Wallet.next_id
        Wallet.next_id += 1

    @classmethod
    def get_balances(cls):
        return Balance.get_own()

    @classmethod
    def get_orders(cls):
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
