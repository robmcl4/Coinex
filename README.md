Coinex
======

A collection of scripts for the coinex cryptocurrency trading platform.

Setup
-----

* Move the `coinex.conf.sample` file to `coinex.conf`
* Complete the config file with your credentials


Testing
-------

Run the `tests.py` file to perform unit tests.

Scripts
-------

* `list_balances.py` - list which coins you own
* `market_cap.py` - show your market cap (in BTC and USD via Bitstamp price)
* `arbitrage.py` - look for and perform arbitrage trades _NOTE:_ it is unlikely that you will find one

Reusables
---------

* `coinex_api.py` can be used in other projects
* `models.py` provides a more friendly set of python objects for interacting with the API
