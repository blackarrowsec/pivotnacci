
class AgentSession(object):

    def __init__(self, cookies):
        self.cookies = cookies

    def __str__(self):
        cookies_dict = {}
        for cookie in self.cookies:
            cookies_dict[cookie.name] = cookie.value

        return str(cookies_dict)


class ConnectionSession(object):

    def __init__(
            self,
            connection_id: str,
            socket_verification_code: str,
            ip: str,
            port: int
    ):
        self.id = connection_id
        self.socket_verification_code = socket_verification_code
        self.ip = ip
        self.port = port


class AgentOptions(object):

    def __init__(
            self,
            url: str,
            ack_message: str,
            headers: dict = {},
            proxies: dict = {},
            request_tries: int = 10,
            retry_interval: float = 0.1,
            password: str = "",
    ):
        self.url = url
        self.ack_message = ack_message
        self.headers = headers
        self.proxies = proxies
        self.request_tries = request_tries
        self.retry_interval = retry_interval
        self.password = password
