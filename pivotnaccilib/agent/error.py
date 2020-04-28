
class AgentError(Exception):
    """Raised when there is a problem related to the agent or the
    communication.
    """

    def __init__(self, msg, fail_msg=""):
        super(AgentError, self).__init__(msg)
        self.fail_msg = fail_msg
