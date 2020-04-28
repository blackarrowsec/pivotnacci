import requests
from ..error import AgentError
from ..constants import Header, Operation, Status
from time import sleep

from ..structs import AgentSession, ConnectionSession, AgentOptions
from .interface import AgentBrokerInterface

import urllib3
# disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ACK_MESSAGE = "Server Error 500 (Internal Error)"


class AgentResponse(object):
    """Internal class to represent the relevant information returned by an
    agent.
    """

    def __init__(self, data, headers):
        self.data = data
        self.headers = headers


class IncorrectAgentError(Exception):
    """Raised when a client returns an INCORRECT status
    """


class NoAgentResponseError(Exception):
    """Raised when the received response was not created by an agent
    """


class AgentBaseBroker(AgentBrokerInterface):
    """
    Class to interact directly with the agent, transforms the
    parameters/answers of agent in python items.
    """

    def __init__(self, options: AgentOptions):
        self.options = options

    def get_session(self) -> AgentSession:
        max_tries = self.options.request_tries
        tries = 0
        while True:
            tries += 1
            try:
                resp = self._request()
                if resp.text.strip() == self.options.ack_message:
                    return AgentSession(resp.cookies)

                if tries >= max_tries:
                    raise AgentError("Not agent found")
            except requests.RequestException as ex:
                if tries >= max_tries:
                    raise AgentError("Error in request: {}".format(ex))

            sleep(self.options.retry_interval)

    def connect(
            self,
            agent_session: AgentSession,
            ip: str,
            port: int
    ) -> ConnectionSession:
        """Request agent to connect to a target host
        """

        headers = {
            Header.OPERATION: Operation.CONNECT,
            Header.IP: str(ip),
            Header.PORT: str(port),
            Header.PASSWORD: self.options.password,
        }
        cookies = agent_session.cookies
        resp = self._try_send_receive(headers, cookies)

        return ConnectionSession(
            resp.headers.get(Header.ID, ""),
            resp.headers.get(Header.SVC, ""),
            ip,
            port
        )

    def disconnect(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession,
    ):
        """Request agent to close a connection
        """
        headers = {
            Header.OPERATION: Operation.DISCONNECT,
            Header.ID: connection.id,
            Header.SVC: connection.socket_verification_code,
            Header.PASSWORD: self.options.password,
        }
        self._try_send_receive(headers, agent_session.cookies)

    def recv(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession
    ) -> bytes:
        """Ask agent if there is new data from the target host
        """
        headers = {
            Header.OPERATION: Operation.RECV,
            Header.ID: connection.id,
            Header.SVC: connection.socket_verification_code,
            Header.PASSWORD: self.options.password,
        }

        resp = self._try_send_receive(headers, agent_session.cookies)
        return resp.data

    def send(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession,
            data: bytes
    ):
        """Send data to agent to retransmit it to the target server
        """
        headers = {
            Header.OPERATION: Operation.SEND,
            Header.ID: connection.id,
            Header.SVC: connection.socket_verification_code,
            Header.PASSWORD: self.options.password,
        }

        self._try_send_receive(
            headers,
            agent_session.cookies,
            data,
            method="POST"
        )

    def _try_send_receive(
            self,
            headers,
            cookies,
            data=None,
            max_tries=0,
            read_timeout=20,
            method="GET"
    ):

        try:
            return self._repeat_send_receive(
                method,
                headers,
                cookies,
                data,
                max_tries,
                read_timeout
            )
        except requests.RequestException as ex:
            raise AgentError("Error in request: {}".format(ex))
        except (IncorrectAgentError, NoAgentResponseError):
            raise AgentError("Unable to find the correct agent")

    def _repeat_send_receive(
            self,
            method,
            headers,
            cookies,
            data,
            max_tries,
            read_timeout
    ):
        """
        Repeat until the correct host is reach in case of
        a balanced server
        """

        if max_tries == 0:
            max_tries = self.options.request_tries

        tries = 0

        while True:
            try:
                return self._send_receive(
                    method,
                    headers,
                    cookies,
                    data,
                    read_timeout
                )
            except (
                    requests.RequestException,
                    IncorrectAgentError,
                    NoAgentResponseError
            ) as ex:
                if tries < max_tries:
                    tries += 1
                else:
                    raise ex

            sleep(self.options.retry_interval)

    def _send_receive(self, method, headers, cookies,  data, read_timeout):
        resp = self._request(
            method,
            headers,
            cookies,
            data,
            read_timeout=read_timeout
        )
        status = resp.headers.get(Header.STATUS, "")

        if status == Status.OK:
            return AgentResponse(resp.content, resp.headers)

        if status == Status.FAIL:
            error_msg = resp.headers.get(Header.ERROR, "Unknown")
            raise AgentError(
                "Error in agent: [HTTP status = {}]  {}".format(
                    resp.status_code,
                    error_msg
                ), fail_msg=error_msg)

        elif status == Status.INCORRECT:
            raise IncorrectAgentError()

        raise NoAgentResponseError()

    def _request(
            self,
            method="GET",
            headers={},
            cookies=None,
            data=None,
            connect_timeout=5,
            read_timeout=20,
    ):
        headers.update(self.options.headers)
        return requests.request(
            method,
            self.options.url,
            headers=headers,
            cookies=cookies,
            data=data,
            timeout=(connect_timeout, read_timeout),
            verify=False,
            proxies=self.options.proxies
        )
