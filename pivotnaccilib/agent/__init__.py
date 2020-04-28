"""This module includes all classes required to communicate with the agents.
Includes the brokers, which speak the agent language and those relative to
maintain a session to be used with the agents.
"""

from .error import AgentError
from .broker import AgentJsp, AgentPhp, AgentAspx, \
    AgentFactory
from .session import AgentConnectionDispatcher
from .structs import AgentOptions


