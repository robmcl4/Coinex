"""
utils.py

General utilities for coinex
"""

import coinex_api


def wait_for_order_to_complete(order_id):
    """
    Block (repeatedly request status) of the given
    order_id until it is fulfilled
    """
    ordr = coinex_api.order_status(order_id)
    while not order.cancelled and not order.complete:
        ordr = coinex_api.order_status(order_id)
