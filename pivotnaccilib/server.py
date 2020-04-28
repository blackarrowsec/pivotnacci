"""Classes to handle connections from clients and retransmit the data to the
agents.
"""

from threading import Thread
import socket
from time import sleep
import socketserver

from .agent import AgentError
from .socks import SocksNegotiator, SocksError

import logging

logger = logging.getLogger(__name__)


class SocksServer(socketserver.ThreadingTCPServer):
    """The server which listen for incoming socks requests
    """

    def __init__(
            self,
            listen_addr,
            listen_port,
            agent_connection_dispatcher,
            agent_polling_interval
    ):
        connection_handler = SocksConnectionHandler
        connection_handler.init_handler(
            agent_connection_dispatcher,
            agent_polling_interval
        )

        super(SocksServer, self).__init__(
            (listen_addr, listen_port),
            connection_handler
        )


class SocksConnectionHandler(socketserver.BaseRequestHandler):
    """Handles the socks handshake and create and creates a ClientHandler to
    redirect the connections
    """
    _socks_negotiator = None
    _agent_polling_interval = 0.1

    @classmethod
    def init_handler(cls, agent_connection_dispatcher, agent_polling_interval):
        cls._socks_negotiator = SocksNegotiator(agent_connection_dispatcher)
        cls._agent_polling_interval = agent_polling_interval

    def handle(self):
        logger.info(
            "Request from %s:%s",
            self.client_address[0],
            self.client_address[1]
        )
        sock = self.request
        try:
            broker = self._socks_negotiator.negotiate(sock)
            client_handler = ClientHandler(
                sock,
                broker,
                self._agent_polling_interval
            )
            client_handler.handle()
        except SocksError as ex:
            logger.error("Socks negotiation failed: %s", str(ex))
        except AgentError as ex:
            logger.error("Agent error: %s", str(ex))
        except Exception as ex:
            logger.error("Unknown error: %s", str(ex))
        finally:
            logger.info("Closing socket with %s:%s",
                        self.client_address[0], self.client_address[1])
            sock.close()


class ClientHandler(object):
    """Retransmit the connection data from the client to agent and viceversa
    """

    def __init__(self, sock, agent_session, polling_interval):
        self._client_sock = sock
        self._agent_session = agent_session
        self._read_size = 4096
        self._continue_loop = True
        self._agent_polling_interval = polling_interval

        self._client_sock.settimeout(1)

    def handle(self):
        try:
            reader = Thread(target=self._read_loop)
            reader.start()

            writer = Thread(target=self._write_loop)
            writer.start()

            reader.join()
            writer.join()
        except Exception as ex:
            raise ex
        finally:
            self._close_agent()

    def _read_loop(self):
        try:
            while self._continue_loop:
                self._try_read()
        except (ConnectionResetError, AgentError):
            self._notify_closed_connection()
        except Exception as ex:
            logger.debug("Exception in read loop: %s", ex)
            raise ex

    def _try_read(self):
        data = self._read_agent()
        if not data:
            sleep(self._agent_polling_interval)
            return

        self._write_client(data)

    def _write_loop(self):
        try:
            while self._continue_loop:
                self._try_write()
        except AgentError:
            self._notify_closed_connection()
        except Exception as ex:
            logger.debug("Exception in write loop: %s", ex)
            raise ex

    def _try_write(self):
        try:
            data = self._read_client()
            if not data:
                self._notify_closed_connection()
                return

            self._write_agent(data)
        except socket.timeout:
            pass

    def _notify_closed_connection(self):
        self._continue_loop = False

    def _read_client(self):
        return self._client_sock.recv(self._read_size)

    def _write_client(self, data):
        self._client_sock.send(data)

    def _read_agent(self):
        return self._agent_session.recv()

    def _write_agent(self, data):
        self._agent_session.send(data)

    def _close_agent(self):
        self._agent_session.disconnect()
