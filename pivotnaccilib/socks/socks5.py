from construct import Struct, Switch, Error, PascalString, \
    Byte, Const, Int16ub, Int32ub, Array, StreamError, this

from .error import SocksError
import ipaddress

VERSION = 5


class AuthRequest(object):
    """Parse the authentication request of a Socks5 client.
    In this message the client specified the supported authentication methods.
    """
    SOCKS_5_AUTH_REQUEST = Struct(
        "nmethods" / Byte,
        "methods" / Array(this.nmethods, Byte),
    )

    def __init__(self, methods):
        self.vn = VERSION
        self.methods = methods

    @classmethod
    def parse_stream(cls, stream):
        try:
            req = cls.SOCKS_5_AUTH_REQUEST.parse_stream(stream)
            return cls(methods=req.methods)
        except StreamError:
            raise SocksError("Error parsing socks 5 request")

    def __repr__(self):
        return repr(self.__dict__)


class Method(object):
    """The Socks5 authentication methods
    """
    NO_AUTHENTICATION_REQUIRED = 0
    GSSAPI = 1
    USERNAME_PASSWORD = 2
    NO_ACCEPTABLE_METHODS = 0xff


class AuthResponse(object):
    """Build the authentication reply to a Socks5 client.
    In the reply it is specified the authentication mechanism choose by the
    server.
    """
    SOCK_5_AUTH_RESPONSE = Struct(
        "vn" / Const(5, Byte),
        "method" / Byte
    )

    def __init__(self, method):
        self.method = method

    def build(self):
        return self.SOCK_5_AUTH_RESPONSE.build(dict(
            method=self.method
        ))


IP_4_Address = Int32ub
IP_6_Address = Array(16, Byte)
DOMAIN_NAME = PascalString(Byte, "ascii")


class Atyp(object):
    """The address types supported by Socks5
    """
    IP_V4 = 1
    DOMAIN_NAME = 3
    IP_V6 = 4


class Command(object):
    """The available commands of Socks5
    """
    CONNECT = 1
    BIND = 2
    UDP_ASSOCIATE = 3


class Request(object):
    """Parse the Socks5 request from a client.
    This message indicates the target address and port  of the connection.
    """
    REQUEST = Struct(
        "ver" / Const(VERSION, Byte),
        "cmd" / Byte,
        "rsv" / Byte,
        "atyp" / Byte,
        "dstaddr" / Switch(this.atyp, {
            Atyp.IP_V4: IP_4_Address,
            Atyp.DOMAIN_NAME: DOMAIN_NAME,
            Atyp.IP_V6: IP_6_Address
        }, default=Error),
        "dstport" / Int16ub,
    )

    def __init__(self, cmd, atyp, dstaddr, dstport):
        self.ver = VERSION
        self.cmd = cmd
        self.atyp = atyp
        self.dstaddr = dstaddr
        self.dstport = dstport

    @classmethod
    def parse_stream(cls, stream):
        try:
            req = cls.REQUEST.parse_stream(stream)

            addr = req.dstaddr
            if req.atyp == Atyp.IP_V4 or req.atyp == Atyp.IP_V6:
                addr = ipaddress.ip_address(addr)

            return cls(
                cmd=req.cmd,
                atyp=req.atyp,
                dstaddr=addr,
                dstport=req.dstport
            )
        except StreamError:
            raise SocksError("Error parsing socks 5 request")


class Reply(object):
    """The reply codes of Socks5
    """
    SUCCESS = 0
    SOCKS_SERVER_FAILURE = 1
    CONNECTION_NOT_ALLOWED = 2
    NETWORK_UNREACHABLE = 3
    HOST_UNREACHABLE = 4
    CONNECTION_REFUSED = 5
    TTL_EXPIRED = 6
    COMMAND_NOT_SUPPORTED = 7
    ADDRESS_TYPE_NOT_SUPPORTED = 8


class Response(object):
    """Class to build the Socks 5 reply to the client.
    This message indicates the state of the conection with the target.
    """
    RESPONSE = Struct(
        "ver" / Const(VERSION, Byte),
        "rep" / Byte,
        "rsv" / Byte,
        "atyp" / Byte,
        "bndaddr" / Switch(this.atyp, {
            Atyp.IP_V4: IP_4_Address,
            Atyp.DOMAIN_NAME: DOMAIN_NAME,
            Atyp.IP_V6: IP_6_Address
        }, default=Error),
        "bndport" / Int16ub,
    )

    def __init__(self, rep, atyp, bndaddr, bndport):
        self.rep = rep
        self.atyp = atyp
        self.bndaddr = bndaddr
        self.bndport = bndport

    def build(self):
        addr = self.bndaddr
        if self.atyp == Atyp.IP_V4 or self.atyp == Atyp.IP_V6:
            addr = int(addr)

        return self.RESPONSE.build(dict(
            rep=self.rep,
            rsv=0,
            atyp=self.atyp,
            bndaddr=addr,
            bndport=self.bndport
        ))
