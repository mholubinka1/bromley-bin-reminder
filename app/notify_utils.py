from smtplib import SMTP


class SMTPClient:
    _client: SMTP

    def __init__(self, username: str, password: str, server: str, port: int) -> None:
        self._client = SMTP(server, port)
        self._client.starttls()
        self._login(username, password)

    def _login(self, username: str, password: str) -> None:
        self._client.login(username, password)
