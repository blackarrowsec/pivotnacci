import ipaddress
import socket

from . import socks4
from . import socks5
from .initial_request import InitialRequest
from .error import SocksError


class SocksNegotiator(object):
    """Perform the Socks dialog with the client.
    """

    def __init__(self, broker_factory):
        self._broker_factory = broker_factory

    def negotiate(self, sock):
        return self._handle_socks(sock)

    def _handle_socks(self, sock):
        socks_request = InitialRequest.parse_stream(sock.makefile(mode='b'))

        version = socks_request.vn

        if version == socks4.VERSION:
            handler = Socks4Handler(sock, self._broker_factory)
        elif version == socks5.VERSION:
            handler = Socks5Handler(sock, self._broker_factory)
        else:
            raise SocksError(
                "Socks version {} not supported".format(socks_request.vn)
            )

        return handler.handle(socks_request)


class SocksHandler(object):
    """Base class for Socks4Handler and Socks5Handler
    """

    def __init__(self, sock, broker_factory):
        self._sock = sock
        self._broker_factory = broker_factory

    def handle(self, request):
        raise NotImplementedError()

    def _send_socket(self, raw):
        try:
            self._sock.sendall(raw)
        except Exception as ex:
            raise SocksError(
                "Error sending data to socks client = {}".format(ex))

    def _connect(self, ip, port):
        return self._broker_factory.connect(ip, port)


class Socks4Handler(SocksHandler):
    """Perform the Socks4 dialog with the client.
    """

    def handle(self, socks_request):
        if socks_request.cd == socks4.Commands.CONNECT:
            return self._handle_connect(socks_request)
        elif socks_request.cd == socks4.Commands.BIND:
            raise SocksError("Socks 4 BIND command not implemented")
        else:
            raise SocksError("Unknown Socks 4 command {}".format(
                socks_request.cd
            ))

    def _handle_connect(self, socks_request):
        ip = socks_request.dstip
        port = socks_request.dstport

        try:
            broker = self._connect(str(ip), port)
            response_code = socks4.ResponseCode.REQUEST_GRANTED
            return broker
        except Exception as ex:
            response_code = socks4.ResponseCode.REQUEST_REJECTED
            raise SocksError(
                "Error connectinng with remote host = {}".format(ex))
        finally:
            self._send_response(response_code, ip, port)

    def _send_response(self, response_code, ip, port):
        response = socks4.Response(cd=response_code, dstport=port, dstip=ip)
        self._send_socket(response.build())


class Socks5Handler(SocksHandler):
    """Perform the Socks5 dialog with the client.
    """

    def handle(self, auth_request):
        self._send_auth_response(socks5.Method.NO_AUTHENTICATION_REQUIRED)
        request = socks5.Request.parse_stream(self._sock.makefile(mode='b'))
        return self._handle_request(request)

    def _handle_request(self, request):
        cmd = request.cmd
        if cmd == socks5.Command.CONNECT:
            return self._handle_connect(request)
        else:
            raise SocksError(
                "Socks 5 command {} not implemented".format(cmd))

    def _handle_connect(self, request):
        dst_ip = self._resolve_address_type(request)

        try:
            broker = self._connect(dst_ip, request.dstport)
            response_code = socks5.Reply.SUCCESS
            return broker
        except Exception as ex:
            response_code = socks5.Reply.CONNECTION_REFUSED
            raise SocksError(
                "Error connectinng with remote host = {}".format(ex))
        finally:
            self._send_response(response_code, request)

    def _resolve_address_type(self, request):
        dst_ip = request.dstaddr
        if request.atyp == socks5.Atyp.DOMAIN_NAME:
            try:
                dst_ip = ipaddress.ip_address(socket.gethostbyname(dst_ip))
            except (socket.gaierror, socket.timeout):
                self._send_response(
                    socks5.Reply.ADDRESS_TYPE_NOT_SUPPORTED,
                    request
                )
                raise SocksError(
                    "Unable to resolv address name {}".format(request.dstaddr))

        return dst_ip

    def _send_response(self, rep, request):
        resp = socks5.Response(
            rep=rep,
            atyp=request.atyp,
            bndaddr=request.dstaddr,
            bndport=request.dstport
        )
        self._send_socket(resp.build())

    def _send_auth_response(self, method):
        resp = socks5.AuthResponse(method)
        self._send_socket(resp.build())
