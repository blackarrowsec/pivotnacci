
from .base import AgentBaseBroker
from ..constants import Header, Operation
from ..structs import ConnectionSession, AgentSession


class AgentPhp(AgentBaseBroker):
    """
    Class to interact directly with the php agent
    """

    def connect(
            self,
            agent_session: AgentSession,
            ip: str,
            port: int
    ) -> ConnectionSession:
        connection = self._init(agent_session, ip, port)
        self._connect(agent_session, connection)
        return connection

    def _init(
            self,
            agent_session: AgentSession,
            ip: str,
            port: int
    ) -> ConnectionSession:
        headers = {
            Header.OPERATION: Operation.INIT,
            Header.PASSWORD: self.options.password,
            Header.IP: str(ip),
            Header.PORT: str(port),
        }
        cookies = agent_session.cookies

        resp = self._try_send_receive(headers, cookies)
        return ConnectionSession(
            resp.headers.get(Header.ID, ""),
            resp.headers.get(Header.SVC, ""),
            ip,
            port
        )

    def _connect(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession
    ):
        headers = {
            Header.OPERATION: Operation.CONNECT,
            Header.PASSWORD: self.options.password,
            Header.ID: connection.id,
            Header.SVC: connection.socket_verification_code,
        }
        max_tries = self.options.request_tries + 1
        self._try_send_receive(
            headers,
            agent_session.cookies,
            max_tries=max_tries,
            read_timeout=2
        )
