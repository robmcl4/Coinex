"""
coinex-api.py

Contains helper functions for interacting with the coinex api.

Expects a config file in the same directory as this file named coinex.conf
Example config file structure:

[Credentials]
Key = <KEY HERE>
Secret = <SECRET HERE>


NOTE: the coinex api spec can be found here:
https://gist.github.com/erundook/8377222
"""

import hmac
from hashlib import sha512
import configparser
import json
import json.encoder
import urllib.request
from binascii import unhexlify
import os
from decimal import *


# set the decimal precision to 8
getcontext().prec = 8


def _get_config():
    """
    Get the contents of the coinex.conf file
    from configparser.
    NOTE: this is memoized
    """
    # this has been memoized, return what we know
    if hasattr(_get_config, '_conf'):
        return _get_config._conf
    # hasn't been memoized, continue to load
    path = os.path.dirname(__file__)
    fname = os.path.join(path, 'coinex.conf')
    ret = configparser.ConfigParser()
    ret.read(fname)
    # memoize and return
    _get_config._conf = ret
    return ret


def _get_key():
    """
    Get the public key
    """
    return _get_config()['Credentials']['Key']


def _get_secret():
    """
    Get the secret key
    """
    return _get_config()['Credentials']['Secret'].encode('utf8')


def _make_request(page, data=None, private=False):
    """
    Make a request to coinex.pw

    'page' is appended to the end of 'https://coinex.pw/api/v2/' to get the url
    'data', if supplied, is turned into JSON and given to the server
    'private' is true when this requires private authentication
    """
    url = "https://coinex.pw/api/v2/" + page
    headers = {
        'User-Agent': 'coinex-python-autosell',
        'Accept': 'application/json',
        'Content-type': 'application/json'
    }
    if private:
        # if data was supplied convert it into a json string
        if data is not None:
            json.encoder.FLOAT_REPR = lambda o: 'foo'
            data = json.dumps(data)
        # also format the data correctly
        else:
            data = ''
        data = data.encode('utf8')
        # construct the headers
        hmc = hmac.new(_get_secret(), digestmod=sha512)
        hmc.update(data)
        headers['API-Key'] = _get_key()
        headers['API-Sign'] = hmc.hexdigest()
        # construct the request
        req = urllib.request.Request(
            url,
            data=(data if data else None),
            headers=headers
        )
    # else not private, just construct the request
    else:
        req = urllib.request.Request(
            url,
            headers=headers
        )
    rsp = urllib.request.urlopen(req)
    return json.loads(rsp.read().decode())


def currencies():
    """
    Get a list of currencies from coinex.pw
    """
    return _make_request('currencies')['currencies']


def trade_pairs():
    """
    Get a list of all trade pairs from coinex.pw
    """
    return _make_request('trade_pairs')['trade_pairs']


def orders(trade_pair_id):
    """
    Get a list of open orders for the given trade pair
    trade_pair_id - the id of the trade pair to lookup
    """
    trade_pair_id = str(int(trade_pair_id))
    return _make_request('orders?tradePair=' + trade_pair_id)['orders']


def last_trades(trade_pair_id):
    """
    Get the last few trades for a given trade pair id
    trade_pair_id - the id of the trade pair to lookup
    """
    trade_pair_id = str(int(trade_pair_id))
    return _make_request('trades?tradePair=' + trade_pair_id)['trades']


def balances():
    """
    Get the balances for the current account
    """
    return _make_request('balances', private=True)['balances']


def open_orders():
    """
    Get a list of own open orders
    """
    return _make_request('orders/own', private=True)['orders']


def submit_order(trade_pair_id, amount, bid, rate):
    """
    Submit an order to coinex.pw

    trade_pair_id - the ID of pair to trade
    amount - how much to trade (decimal)
    bid - defines if order is bid (buy/true) or ask (sell/false)
    rate - Exchange rate (decimal)
    """
    trade_pair_id = int(trade_pair_id)
    bid = bool(bid)
    amount = int(Decimal(amount) * pow(10, 8))
    rate = int(Decimal(rate) * pow(10, 8))
    qry = {
        'trade_pair_id': trade_pair_id,
        'amount': amount,
        'bid': bid,
        'rate': rate
    }
    # set the root key to 'order' as per spec
    qry = {'order': qry}
    return _make_request('orders', data=qry, private=True)['order'][0]


def order_status(order_id):
    """
    Get the status of a given order ID
    """
    order_id = str(int(order_id))
    return _make_request('orders/' + order_id, private=True)['orders'][0]


def cancel_order(order_id):
    """
    Cancel a given order
    """
    order_id = str(int(order_id))
    return _make_request(
        'orders/' + order_id, + '/cancel',
        private=True
    )['orders'][0]
