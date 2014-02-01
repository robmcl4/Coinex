"""
coin.py
Contains a class defining a currency (coin).
"""


class Coin:
    """
    A container for a coin
    """

    def __init__(self, currency_id, currency_name, amount):
        self.currency_id = int(currency_id)
        self.currency_name = str(currency_name)
        self.amount = float(amount)