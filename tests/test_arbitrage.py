"""
test_arbitrage.py

Test the coinex arbitrage
"""

import os
import sys
import unittest

_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _path not in sys.path:
    sys.path.append(_path)

import coinex_api


if __name__ == '__main__':
    unittest.main()
