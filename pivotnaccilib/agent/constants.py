
class Status(object):
    """Possible values used in the Header STATUS"""
    OK = "OK"
    FAIL = "FAIL"
    INCORRECT = "INCORRECT"


class Header(object):
    """HTTP Headers used by the agents"""

    # Sent by the agent indicate the status of the operation
    STATUS = "X-STATUS"

    # Sent by the agent when STATUS == FAIL, with an error message
    ERROR = "X-ERROR"

    # Sent by broker to the agent to indicate the operation to perform
    OPERATION = "X-OPERATION"

    # Sent by the broker to indicate the IP address of the target host
    IP = "X-IP"

    # Sent by the broker to indicate the port of the target host
    PORT = "X-PORT"

    # Sent by the agent in CONNECT to indicate the connection ID
    # Sent by the broker in RECV, SEND and DISCONNECT to specify the
    # desired connection.
    ID = "X-ID"

    # SVC => Socket Verification Code
    # Sent by the agent in CONNECT to identify the socket
    # Sent by the broker in RECV, SEND and DISCONNECT to allow the agent
    # know if it is capable of write/read data to the desired socket.
    # In case a broker is not allowed to access the socket, it would
    # return the STATUS INCORRECT.
    # This can happen when a session is shared between machines, however
    # only one of them actually has access to the socket descriptor.
    SVC = "X-SVC"

    # Header checked by the agent to verify the sender
    PASSWORD = "X-PASSWORD"


class Operation(object):
    """Operations performed by the agents"""

    # Used by the php agent to create the previous setup required
    # before connect with the target
    INIT = "INIT"

    # To connect to the target host
    CONNECT = "CONNECT"

    # To close the connection with the target host
    DISCONNECT = "DISCONNECT"

    # To request available data from target
    RECV = "RECV"

    # To send data to the target
    SEND = "SEND"
