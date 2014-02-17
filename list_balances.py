"""
list_balance.py

Because coinex sucks at showing you where your coin is
"""
import models


def main():
    """
    list all balances
    """
    for bal in models.Wallet.get_balances():
        amt = bal.amount + bal.held
        if amt > 0:
            print("{0} {1} ({2} held)".format(
                bal.currency.abbreviation,
                bal.amount + bal.held,
                bal.held
                )
            )


if __name__ == '__main__':
    main()
