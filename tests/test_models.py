"""
test_models.py

Test the models objects
"""

import unittest
import sys
import os
from decimal import *

_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _path not in sys.path:
    sys.path.append(_path)

import models


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

        bals = models.Balance.get_own()
        self.assertTrue(isinstance(bals, list), 'balances should be a list')

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

        curs = models.Currency.get_all()
        self.assertTrue(
            0 != len(curs),
            'List of currencies should not be empty'
        )
        self.assertTrue(
            isinstance(curs[0], models.Currency),
            'Currency should be a Currency'
        )

    def test_registry(self):
        reg = models.registry
        curr = models.Currency(10, 'NMC', 'Namecoin')
        bal = models.Balance(curr, 100)
        bal2 = models.Balance(curr, 20)
        reg.put(curr)
        reg.put(bal)
        reg.put(bal2)
        got_bal = reg.get(models.Balance, bal.id)
        self.assertTrue(
            got_bal == bal,
            'Balance should be equal'
        )
        got_bal = reg.get(models.Balance, bal2.id)
        self.assertTrue(
            bal2 == got_bal,
            'Balance 2 should be equal'
        )
        got_curr = reg.get(models.Currency, curr.id)
        self.assertTrue(
            curr == got_curr,
            'Currencies should be equal'
        )
        deleted = reg.delete(curr)
        self.assertTrue(deleted == curr, "should have deleted curr")
        got_curr = reg.get(models.Currency, curr.id)
        self.assertTrue(
            got_curr is None,
            'Should not fetch object after deletion'
        )

    def test_exchange(self):
        excs = models.Exchange.get_all()
        self.assertTrue(0 != len(excs), 'There should be more than 0 exchanges')
        self.assertTrue(
            isinstance(excs[0], models.Exchange),
            'List should have exchanges'
        )
        ex = excs[0]
        ords = ex.get_orders()
        self.assertTrue(0 != len(ords), 'There should be more than 0 orders')
        self.assertTrue(
            isinstance(ords[0], models.Order),
            'List should have orders'
        )
        ords = ex.get_recent_trades()
        self.assertTrue(0 != len(ords), 'There should be more than 0 orders 02')
        self.assertTrue(
            isinstance(ords[0], models.Order),
            'list should have orders 02'
        )

if __name__ == '__main__':
    unittest.main()
