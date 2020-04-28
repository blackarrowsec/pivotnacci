"""Includes the classes required to interpret and handle a Socks dialog with a
client.
"""

from .error import SocksError
from .negotiator import SocksNegotiator

__all__ = ["SocksError", "SocksNegotiator"]
