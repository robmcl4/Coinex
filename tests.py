import unittest
from decimal import *
import coinex_api
import models


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


class TestModels(unittest.TestCase):

    def set_up(self):
        pass

    def test_balance(self):
        curr = models.Currency(10, 'BTC', 'Bitcoin')
        bal = models.Balance(curr, '10')
        self.assertTrue(isinstance(bal.id, int), 'balance should be an int')
        bal2 = models.Balance(curr, '11')
        self.assertTrue(bal.id != bal2.id, 'balance ids should not be equal')
        self.assertTrue(bal.amount == Decimal('10'), 'amount should match')
        self.assertTrue(bal.currency == curr, 'currency should match')

    def test_currency(self):
        curr = models.Currency(10, 'NMC', 'Namecoin')
        self.assertTrue(curr.id == 10, 'ID should be 10')
        self.assertTrue(
            curr.abbreviation == 'NMC',
            'abbreviation should be NMC'
        )
        self.assertTrue(curr.name == 'Namecoin', 'Name should be Namecoin')
        self.assertTrue(curr == curr, 'Equality should work')
        self.assertFalse(curr != curr, 'Not equals should work')


if __name__ == '__main__':
    unittest.main()
