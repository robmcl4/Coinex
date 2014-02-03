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
