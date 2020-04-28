from abc import ABC, abstractmethod
from ..structs import AgentSession, ConnectionSession


class AgentBrokerInterface(ABC):

    def get_session(self) -> AgentSession:
        raise NotImplementedError()

    @abstractmethod
    def connect(
            self,
            agent_session: AgentSession,
            ip: str,
            port: int
    ) -> ConnectionSession:
        raise NotImplementedError()

    @abstractmethod
    def recv(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession
    ) -> bytes:
        raise NotImplementedError()

    @abstractmethod
    def send(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession,
            data: bytes
    ):
        raise NotImplementedError()

    @abstractmethod
    def disconnect(
            self,
            agent_session: AgentSession,
            connection: ConnectionSession
    ):
        raise NotImplementedError()
