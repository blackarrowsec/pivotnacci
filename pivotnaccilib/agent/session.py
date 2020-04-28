from .broker.interface import AgentBrokerInterface
from .structs import AgentSession, ConnectionSession


class AgentConnectionHandler(object):
    """Keep the information of a connection session of an agent with
    a target host.
    """

    def __init__(
            self,
            agent_broker: AgentBrokerInterface,
            agent_session: AgentSession,
            connection: ConnectionSession
    ):
        self.agent_broker = agent_broker
        self.agent_session = agent_session
        self.connection = connection

    def recv(self) -> bytes:
        return self.agent_broker.recv(
            self.agent_session,
            self.connection
        )

    def send(self, data: bytes):
        self.agent_broker.send(
            self.agent_session,
            self.connection,
            data
        )

    def disconnect(self):
        self.agent_broker.disconnect(
            self.agent_session,
            self.connection
        )


class AgentConnectionDispatcher(object):
    """Creates connections with a target host based on a agent
    broker and a agent session.
    """

    def __init__(
            self,
            agent_broker: AgentBrokerInterface,
            agent_session: AgentSession
    ):
        self.agent_broker = agent_broker
        self.agent_session = agent_session

    def connect(self, ip: str, port: int) -> AgentConnectionHandler:
        """Connects with an agent an creates a new session."""
        connection = self.agent_broker.connect(
            self.agent_session,
            ip,
            port
        )
        return AgentConnectionHandler(
            self.agent_broker,
            self.agent_session,
            connection
        )
