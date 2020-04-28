from construct import Struct, \
    Byte, Const, Int16ub, Int32ub, RepeatUntil, StreamError
import ipaddress
from .error import SocksError

VERSION = 4


class Commands:
    """Available commands for Socks4 request
    """
    CONNECT = 1
    BIND = 2


class Request(object):
    """Parse the Socks4 request from the client.
    """
    SOCKS_4_REQUEST_STRUCT = Struct(
        "cd" / Byte,
        "dstport" / Int16ub,
        "dstip" / Int32ub,
        "userid" / RepeatUntil(lambda b, _1, _2: b == 0, Byte),
    )

    def __init__(self, cd, dstport, dstip, userid):
        self.vn = VERSION
        self.cd = cd
        self.dstport = dstport
        self.dstip = dstip
        self.userid = userid

    @classmethod
    def parse_stream(cls, stream):
        try:
            req = cls.SOCKS_4_REQUEST_STRUCT.parse_stream(stream)
            return cls(
                cd=req.cd,
                dstport=req.dstport,
                dstip=ipaddress.ip_address(req.dstip),
                userid=req.userid[:-1]
            )
        except StreamError as ex:
            raise ex
            raise SocksError("Error parsing socks 4 request")

    def __repr__(self):
        return repr(self.__dict__)


class ResponseCode(object):
    """Status codes to the Socks4 response.
    """
    REQUEST_GRANTED = 90
    REQUEST_REJECTED = 91
    REQUEST_REJECTED_NOT_CONNECT = 92
    REQUEST_REJECTED_ID_MISMATCH = 93


class Response(object):
    """Build the Socks4 response to the client.
    This message indicates if the connection was successful.
    """
    SOCKS_4_RESPONSE_STRUCT = Struct(
        "vn" / Const(0, Byte),
        "cd" / Byte,
        "dstport" / Int16ub,
        "dstip" / Int32ub,
    )

    def __init__(self, cd, dstport, dstip):
        self.cd = cd
        self.dstport = dstport
        self.dstip = dstip

    def build(self):
        return self.SOCKS_4_RESPONSE_STRUCT.build(dict(
            cd=self.cd,
            dstport=self.dstport,
            dstip=int(self.dstip)
        ))
