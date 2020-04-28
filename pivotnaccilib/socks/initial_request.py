from .error import SocksError
from . import socks4
from . import socks5


class InitialRequest(object):
    """Helper to parse initial request and determine the Socks version.
    """

    @classmethod
    def parse_stream(cls, stream):
        version = ord(stream.read(1))

        if version == socks4.VERSION:
            return socks4.Request.parse_stream(stream)
        elif version == socks5.VERSION:
            return socks5.AuthRequest.parse_stream(stream)
        else:
            raise SocksError("Unknown version of socks: {}".format(version))
