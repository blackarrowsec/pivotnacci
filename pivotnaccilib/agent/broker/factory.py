from .aspx import AgentAspx
from .php import AgentPhp
from .jsp import AgentJsp
from .interface import AgentBrokerInterface
from ..error import AgentError
from ..structs import AgentOptions


class AgentFactory(object):
    """To create the different classes of agents
    """
    TYPES = ["php", "jsp", "aspx"]

    @classmethod
    def create(
            cls,
            agent_type: str,
            agent_options: AgentOptions
    ) -> AgentBrokerInterface:

        if agent_type == "php":
            return AgentPhp(agent_options)
        elif agent_type == "jsp":
            return AgentJsp(agent_options)
        elif agent_type == "aspx":
            return AgentAspx(agent_options)

        raise AgentError("Unknown agent type {}".format(agent_type))
