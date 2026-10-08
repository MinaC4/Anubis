from urllib.parse import urlparse


def is_safe_http_url(value):
    if not isinstance(value, str) or not value or "\\" in value or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return False
    try:
        parsed = urlparse(value)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False
