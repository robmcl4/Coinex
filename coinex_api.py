"""
coinex-api.py

Contains helper functions for interacting with the coinex api.

Expects a config file in the same directory as this file named coinex.conf
Example config file structure:

[Credentials]
Key = <KEY HERE>
Secret = <SECRET HERE>

"""

import hmac
import configparser
import json
import urllib.request
import os


def _get_config():
    """
    Get the contents of the coinex.conf file
    from configparser.
    NOTE: this is memoized
    """
    # this has been memoized, return what we know
    if hasattr(_get_config, '_conf'):
        return _get_config._conf
    # hasn't been memoized, continue to load
    path = os.path.dirname(__file__)
    fname = os.path.join(path, 'coinex.conf')
    ret = configparser.ConfigParser()
    ret.read(fname)
    # memoize and return
    _get_config._conf = ret
    return ret


def _get_key():
    """
    Get the public key
    """
    return _get_config()['Credentials']['Key']


def _get_secret():
    """
    Get the secret key
    """
    return _get_config()['Credentials']['Secret']


def _make_request(page, data=None, method='GET', private=False):
    """
    Make a request to coinex.pw

    'page' is appended to the end of 'https://coinex.pw/api/v2/' to get the url
    'data', if supplied, is turned into JSON and given to the server
    'method' is the HTTP method to use
    'private' is true when this requires private authentication
    """
    url = "https://coinex.pw/api/v2/" + page
    if private:
        # if data was supplied convert it into a json string
        if data is not None:
            data = json.dumps(data)
        # construct the headers
        hmac = hmac.new(
            _get_secret(),
            msg=data,
            digestmod='sha-512'
        )
        headers = {
            'API-Key': _get_key(),
            'API-Secret': hmac.hexdigest()
        }
        # construct the request
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            nmethod=method
        )
    # else not private, just construct the request
    else:
        req = urllib.request.Request(
            url,
            method=method
        )
    rsp = urllib.urlopen(req)
    return json.loads(rsp.read())


def currencies():
    """
    Get a list of currencies from coinex.pw
    """
    return _make_request('currencies')
