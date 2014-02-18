"""
arbitrage.py

Check for arbitrage opportunities.

USAGE:  python arbitrage.py [--all]

--all   Display all arbitrage opportunities, not just profitable ones
"""

from models import *
from decimal import *
import utils
import sys

# the coinex transaction fee
TRANSAC_FEE = 0.002
# the minimum amount of to_currency required for a transaction
MIN_TRANSAC = 0.01


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

    def get_best_offer(self, target_cur):
        """
        Memoize getting the best offer for a currency
        """
        if hasattr(self, '_best_offers'):
            if target_cur.id in self._best_offers:
                return self._best_offers[target_cur.id]
        else:
            self._best_offers = dict()
        ret = super().get_best_offer(target_cur)
        self._best_offers[target_cur.id] = ret
        return ret

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
            raise ValueError(
                'Unsupported currency for this exchange ' +
                target_cur.abbreviation
            )

    def is_enough(self, amt, cur):
        """
        Returns True if the given amt is enough to be traded.
        amt: a Decimal of the amount to check
        cur: the currency of amt
        Otherwise returns False
        """
        if cur == self.to_currency:
            return amt > MIN_TRANSAC
        elif cur == self.from_currency:
            new_amt = amt / self.get_best_offer(self.to_currency).rate
            return new_amt > MIN_TRANSAC
        else:
            raise ValueError("Invalid currency")

    def max_currency(self, target_cur):
        """
        Returns a Decimal of the maximum amount of currency that can
        be exchanged into target_cur in units of the currency
        that is not target_cur
        NOTE: this accounts for the transaction fee
        """
        tfee = Decimal(1 - TRANSAC_FEE)
        if target_cur == self.to_currency:
            # we need to end up with units of from_currency
            best_order = self.get_lowest_ask()
            # filter out non-asks
            orders = filter(
                lambda x: x.bid is False,
                self.get_orders()
            )
            # filter out orders not of the same rate
            # maybe multiple orders exist?
            orders = filter(
                lambda x: x.rate == best_order.rate,
                orders
            )
            # we need to return in units of from_currency
            # amount is in units of to_currency
            # order.rate is in from_currency per to_currency
            ret = Decimal(0)
            for order in orders:
                ret += (order.amount - order.filled) * order.rate
            return Decimal(ret * tfee)
        elif target_cur == self.from_currency:
            best_order = self.get_highest_bid()
            # filter out non-bids
            orders = filter(
                lambda x: x.bid is True,
                self.get_orders()
            )
            # filter out orders not of the same rate
            orders = filter(
                lambda x: x.rate == best_order.rate,
                orders
            )
            # we need to return in units of to_currency
            # balance.amount is in units of to_currency
            # order.rate is in from_currency per to_currency
            ret = Decimal(0)
            for order in orders:
                ret += order.amount - order.filled
            return Decimal(ret * tfee)
        raise ValueError(
            'Unsupported currency for this exchange ' +
            target_cur.abbreviation
        )


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
        elif ex2.from_currency == ex1.to_currency:
            self.cur3 = ex2.to_currency
        else:
            raise ValueError("Unsupported 2nd exchange combination")

        # verify the third exchange's validity
        ex3_curs = [ex3.to_currency, ex3.from_currency]
        if not self.cur1 in ex3_curs or not self.cur3 in ex3_curs:
            raise ValueError("Unsupported 3rd exchange combination")

    def get_roi(self):
        """
        Get the return on investment.
        Returns a Decimal of the ROI or None if this chain cannot be executed
        NOTE: 100% is returned as Decimal(1.0)
        NOTE: this is memoized
        """
        if self._roi is not None:
            return self._roi
        tfee = Decimal(1 - TRANSAC_FEE)
        # we are starting with 1 unit of ex1.from_currency
        amt = Decimal(1)

        # make sure it is enough to convert
        if not self.ex1.is_enough(amt, self.cur1):
            return None
        # now convert to cur2
        amt = (self.ex1.convert_to_other(amt, self.cur2)) * tfee

        # again make sure it is enough to convert
        if not self.ex2.is_enough(amt, self.cur2):
            return None
        # now convert to cur3
        amt = (self.ex2.convert_to_other(amt, self.cur3)) * tfee

        # again make sure it is enough to convert
        if not self.ex3.is_enough(amt, self.cur3):
            return None
        # now convert back to cur1
        amt = (self.ex3.convert_to_other(amt, self.cur1)) * tfee

        # let's see what we got back! return the ROI
        self._roi = Decimal(amt - Decimal(1))
        return self._roi

    def get_max_transfer(self):
        """
        Get the max that can be transferred through this chain
        returns in units of currency 1
        NOTE: this is memoized
        """
        if hasattr(self, '_max_transfer'):
            return self._max_transfer
        tfee = Decimal(1 - TRANSAC_FEE)

        # max3 is currently in units of cur3, convert to cur1 backward
        max3 = self.ex3.max_currency(target_cur=self.cur1)
        # max3 is now in units of cur2
        max3 = self.ex2.convert_to_other(amt=max3, target_cur=self.cur2) / tfee
        # max3 is now in units of cur1
        max3 = self.ex1.convert_to_other(amt=max3, target_cur=self.cur1) / tfee

        # max2 is currently in units of cur2, convert to cur1 backward
        max2 = self.ex2.max_currency(target_cur=self.cur3)
        # max2 is now in units of cur1
        max2 = self.ex1.convert_to_other(amt=max2, target_cur=self.cur1) / tfee

        # max1 is currently in units of cur1
        max1 = self.ex1.max_currency(target_cur=self.cur2)
        ret = min(max1, max2, max3)
        self._max_transfer = ret
        return ret

    def get_min_transfer(self):
        """
        Get the least amount of cur1 that can be put through
        the system
        NOTE: this is memoized
        """
        if hasattr(self, '_min_transfer'):
            return self._min_transfer

        tfee = Decimal(1 - TRANSAC_FEE)

        # get the minimum of cur1 we can trade
        if self.cur1 == self.ex3.to_currency:
            # min1 is in units of cur1, convert backward through the chain
            min1 = Decimal(MIN_TRANSAC)
            min1 = self.ex3.convert_to_other(amt=min1, target_cur=self.cur3)
            min1 /= tfee
            min1 = self.ex2.convert_to_other(amt=min1, target_cur=self.cur2)
            min1 /= tfee
            min1 = self.ex1.convert_to_other(amt=min1, target_cur=self.cur1)
            min1 /= tfee
        else:
            min1 = Decimal(0)

        if self.cur3 in [self.ex2.to_currency, self.ex3.to_currency]:
            min3 = Decimal(MIN_TRANSAC)
            min3 = self.ex2.convert_to_other(amt=min3, target_cur=self.cur2)
            min3 /= tfee
            min3 = self.ex1.convert_to_other(amt=min3, target_cur=self.cur1)
            min3 /= tfee
        else:
            min3 = Decimal(0)

        if self.cur2 in [self.ex1.to_currency, self.ex2.to_currency]:
            min2 = Decimal(MIN_TRANSAC)
            min2 = self.ex1.convert_to_other(amt=min2, target_cur=self.cur1)
            min2 /= tfee
        else:
            min2 = Decimal(0)
        ret = max(min1, min2, min3)
        self._min_transfer = ret
        return ret

    def can_execute(self):
        """
        Returns true if the user currently has some of the first currency and
        this chain's max is greater than the min.
        NOTE: this memoizes the wallet balances
        """
        if self.get_min_transfer() >= self.get_min_transfer():
            return False
        if not hasattr(ArbitrageChain, '_bals') or not ArbitrageChain._bals:
            ArbitrageChain._bals = Wallet.get_balances()
        for bal in ArbitrageChain._bals:
            if bal.currency == self.cur1 and bal.amount > 0:
                print("{0} {1}".format(bal.currency.abbreviation, bal.amount))
                return True
        return False

    def perform_chain_operation(self, amt, target_cur, exchange):
        """
        Trade the given amount (of not target_cur) over the exchange.
        Returns the amount of target_cur that we now have
        """
        tfee = Decimal(1 - Decimal(TRANSAC_FEE))

        from_cur = exchange.from_currency
        if exchange.from_currency == target_cur:
            from_cur = exchange.to_currency

        best = exchange.get_best_offer(target_cur)

        print('Buying {0} of {1}'.format(
            str(amt),
            target_cur.abbreviation
        ))

        # amount must always be in terms of the 'to_currency',
        # convert if needed
        if exchange.to_currency != from_cur:
            amt = self.ex1.convert_to_other(amt, target_cur)

        ordr = best.get_compliment(max_amt=amt)
        try:
            ordr.submit()
        except Exception as e:
            if hasattr(e, 'read'):
                print(e.read())
            raise e
        if (ordr.complete is not True):
            print("waiting for order to complete")
            ordr = utils.wait_for_order_to_complete(ordr.id)
        amt *= tfee
        print("now have {0} of {1}".format(
            str(amt),
            target_cur.abbreviation
        ))
        return amt

    def execute(self):
        """
        Perform the trades necessary to complete this chain
        """
        while True:
            try:
                amt = input("How much currency to use? ({0}) ".format(
                    self.cur1.abbreviation
                ))
                amt = Decimal(amt)
                break
            except InvalidOperation:
                print("Invalid amount. Enter again.")

        amt = self.perform_chain_operation(
            amt,
            self.cur2,
            self.ex1
        )
        amt = self.perform_chain_operation(
            amt,
            self.cur3,
            self.ex2
        )
        amt = self.perform_chain_operation(
            amt,
            self.cur1,
            self.ex3
        )
        # reset the record of balances
        ArbitrageChain._bals = None
        print("finished")

    def __str__(self):
        ret = ''
        ret += self.cur1.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur2.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur3.abbreviation.rjust(4)
        ret += ' -> '
        ret += self.cur1.abbreviation.rjust(4)
        roi = self.get_roi()
        if roi:
            ret += ' ({0})%'.format(str(roi * 100))
        else:
            ret += ' (Not Exchangeable)'
        ret += ' ({0} to {1} {2})'.format(
            str(self.get_max_transfer()),
            str(self.get_min_transfer()),
            self.cur1.abbreviation
        )

        ret += '\n'

        def describe_exchange(ex, to_currency):
            return '-> {0} {1}/{2}'.format(
                ex.get_best_offer(to_currency).rate,
                ex.from_currency.abbreviation,
                ex.to_currency.abbreviation
            )

        ret += describe_exchange(self.ex1, self.cur2) + '\n'
        ret += describe_exchange(self.ex2, self.cur3) + '\n'
        ret += describe_exchange(self.ex3, self.cur1)
        return ret


def offer_execute_chain(chain):
    """
    Ask the user if they would like to execute a given chain. If they
    answer positively, the chain is executed
    """
    answer = input("Would you like to execute this chain? (y/N) ")
    if answer.lower() in ['y', 'yes']:
        chain.execute()
    else:
        print("Not executing chain")


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
        roi = chain.get_roi()
        if roi and roi > 0:
            yield chain


def show_all():
    """
    Print out all possible arbitrages, regardless of profit
    """
    print("-------Getting All Chains-------")
    chains = get_chains()
    for chain in chains:
        print(str(chain))
        if chain.can_execute():
            offer_execute_chain(chain)
        else:
            print('This chain cannot be executed')
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
        if chain.can_execute():
            offer_execute_chain(chain)
        else:
            print('This chain cannot be executed')
        n += 1
    print('Found {0} arbitrage chains'.format(n))


def main():
    try:
        if '--all' in sys.argv:
            show_all()
        else:
            show_profitable()
    except KeyboardInterrupt:
        print("Exiting")

if __name__ == '__main__':
    main()
