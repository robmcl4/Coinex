import os
import sys
from decimal import *
import unittest

_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _path not in sys.path:
    sys.path.append(_path)

import market_cap


class TestMarketCap(unittest.TestCase):

    def test_bitstamp_price(self):
        prc = market_cap.get_bitstamp_price()
        self.assertTrue(
            isinstance(prc, Decimal),
            'price should be a decimal'
        )
        self.assertTrue(
            prc > 1,
            'I bet bitcoin is more than $1/BTC yo'
        )

if __name__ == '__main__':
    unittest.main()
