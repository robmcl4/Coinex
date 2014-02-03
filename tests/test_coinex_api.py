"""
test_coinex_api.py

Test the coinex API
NOTE: requires active credentials in the config file
"""

from decimal import *
import os
import sys
import unittest

_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _path not in sys.path:
    sys.path.append(_path)

import coinex_api


class TestAPIFunctions(unittest.TestCase):

    def set_up(self):
        pass

    def test_config_load(self):
        # do this twice to test memoization
        conf = coinex_api._get_config()
        conf = coinex_api._get_config()

        self.assertTrue('Credentials' in conf, 'Config should have credentials')
        self.assertTrue('Key' in conf['Credentials'], 'Config should have key')
        self.assertTrue(
            'Secret' in conf['Credentials'],
            'Config should have secret'
        )

    def test_get_currencies(self):
        curr = coinex_api.currencies()
        self.assertTrue(
            isinstance(
                curr,
                list
            ),
            'currencies should be a list'
        )

    def test_get_trade_pairs(self):
        tp = coinex_api.trade_pairs()
        self.assertTrue(
            isinstance(
                tp,
                list
            ),
            'trade pairs should be a list'
        )

    def test_get_order_status(self):
        ords = coinex_api.orders(2)
        self.assertTrue(
            isinstance(
                ords,
                list
            ),
            'orders should be a list'
        )

    def test_get_last_trades(self):
        trds = coinex_api.last_trades(2)
        self.assertTrue(
            isinstance(
                trds,
                list
            ),
            'last trades should be a list'
        )

    def test_get_balances(self):
        bal = coinex_api.balances()
        self.assertTrue(
            isinstance(
                bal,
                list
            ),
            'last trades should be a list'
        )

    def test_get_open_orders(self):
        ords = coinex_api.open_orders()
        self.assertTrue(
            isinstance(
                ords,
                list
            )
        )

if __name__ == '__main__':
    unittest.main()
