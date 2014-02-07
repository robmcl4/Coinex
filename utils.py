"""
utils.py

General utilities for coinex
"""

import coinex_api
import models
import time


def wait_for_order_to_complete(order_id):
    """
    Block (repeatedly request status) of the given
    order_id until it is fulfilled.
    Returns the Order.
    """
    time.sleep(10)
    ordr = coinex_api.order_status(order_id)
    while not ordr['cancelled'] and not ordr['complete']:
        time.sleep(10)
        ordr = coinex_api.order_status(order_id)
    time.sleep(10)
    return models.Order(API_resp=ordr)
