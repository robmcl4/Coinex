"""
market_cap.py

View the market capitalization of your coinex account.
Uses bitstamp prices.

OUTPUT:
xxxx BTC
xxxx USD
"""

import urllib.request
import models
import json
import sys
from decimal import *
from urllib.error import URLError, HTTPError


# set the decimal precision to 8
getcontext().prec = 8


def get_bitstamp_price():
    """
    Get the price from bitstamp.
    Returns in units of USD/BTC
    """
    req = urllib.request.urlopen('https://www.bitstamp.net/api/ticker/')
    ret = req.read().decode()
    ret = json.loads(ret)
    return Decimal(ret['last'])


def get_balances():
    """
    Memoized method to get a list of all balances.
    Also, for our purposes the total amount owned should include
    held, so do that.
    """
    if not hasattr(get_balances, '_balances'):
        bals = models.Wallet.get_balances()
        for bal in bals:
            bal.amount += bal.held
            bal.held = Decimal(0)
        get_balances._balances = bals
    return get_balances._balances


def get_amt_in_btc(bal):
    """
    Get a Decimal representing the BTC value of the given Balance.
    Converts using an exchange if needed.
    Bal - a models.Balance object
    """
    if bal.currency.abbreviation == 'BTC':
        return bal.amount
    # we need to convert. find an appropriate exchange
    for exchange in models.Exchange.get_all():
        to_correct = exchange.to_currency == bal.currency
        from_correct = exchange.from_currency.abbreviation == 'BTC'
        if to_correct and from_correct:
            break
    else:
        raise ValueError(
            'An exchange was not found that can convert {0} to BTC'.format(
                bal.currency.abbreviation
            )
        )
    ordr = exchange.get_highest_bid()
    return Decimal(bal.amount * ordr.rate)


def get_amt_in_usd(btc):
    """
    Get an amount in USD as a decimal
    btc - a Decimal representing bitcoin amount
    returns a Decimal of usd
    """
    return Decimal(btc * get_bitstamp_price())


def main():
    """
    Get the market cap!
    """
    btc = Decimal(0)
    try:
        for balance in get_balances():
            try:
                btc += get_amt_in_btc(balance)
            except ValueError:
                sys.stderr.write(
                    'WARNING: Cannot convert {0} to btc\n'.format(
                        balance.currency.abbreviation
                    )
                )
                # there isn't an exchange for this coin to BTC, ignore it
                pass
    except HTTPError as e:
        print("Error: status code {0}".format(e.code))
        print("Is coinex down?")
        return

    btc_str = '{0:12.8f}'.format(btc)
    print('{0} BTC'.format(btc_str))

    try:
        usd = get_amt_in_usd(btc)
    except HTTPError as e:
        print("Error: status code {0}".format(e.code))
        print("Is bitstramp down?")
        return

    usd_str = '{0:12.8f}'.format(usd)
    print('{0} USD'.format(usd_str))

if __name__ == '__main__':
    main()
