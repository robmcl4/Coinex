"""
arbitrage.py

Check for arbitrage opportunities.

USAGE:  python arbitrage.py [--all]

--all   Display all arbitrage opportunities, not just profitable ones
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
            raise ValueError('Unsupported currency for this exchange')

    def max_currency(self, target_cur):
        """
        Returns a Decimal of the maximum amount of currency that can
        be exchanged into target_cur in units of the currency
        that is not target_cur
        NOTE: this accounts for the transaction fee
        """
        tfee = Decimal(1 - TRANSAC_FEE)
        if target_cur == self.to_currency:
            best_order = self.get_lowest_ask()
            orders = filter(
                lambda x: x.rate == best_order.rate,
                self.get_orders()
            )
            # we need to return in units of from_currency
            # balance.amount is in units of to_currency
            # order.rate is in to_currency per from_currency
            ret = Decimal(0)
            for order in orders:
                ret += order.amount / order.rate
            return ret * tfee
        elif target_cur == self.from_currency:
            best_order = self.get_highest_bid()
            orders = filter(
                lambda x: x.rate == best_order.rate,
                self.get_orders()
            )
            # we need to return in units of to_currency
            # balance.amount is in units of to_currency
            # order.rate is in to_currency per from_currency
            ret = Decimal(0)
            for order in orders:
                ret += order.amount
            return ret * tfee
        raise ValueError('Unsupported currency for this exchange')


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

    def get_max_transfer(self):
        """
        Get the max that can be transferred through this chain
        returns in units of currency 1
        """
        tfee = Decimal(1 - TRANSAC_FEE)

        # max3 is currently in units of cur3, convert to cur1 backward
        max3 = self.ex3.max_currency(self.cur1)
        # max3 is now in units of cur2
        max3 = self.ex2.convert_to_other(max3, self.cur2) / tfee
        # max3 is now in units of cur1
        max3 = self.ex1.convert_to_other(max3, self.cur1) / tfee

        # max2 is currently in units of cur2, convert to cur1 backward
        max2 = self.ex2.max_currency(self.cur3)
        # max2 is now in units of cur1
        max2 = self.ex1.convert_to_other(max2, self.cur1) / tfee

        # max1 is currently in units of cur1
        max1 = self.ex1.max_currency(self.cur2)
        return min(max1, max2, max3)

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
        ret += ' ({0} {1})'.format(
            str(self.get_max_transfer()),
            self.cur1.abbreviation
        )

        ret += '\n'

        def describe_exchange(ex, to_currency):
            return '-> {0} {1}/{2}'.format(
                ex.get_best_offer(to_currency).rate,
                ex.to_currency.abbreviation,
                ex.from_currency.abbreviation
            )

        ret += describe_exchange(self.ex1, self.cur2) + '\n'
        ret += describe_exchange(self.ex2, self.cur3) + '\n'
        ret += describe_exchange(self.ex3, self.cur1)
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
        exld = ex1.from_currency
        viable1 = filter(
            lambda x: valid(x, ex1.to_currency, exclude=ex1, exclude_cur=exld),
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
    for chain in chains:
        ascii_art_spinner.clear()
        print(str(chain))
    print('Found {0} arbitrage chains'.format(len(chains)))


def show_profitable():
    """
    Print out only profitable arbitrages
    """
    print("-------Getting Profitable Chains-------")
    chains = get_profitable_chains()
    n = 0
    for chain in chains:
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
