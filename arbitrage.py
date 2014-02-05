"""
arbitrage.py

Check for arbitrage opportunities
"""

from models import *
from decimal import *
import ascii_art_spinner
import sys

TRANSAC_FEE = 0.002


class SmartExchange(Exchange):
    """
    Defines a SmartExchange, which can tell the current trading price
    via a weighted average
    """

    def __init__(self, exc):
        """
        Make a new SmartExchange around the given exchange
        """
        self._loaded = exc._loaded
        self.id = exc.id
        self.from_currency = exc.from_currency
        self.to_currency = exc.to_currency

    def get_orders(self):
        """
        Memoize getting the orders
        """
        if hasattr(self, '_orders'):
            return self._orders
        self._orders = super().get_orders()
        return self._orders

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
        raise ValueError('Unsupported currency for this exchange')

    def convert_to_other(self, amt, target_cur):
        """
        Convert the given amount of coin to the target currency using the most
        fiar trade, returns the amount of the new currency
        """
        amt = Decimal(amt)
        if target_cur == self.to_currency:
            return amt / self.get_best_offer(target_cur).rate
        elif target_cur == self.from_currency:
            return amt * self.get_best_offer(target_cur).rate
        else:
            raise ValueError('Unsupported currency for this exchanges')


class ArbitrageChain:
    """
    Defines the series of exchanges through which an arbitrage can be run
    """

    def __init__(self, ex1, ex2, ex3):
        self._roi = None
        self.ex1 = ex1
        self.ex2 = ex2
        self.ex3 = ex3

        self.cur1 = ex1.from_currency
        self.cur2 = ex1.to_currency
        if ex2.to_currency == ex1.to_currency:
            self.cur3 = ex2.from_currency
        else:
            self.cur3 = ex2.to_currency

    def get_roi(self):
        """
        Get the return on investment
        NOTE: 100% is returned as Decimal(1.0)
        """
        if self._roi is not None:
            return self._roi
        tfee = Decimal(1 - TRANSAC_FEE)
        # we are starting with 1 unit of ex1.from_currency
        amt = Decimal(1)
        # now convert to ex1.to_currency
        amt = (self.ex1.convert_to_other(amt, self.cur2)) * tfee
        # now convert to ex2.to_currency
        amt = (self.ex2.convert_to_other(amt, self.cur3)) * tfee
        # now convert to ex3.to_currency
        amt = (self.ex3.convert_to_other(amt, self.cur1)) * tfee
        # let's see what we got back! return the ROI
        self._roi = Decimal(amt - Decimal(1))
        return self._roi

    def __str__(self):
        ret = ''
        ret += self.cur1.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur2.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur3.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur1.abbreviation.rjust(4)
        ret += ' ({0})%'.format(str(self.get_roi() * 100))
        return ret


def valid(exc, cur1, cur2=None, exclude=None, exclude_cur=None):
    """
    Find if the given exc satisfies currency 1
    (currency 2) (and is not exclude) (and currency is not exclude)
    """
    if exclude is not None and exc == exclude:
        return False
    curs = [exc.to_currency, exc.from_currency]
    if exclude_cur is not None and exclude_cur in curs:
        return False
    if cur2 is not None:
        return cur1 in curs and cur2 in curs
    return cur1 in curs


def get_chains():
    """
    Get a list of all arbitrage chains
    """
    excs = Exchange.get_all()
    ret = []
    for ex1 in excs:
        excld = ex1.from_currency
        viable1 = filter(
            lambda x: valid(x, ex1.to_currency, exclude=ex1, exclude_cur=excld),
            excs
        )
        for ex2 in viable1:
            if ex2.to_currency == ex1.to_currency:
                cur = ex2.from_currency
            else:
                cur = ex2.to_currency
            viable2 = filter(
                lambda x: valid(x, cur, ex1.from_currency, ex2),
                excs
            )
            for ex3 in viable2:
                ex1 = SmartExchange(ex1)
                ex2 = SmartExchange(ex2)
                ex3 = SmartExchange(ex3)
                ret.append(ArbitrageChain(ex1, ex2, ex3))
    return ret


def get_profitable_chains(len_cb=None, iter_cb=None):
    """
    Get  alist of all profitable arbitrage chains
    """
    chains = get_chains()
    if len_cb:
        len_cb(len(chains))
    for chain in chains:
        if iter_cb:
            iter_cb()
        if chain.get_roi() > 0:
            yield chain


def show_all():
    """
    Print out all possible arbitrages, regardless of profit
    """
    print("-------Getting All Chains-------")
    chains = get_chains()
    ascii_art_spinner.start(len(chains))
    for chain in chains:
        ascii_art_spinner.clear()
        print(str(chain))
        ascii_art_spinner.tick()
    ascii_art_spinner.clear()
    print('Found {0} arbitrage chains'.format(len(chains)))


def show_profitable():
    """
    Print out only profitable arbitrages
    """
    print("-------Getting Profitable Chains-------")
    chains = get_profitable_chains(
        len_cb=ascii_art_spinner.start,
        iter_cb=ascii_art_spinner.tick
    )
    n = 0
    for chain in list(chains):
        print(str(chain))
        n += 1
    print('Found {0} arbitrage chains'.format(n))


def main():
    if '--all' in sys.argv:
        show_all()
    else:
        show_profitable()


if __name__ == '__main__':
    main()
